from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional
import asyncio
import random

from pyrogram.errors import SessionPasswordNeeded
from pyrogram.types import Chat, SentCode

from config import API_HASH, API_ID
from db.models import (
    AccountGroupTBL,
    AccountsTBL,
    GroupsTBL,
    TelegramOperationTBL,
    UsersTBL,
)
from telegram_client import TelegramClient
from utils.manage_files import delete_session_file, generate_session_path


@dataclass
class AccountInfo:
    account_id: int
    display_name: str
    phone_number: str
    is_authorized: bool
    is_active: bool
    status: str


@dataclass
class ForwardResult:
    account_id: int
    target_id: int | str
    success: bool
    result: Any = None
    error: Optional[str] = None


class AccountManager:
    def __init__(self, operator_id: int, actor_id: Optional[int] = None):
        operator = UsersTBL.get_user(operator_id)

        if not operator:
            raise ValueError(f"Operator/user {operator_id} not found")

        if not operator.is_active and not operator.is_sudo:
            raise ValueError(f"Operator/user {operator_id} is inactive")

        self.operator_id = operator_id
        self.actor_id = actor_id or operator_id
        self.operator = operator

        self.accounts: dict[int, AccountsTBL] = {}
        self.clients: dict[int, TelegramClient] = {}
        self.pending_clients: dict[str, TelegramClient] = {}
        self.pending_codes: dict[str, SentCode] = {}

        self.refresh_accounts()

    def refresh_accounts(self) -> dict[int, AccountsTBL]:
        """Reload operator accounts and rebuild their Telegram client objects.

        Clients are intentionally created in a disconnected state.  This makes
        the runtime state survive bot restarts without opening a Telegram
        connection for every account automatically.
        """
        db_accounts = list(AccountsTBL.get_admin_accounts(self.operator_id))

        self.accounts = {
            account.account_id: account
            for account in db_accounts
        }

        # Drop runtime clients for accounts that were deleted from the DB.
        valid_ids = set(self.accounts)
        self.clients = {
            account_id: client
            for account_id, client in self.clients.items()
            if account_id in valid_ids
        }

        # Recreate a disconnected TelegramClient object for every authorized
        # account that has a saved session.  No network connection is opened.
        for account in db_accounts:
            if (
                account.is_authorized
                and account.session_path
                and account.account_id not in self.clients
            ):
                self.clients[account.account_id] = self._build_client(account)

        return self.accounts

    @staticmethod
    def _build_client(account: AccountsTBL) -> TelegramClient:
        return TelegramClient(
            name=account.session_path,
            api_id=API_ID,
            api_hash=API_HASH,
            phone_number=account.phone_number,
        )

    def get_account(self, account_id: int) -> AccountsTBL:
        account = self.accounts.get(account_id)

        if account is None:
            account = AccountsTBL.get_account(account_id)

            if account and account.admin_id == self.operator_id:
                self.accounts[account_id] = account
            else:
                account = None

        if account is None:
            raise ValueError(
                f"Account {account_id} does not belong to operator {self.operator_id}"
            )

        return account

    def get_accounts(self) -> list[AccountsTBL]:
        return list(self.accounts.values())

    def get_account_info(self, account_id: int) -> AccountInfo:
        account = self.get_account(account_id)

        return AccountInfo(
            account_id=account.account_id,
            display_name=account.display_name,
            phone_number=account.phone_number,
            is_authorized=account.is_authorized,
            is_active=account.is_active,
            status=account.status,
        )

    def active_accounts(self) -> list[int]:
        return [
            account_id
            for account_id, client in self.clients.items()
            if client.is_connected
        ]

    def active_clients(self) -> dict[int, TelegramClient]:
        return self.clients.copy()

    def is_connected(self, account_id: int) -> bool:
        client = self.clients.get(account_id)
        return bool(client and client.is_connected)

    async def start_login(
        self,
        phone_number: str,
        display_name: Optional[str] = None,
    ) -> SentCode:
        account = AccountsTBL.get_by_phone(phone_number)

        if account and account.admin_id != self.operator_id:
            raise ValueError(
                "This Telegram account belongs to another operator"
            )

        if account and account.is_authorized:
            raise ValueError(
                f"Account {phone_number} is already authorized"
            )

        if phone_number in self.pending_clients:
            return self.pending_codes[phone_number]

        session_path = generate_session_path(phone_number)

        if not account:
            account = AccountsTBL.insert_account(
                admin=self.operator,
                display_name=display_name or phone_number,
                phone_number=phone_number,
                session_path=str(session_path),
            )
            self.accounts[account.account_id] = account
        else:
            if display_name:
                AccountsTBL.update_account(
                    account.account_id,
                    display_name=display_name,
                )

            if not account.session_path:
                AccountsTBL.update_account(
                    account.account_id,
                    session_path=str(session_path),
                )

            self.accounts[account.account_id] = account

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
                AccountsTBL.update_login(
                    account.account_id,
                    me,
                    str(session_path),
                )
                self.accounts[account.account_id] = account
                await client.disconnect_client()
                raise ValueError(
                    f"Account {phone_number} is already authorized"
                )

            sent_code = await client.send_code(phone_number)

            self.pending_clients[phone_number] = client
            self.pending_codes[phone_number] = sent_code
            AccountsTBL.set_status(account.account_id, "waiting_code")

            self._log(
                account,
                "login.send_code",
                result="code_sent",
            )

            return sent_code

        except Exception as exc:
            AccountsTBL.set_status(account.account_id, "failed")
            self._log(
                account,
                "login.send_code",
                status="failed",
                error=str(exc),
            )

            if phone_number not in self.pending_clients:
                await client.disconnect_client()

            raise

    async def verify_login(
        self,
        phone_number: str,
        phone_code: str,
        password: Optional[str] = None,
    ) -> AccountsTBL:
        client = self.pending_clients.get(phone_number)
        code = self.pending_codes.get(phone_number)
        account = AccountsTBL.get_by_phone(phone_number)

        if not client or not code:
            raise ValueError(f"No pending login for {phone_number}")

        if not account or account.admin_id != self.operator_id:
            raise ValueError(
                "This Telegram account does not belong to this operator"
            )

        try:
            try:
                await client.sign_in(
                    phone_number=phone_number,
                    phone_code_hash=code.phone_code_hash,
                    phone_code=phone_code,
                )
            except SessionPasswordNeeded:
                if not password:
                    raise ValueError(
                        "Two-step verification password is required"
                    )

                await client.check_password(password)

            me = await client.load_me()

            AccountsTBL.update_login(
                account.account_id,
                me,
                account.session_path,
            )

            self.accounts[account.account_id] = account
            self.clients[account.account_id] = client
            self._clear_pending(phone_number)

            self._log(
                account,
                "login.verify",
                result=f"telegram_user_id={me.id}",
            )

            return account

        except Exception as exc:
            AccountsTBL.set_status(account.account_id, "failed")
            self._log(
                account,
                "login.verify",
                status="failed",
                error=str(exc),
            )
            raise

    async def connect_account(self, account_id: int) -> TelegramClient:
        account = self.get_account(account_id)
        existing = self.clients.get(account_id)

        if existing and existing.is_connected:
            return existing

        if not account.is_authorized:
            raise ValueError(f"Account {account_id} is not authorized")

        if not account.is_active:
            raise ValueError(f"Account {account_id} is disabled")

        if not account.session_path:
            raise ValueError(f"Account {account_id} has no session path")

        client = existing or self._build_client(account)

        try:
            authorized = await client.login()

            if not authorized:
                AccountsTBL.set_status(account_id, "unauthorized")
                raise ValueError(
                    f"Account {account_id} session is not authorized"
                )

            await client.load_me()
            self.clients[account_id] = client
            AccountsTBL.mark_connected(account_id)

            self._log(
                account,
                "account.connect",
                result="connected",
            )

            return client

        except Exception as exc:
            self._log(
                account,
                "account.connect",
                status="failed",
                error=str(exc),
            )
            await client.disconnect_client()
            raise

    async def disconnect_account(self, account_id: int) -> bool:
        account = self.get_account(account_id)
        client = self.clients.get(account_id)

        if not client:
            AccountsTBL.mark_disconnected(account_id)
            return False

        try:
            await client.disconnect_client()
            AccountsTBL.mark_disconnected(account_id)

            self._log(
                account,
                "account.disconnect",
                result="disconnected",
            )

            return True

        except Exception as exc:
            self._log(
                account,
                "account.disconnect",
                status="failed",
                error=str(exc),
            )
            raise

    async def set_account_active(
        self,
        account_id: int,
        active: bool,
    ) -> AccountsTBL:
        account = self.get_account(account_id)

        if active:
            account = AccountsTBL.activate(account_id)
        else:
            await self.disconnect_account(account_id)
            account = AccountsTBL.deactivate(account_id)

        if account is None:
            raise ValueError(f"Account {account_id} not found")

        self.accounts[account_id] = account
        return account

    async def delete_account(
        self,
        account_id: int,
        delete_session: bool = True,
    ) -> bool:
        account = self.get_account(account_id)
        session_path = account.session_path

        await self.disconnect_account(account_id)
        self.accounts.pop(account_id, None)
        self.clients.pop(account_id, None)
        AccountsTBL.delete_account(account_id)

        if delete_session and session_path:
            delete_session_file(path=session_path + ".session")

        return True


    async def disable_account(self, account_id: int) -> AccountsTBL:
        return await self.set_account_active(account_id, False)

    async def activate_account(self, account_id: int) -> AccountsTBL:
        return await self.set_account_active(account_id, True)

    async def forward_to_selected_groups(
        self,
        account_id: int,
        from_chat_id: int | str,
        message_ids: int | list[int],
        group_ids: list[int],
        min_delay: float = 1.0,
        max_delay: float = 3.0,
    ) -> list[ForwardResult]:
        results: list[ForwardResult] = []

        for index, group_id in enumerate(group_ids):
            try:
                result = await self.forward_messages(
                    account_id,
                    group_id,
                    from_chat_id,
                    message_ids,
                )
                results.append(
                    ForwardResult(
                        account_id=account_id,
                        target_id=group_id,
                        success=True,
                        result=result,
                    )
                )
            except Exception as exc:
                results.append(
                    ForwardResult(
                        account_id=account_id,
                        target_id=group_id,
                        success=False,
                        error=str(exc),
                    )
                )

            if index < len(group_ids) - 1:
                await asyncio.sleep(random.uniform(min_delay, max_delay))

        return results

    async def get_client(self, account_id: int) -> TelegramClient:
        self.get_account(account_id)
        client = self.clients.get(account_id)

        if client and client.is_connected:
            return client

        return await self.connect_account(account_id)

    async def get_me(self, account_id: int):
        return await self._run(
            account_id,
            "get_me",
            lambda client: client.get_me_info(),
        )

    async def get_chat(
        self,
        account_id: int,
        chat_id: int | str,
    ):
        return await self._run(
            account_id,
            "get_chat",
            lambda client: client.get_chat(chat_id),
            target_id=chat_id if isinstance(chat_id, int) else None,
            target_type="chat",
        )

    async def get_dialogs(
        self,
        account_id: int,
        limit: Optional[int] = None,
    ) -> list[Chat]:
        return await self._run(
            account_id,
            "get_dialogs",
            lambda client: client.get_dialogs(limit),
            target_type="groups",
        )

    async def get_groups(
        self,
        account_id: int,
        limit: Optional[int] = None,
    ) -> list[Chat]:
        return await self._run(
            account_id,
            "get_groups",
            lambda client: client.get_groups(limit),
            target_type="groups",
        )

    async def sync_account_groups(
        self,
        account_id: int,
    ) -> list[AccountGroupTBL]:
        """Fetch the account's current Telegram groups live and mirror them
        into the local DB (GroupsTBL/AccountGroupTBL).

        Groups that are no longer among the account's dialogs are marked as
        left, so the saved list stays a faithful copy of what the account is
        actually a member of.
        """
        account = self.get_account(account_id)
        chats = await self.get_groups(account_id)

        current_ids: set[int] = set()

        for chat in chats:
            current_ids.add(chat.id)
            group = GroupsTBL.insert_group(
                group_id=chat.id,
                group_title=getattr(chat, "title", str(chat.id)),
                group_username=getattr(chat, "username", None),
                group_type=str(getattr(chat, "type", "group")),
            )
            AccountGroupTBL.insert_group(account, group)

        for relation in AccountGroupTBL.get_account_groups(account_id, joined_only=True):
            if relation.group_id not in current_ids:
                AccountGroupTBL.mark_left(account_id, relation.group_id)

        return list(
            AccountGroupTBL.get_account_groups(account_id, joined_only=True)
        )

    async def join_group(
        self,
        account_id: int,
        chat_or_link: int | str,
    ) -> Chat:
        result = await self._run(
            account_id,
            "join_group",
            lambda client: client.join_group(chat_or_link),
            target_type="group",
        )

        account = self.get_account(account_id)

        if hasattr(result, "id"):
            group = GroupsTBL.insert_group(
                group_id=result.id,
                group_title=getattr(result, "title", str(result.id)),
                group_username=getattr(result, "username", None),
                group_type=str(getattr(result, "type", "group")),
            )
            AccountGroupTBL.insert_group(account, group)

        return result

    async def join_group_for_accounts(
        self,
        account_ids: list[int],
        chat_or_link: int | str,
    ) -> list[ForwardResult]:
        results: list[ForwardResult] = []

        for account_id in account_ids:
            try:
                result = await self.join_group(account_id, chat_or_link)
                results.append(
                    ForwardResult(
                        account_id=account_id,
                        target_id=chat_or_link,
                        success=True,
                        result=result,
                    )
                )
            except Exception as exc:
                results.append(
                    ForwardResult(
                        account_id=account_id,
                        target_id=chat_or_link,
                        success=False,
                        error=str(exc),
                    )
                )

        return results

    async def leave_group(
        self,
        account_id: int,
        chat_id: int | str,
    ):
        result = await self._run(
            account_id,
            "leave_group",
            lambda client: client.leave_group(chat_id),
            target_id=chat_id if isinstance(chat_id, int) else None,
            target_type="group",
        )

        if isinstance(chat_id, int):
            AccountGroupTBL.mark_left(account_id, chat_id)

        return result

    async def send_message(
        self,
        account_id: int,
        chat_id: int | str,
        text: str,
        **kwargs: Any,
    ):
        return await self._run(
            account_id,
            "send_message",
            lambda client: client.send_message(
                chat_id,
                text,
                **kwargs,
            ),
            target_id=chat_id if isinstance(chat_id, int) else None,
            target_type="chat",
        )

    async def forward_message(
        self,
        account_id: int,
        chat_id: int | str,
        from_chat_id: int | str,
        message_id: int,
    ):
        return await self._run(
            account_id,
            "forward_message",
            lambda client: client.forward_messages(
                chat_id=chat_id,
                from_chat_id=from_chat_id,
                message_ids=message_id,
            ),
            target_id=chat_id if isinstance(chat_id, int) else None,
            target_type="chat",
        )

    async def forward_messages(
        self,
        account_id: int,
        chat_id: int | str,
        from_chat_id: int | str,
        message_ids: int | list[int],
    ):
        return await self._run(
            account_id,
            "forward_messages",
            lambda client: client.forward_messages(
                chat_id=chat_id,
                from_chat_id=from_chat_id,
                message_ids=message_ids,
            ),
            target_id=chat_id if isinstance(chat_id, int) else None,
            target_type="chat",
        )

    async def forward_to_account_groups(
        self,
        account_id: int,
        from_chat_id: int | str,
        message_ids: int | list[int],
    ) -> list[ForwardResult]:
        groups = AccountGroupTBL.get_account_groups(
            account_id,
            joined_only=True,
        )
        results: list[ForwardResult] = []

        for relation in groups:
            try:
                result = await self.forward_messages(
                    account_id,
                    relation.group_id,
                    from_chat_id,
                    message_ids,
                )
                results.append(
                    ForwardResult(
                        account_id=account_id,
                        target_id=relation.group_id,
                        success=True,
                        result=result,
                    )
                )
            except Exception as exc:
                results.append(
                    ForwardResult(
                        account_id=account_id,
                        target_id=relation.group_id,
                        success=False,
                        error=str(exc),
                    )
                )

        return results

    async def forward_to_accounts_groups(
        self,
        account_ids: list[int],
        from_chat_id: int | str,
        message_ids: int | list[int],
    ) -> list[ForwardResult]:
        results: list[ForwardResult] = []

        for account_id in account_ids:
            results.extend(
                await self.forward_to_account_groups(
                    account_id,
                    from_chat_id,
                    message_ids,
                )
            )

        return results

    async def get_messages(
        self,
        account_id: int,
        chat_id: int | str,
        message_ids: int | list[int],
    ):
        return await self._run(
            account_id,
            "get_messages",
            lambda client: client.get_messages(
                chat_id,
                message_ids,
            ),
            target_id=chat_id if isinstance(chat_id, int) else None,
            target_type="chat",
        )

    async def _run(
        self,
        account_id: int,
        operation: str,
        action: Callable[
            [TelegramClient],
            Awaitable[Any],
        ],
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
    ):
        account = self.get_account(account_id)
        client = await self.get_client(account_id)

        try:
            result = await action(client)
            self._log(
                account,
                operation,
                result=self._result_text(result),
                target_type=target_type,
                target_id=target_id,
            )
            AccountsTBL.touch(account_id)
            return result

        except Exception as exc:
            self._log(
                account,
                operation,
                status="failed",
                error=str(exc),
                target_type=target_type,
                target_id=target_id,
            )
            raise

    def _log(
        self,
        account: AccountsTBL,
        operation: str,
        status: str = "success",
        result: Optional[str] = None,
        error: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
    ) -> TelegramOperationTBL:
        actor = UsersTBL.get_user(self.actor_id)

        return TelegramOperationTBL.insert_operation(
            account=account,
            actor=actor,
            operation=operation,
            status=status,
            target_type=target_type,
            target_id=target_id,
            result=result,
            error=error,
        )

    @staticmethod
    def _result_text(result: Any) -> str:
        if result is None:
            return "ok"

        if isinstance(result, (str, int, float, bool)):
            return str(result)

        result_id = getattr(result, "id", None)

        if result_id is not None:
            return f"id={result_id}"

        if isinstance(result, list):
            return f"count={len(result)}"

        return result.__class__.__name__

    def _clear_pending(self, phone_number: str) -> None:
        self.pending_clients.pop(phone_number, None)
        self.pending_codes.pop(phone_number, None)
