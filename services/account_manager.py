import asyncio
import time
from typing import Optional, Callable, Awaitable, Any

from pyrogram.errors import SessionPasswordNeeded
from pyrogram.types import SentCode

from config import API_ID, API_HASH
from db.models import (
    UsersTBL,
    AccountsTBL,
    GroupsTBL,
    AccountGroupTBL,
    TelegramOperationTBL,
)
from telegram_client.base import TelegramClient
from utils.logger import get_logger
from utils.manage_files import generate_session_path, delete_session_file

logger = get_logger(__name__)


class AccountManager:
    """Account lifecycle + DB persistence + operation logging.

    TelegramClient is intentionally kept DB-free. All DB writes stay here/models.
    """

    def __init__(self, idle_timeout: int = 300, check_interval: int = 30):
        self.clients: dict[int, TelegramClient] = {}
        self.pending_clients: dict[str, TelegramClient] = {}
        self.pending_codes: dict[str, SentCode] = {}
        self.idle_timeout = idle_timeout
        self.check_interval = check_interval
        self._last_usage: dict[int, float] = {}
        self._monitor_task: asyncio.Task | None = None
        self._running = False

    async def start(self):
        if self._running:
            return
        self._running = True
        self._monitor_task = asyncio.create_task(self._idle_monitor())
        logger.info("AccountManager started")

    async def stop(self):
        if not self._running:
            return
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        for account_id in list(self.clients):
            await self.disconnect_account(account_id)
        for phone in list(self.pending_clients):
            await self._cleanup_pending(phone)

        logger.info("AccountManager stopped")

    async def start_login(self, admin_id: int, phone_number: str) -> SentCode:
        """Create/reuse the account record, connect and send Telegram login code."""
        admin = UsersTBL.get_user(admin_id)
        if not admin:
            raise ValueError(f"Admin/user {admin_id} not found")

        account = AccountsTBL.get_by_phone(phone_number)
        session_path = generate_session_path(phone_number)
        if account and account.is_authorized:
            raise ValueError(f"Account {phone_number} is already authorized")

        if phone_number in self.pending_clients:
            return self.pending_codes[phone_number]

        if not account:
            account = AccountsTBL.insert_account(admin, phone_number, str(session_path))
        elif not account.session_path:
            account.session_path = str(session_path)
            account.save()

        client = TelegramClient(
            name=str(session_path),
            api_id=API_ID,
            api_hash=API_HASH,
            phone_number=phone_number,
        )

        try:
            authorized = await client.login(phone_number)
            if authorized:
                me = client.me or await client.load_me()
                AccountsTBL.update_login(account.account_id, me, str(session_path))
                await client.disconnect_client()
                raise ValueError(f"Account {phone_number} is already authorized")

            sent_code = await client.send_code(phone_number)
            self.pending_clients[phone_number] = client
            self.pending_codes[phone_number] = sent_code
            AccountsTBL.set_status(account.account_id, "waiting_code")
            self._log(account, "login.send_code", result="code_sent")
            return sent_code
        except Exception as exc:
            self._log(account, "login.send_code", status="failed", error=str(exc))
            if phone_number not in self.pending_clients:
                await client.disconnect_client()
            raise

    async def verify_login(self, phone_number: str, phone_code: str, password: Optional[str] = None) -> AccountsTBL:
        """Finish Telegram login and persist the Telegram profile."""
        client = self.pending_clients.get(phone_number)
        code = self.pending_codes.get(phone_number)
        account = AccountsTBL.get_by_phone(phone_number)

        if not client or not code:
            raise ValueError(f"No pending login for {phone_number}")
        if not account:
            raise ValueError(f"Account {phone_number} not found")

        try:
            try:
                await client.sign_in(
                    phone_number=phone_number,
                    phone_code_hash=code.phone_code_hash,
                    phone_code=phone_code,
                )
            except SessionPasswordNeeded:
                if not password:
                    raise ValueError("Two-step verification password is required")
                await client.check_password(password)

            me = await client.load_me()
            AccountsTBL.update_login(account.account_id, me, account.session_path)
            self.clients[account.account_id] = client
            self._last_usage[account.account_id] = time.monotonic()
            self._clear_pending(phone_number)
            self._log(account, "login.verify", result=f"telegram_user_id={me.id}")
            return account
        except Exception as exc:
            self._log(account, "login.verify", status="failed", error=str(exc))
            raise

    async def connect_account(self, account_id: int) -> TelegramClient:
        """Connect an already-authorized account using its saved session."""
        existing = self.clients.get(account_id)
        if existing and existing.is_connected:
            self._touch(account_id)
            return existing

        account = AccountsTBL.get_account(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        if not account.is_authorized:
            raise ValueError(f"Account {account_id} is not authorized")
        if not account.is_active:
            raise ValueError(f"Account {account_id} is disabled")
        if not account.session_path:
            raise ValueError(f"Account {account_id} has no session path")

        client = TelegramClient(name=account.session_path, api_id=API_ID, api_hash=API_HASH, phone_number=account.phone_number)
        try:
            authorized = await client.login()
            if not authorized:
                AccountsTBL.set_status(account_id, "unauthorized")
                raise ValueError(f"Account {account_id} session is not authorized")

            await client.load_me()
            self.clients[account_id] = client
            self._touch(account_id)
            AccountsTBL.mark_connected(account_id)
            self._log(account, "account.connect", result="connected")
            return client
        except Exception as exc:
            self._log(account, "account.connect", status="failed", error=str(exc))
            await client.disconnect_client()
            raise

    async def disconnect_account(self, account_id: int) -> bool:
        client = self.clients.pop(account_id, None)
        account = AccountsTBL.get_account(account_id)
        if not client:
            if account:
                AccountsTBL.mark_disconnected(account_id)
            return False

        try:
            await client.disconnect_client()
            if account:
                AccountsTBL.mark_disconnected(account_id)
                self._log(account, "account.disconnect", result="disconnected")
            return True
        except Exception as exc:
            if account:
                self._log(account, "account.disconnect", status="failed", error=str(exc))
            raise
        finally:
            self._last_usage.pop(account_id, None)

    async def delete_account(self, account_id: int, delete_session: bool = True) -> bool:
        account = AccountsTBL.get_account(account_id)
        if not account:
            return False

        await self.disconnect_account(account_id)
        session_path = account.session_path
        account.delete_instance(recursive=True)
        if delete_session and session_path:
            delete_session_file(path=session_path + ".session")
        return True

    async def get_client(self, account_id: int) -> TelegramClient:
        client = self.clients.get(account_id)
        if client and client.is_connected:
            self._touch(account_id)
            return client
        return await self.connect_account(account_id)

    def is_connected(self, account_id: int) -> bool:
        client = self.clients.get(account_id)
        return bool(client and client.is_connected)

    def active_accounts(self) -> list[int]:
        return list(self.clients.keys())

    async def get_me(self, account_id: int):
        return await self._run(account_id, "get_me", lambda c: c.get_me_info())

    async def get_chat(self, account_id: int, chat_id: int | str):
        return await self._run(account_id, "get_chat", lambda c: c.get_chat(chat_id), target_id=chat_id, target_type="chat")

    async def get_dialogs(self, account_id: int, limit: int | None = None):
        return await self._run(account_id, "get_dialogs", lambda c: c.get_dialogs(limit), target_type="dialogs")

    async def get_groups(self, account_id: int, limit: int | None = None):
        groups = await self._run(account_id, "get_groups", lambda c: c.get_groups(limit), target_type="groups")
        return groups

    async def join_group(self, account_id: int, chat_or_link: int | str):
        result = await self._run(account_id, "join_group", lambda c: c.join_group(chat_or_link), target_type="group")
        account = AccountsTBL.get_account(account_id)
        if account and hasattr(result, "id"):
            group = GroupsTBL.insert_group(
                group_id=result.id,
                group_title=getattr(result, "title", str(result.id)),
                group_username=getattr(result, "username", None),
                group_type=str(getattr(result, "type", "group")),
            )
            AccountGroupTBL.insert_group(account, group)
        return result

    async def leave_group(self, account_id: int, chat_id: int | str):
        result = await self._run(account_id, "leave_group", lambda c: c.leave_group(chat_id), target_id=chat_id, target_type="group")
        if isinstance(chat_id, int):
            AccountGroupTBL.mark_left(account_id, chat_id)
        return result

    async def send_message(self, account_id: int, chat_id: int | str, text: str, **kwargs):
        return await self._run(
            account_id,
            "send_message",
            lambda c: c.send_message_to(chat_id, text, **kwargs),
            target_id=chat_id if isinstance(chat_id, int) else None,
            target_type="chat",
        )

    async def forward_message(self, account_id: int, chat_id: int | str, from_chat_id: int | str, message_id: int):
        return await self._run(
            account_id,
            "forward_message",
            lambda c: c.forward_message_to(chat_id, from_chat_id, message_id),
            target_id=chat_id if isinstance(chat_id, int) else None,
            target_type="chat",
        )

    async def get_messages(self, account_id: int, chat_id: int | str, message_ids: int | list[int]):
        return await self._run(
            account_id,
            "get_messages",
            lambda c: c.get_messages_from(chat_id, message_ids),
            target_id=chat_id if isinstance(chat_id, int) else None,
            target_type="chat",
        )

    async def _run(
        self,
        account_id: int,
        operation: str,
        action: Callable[[TelegramClient], Awaitable[Any]],
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
    ):
        account = AccountsTBL.get_account(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        client = await self.get_client(account_id)
        try:
            result = await action(client)
            self._touch(account_id)
            TelegramOperationTBL.log(
                account=account,
                operation=operation,
                target_type=target_type,
                target_id=target_id,
                status="success",
                result=self._result_text(result),
            )
            return result
        except Exception as exc:
            TelegramOperationTBL.log(
                account=account,
                operation=operation,
                target_type=target_type,
                target_id=target_id,
                status="failed",
                error=str(exc),
            )
            raise

    def _touch(self, account_id: int):
        self._last_usage[account_id] = time.monotonic()
        AccountsTBL.touch(account_id)

    @staticmethod
    def _result_text(result: Any) -> str:
        if result is None:
            return "ok"
        if isinstance(result, (str, int, float, bool)):
            return str(result)
        data = getattr(result, "id", None)
        if data is not None:
            return f"id={data}"
        if isinstance(result, list):
            return f"count={len(result)}"
        return result.__class__.__name__

    @staticmethod
    def _log(account: AccountsTBL, operation: str, status: str = "success", result: str | None = None, error: str | None = None):
        return TelegramOperationTBL.log(
            account=account,
            operation=operation,
            status=status,
            result=result,
            error=error,
        )

    def _clear_pending(self, phone_number: str):
        self.pending_clients.pop(phone_number, None)
        self.pending_codes.pop(phone_number, None)

    async def _cleanup_pending(self, phone_number: str):
        client = self.pending_clients.pop(phone_number, None)
        self.pending_codes.pop(phone_number, None)
        if client:
            await client.disconnect_client()

    async def _idle_monitor(self):
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)
                now = time.monotonic()
                for account_id, last_used in list(self._last_usage.items()):
                    if now - last_used >= self.idle_timeout:
                        await self.disconnect_account(account_id)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Account idle monitor failed")
