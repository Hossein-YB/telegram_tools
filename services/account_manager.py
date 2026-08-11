import asyncio
from utils.logger import get_logger
import time
from typing import Optional

from pyrogram.errors import SessionPasswordNeeded
from pyrogram.types import SentCode

from config import API_ID, API_HASH
from forwarder_client.base import ForwardBot
from utils.manage_files import generate_session_path

logger = get_logger(__name__)


class AccountManager:

    def __init__(self, idle_timeout: int = 300, check_interval: int = 30, ):
        self.clients: dict[str, ForwardBot] = {}
        self.last_usage: dict[str, float] = {}

        self.pending_auth: dict[str, ForwardBot] = {}
        self.pending_codes: dict[str, SentCode] = {}

        self.idle_timeout = idle_timeout
        self.check_interval = check_interval

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
        for phone_number in list(self.clients):
            await self.disconnect(phone_number)

        for phone_number in list(self.pending_auth):
            await self._cleanup_pending(phone_number)

        logger.info("AccountManager stopped")

    async def create_instance_forwarder(self, phone_number: str, ) -> bool:
        if phone_number in self.clients:
            self.touch(phone_number)
            return True

        if phone_number in self.pending_auth:
            return False

        session_path = generate_session_path(phone_number)

        client = ForwardBot(name=session_path, api_id=API_ID, api_hash=API_HASH, phone_number=phone_number, )

        try:
            is_authorized = await client.connect()

            if is_authorized:
                await client.initialize_after_login()

                self.clients[phone_number] = client
                self.touch(phone_number)

                logger.info("Account already authorized: %s", phone_number, )

                return True

            self.pending_auth[phone_number] = client

            logger.info("Account requires authorization: %s", phone_number, )

            return False

        except Exception:
            logger.exception("Failed to create account client: %s", phone_number, )

            try:
                await client.disconnect()
            except Exception:
                pass

            raise

    async def send_code(self, phone_number: str, ) -> SentCode:
        client = self.pending_auth.get(phone_number)

        if not client:
            raise ValueError(f"Account {phone_number} is not waiting for authorization")

        try:
            sent_code = await client.send_code(phone_number)

            self.pending_codes[phone_number] = sent_code

            logger.info("Authorization code sent: %s", phone_number, )

            return sent_code

        except Exception:
            logger.exception("Failed to send authorization code: %s", phone_number, )
            raise

    async def verify_code(self, phone_number: str, phone_code: str, password: Optional[str] = None, ) -> ForwardBot:
        client = self.pending_auth.get(phone_number)

        if not client:
            raise ValueError(f"Account {phone_number} is not waiting for authorization")

        sent_code = self.pending_codes.get(phone_number)

        if not sent_code:
            raise ValueError(f"No authorization code exists for {phone_number}")

        try:
            try:
                await client.sign_in(phone_number=phone_number, phone_code_hash=sent_code.phone_code_hash,
                                     phone_code=phone_code, )

            except SessionPasswordNeeded:
                if not password:
                    raise ValueError("Two-step verification password is required")

                await client.check_password(password)

            await client.initialize_after_login()
            self.clients[phone_number] = client
            self.pending_auth.pop(phone_number, None, )
            self.pending_codes.pop(phone_number, None,)
            self.touch(phone_number)
            logger.info("Account authorized successfully: %s", phone_number, )

            return client

        except Exception:
            logger.exception("Failed to authorize account: %s", phone_number, )
            raise

    async def new_client(self, phone_number: str, ) -> SentCode:

        is_authorized = await self.create_instance_forwarder(phone_number)
        if is_authorized:
            raise ValueError(f"Account {phone_number} is already authorized")
        return await self.send_code(phone_number)

    async def connect(self, phone_number: str, ) -> ForwardBot:
        client = self.clients.get(phone_number)

        if client:
            self.touch(phone_number)
            return client

        if phone_number in self.pending_auth:
            raise ValueError(f"Account {phone_number} is waiting for authorization")

        session_path = generate_session_path(phone_number)

        client = ForwardBot(name=session_path, api_id=API_ID, api_hash=API_HASH, phone_number=phone_number, )

        try:
            is_authorized = await client.connect()

            if not is_authorized:
                await client.disconnect()

                raise ValueError(f"Account {phone_number} is not authorized")

            await client.initialize_after_login()

            self.clients[phone_number] = client
            self.touch(phone_number)

            logger.info("Account connected: %s", phone_number, )

            return client

        except Exception:
            try:
                await client.disconnect()
            except Exception:
                pass

            raise

    async def disconnect(self, phone_number: str, ) -> bool:
        client = self.clients.pop(phone_number, None, )

        if not client:
            return False

        try:
            await client.shutdown()
        except Exception:
            logger.exception("Failed to disconnect account: %s", phone_number, )
        finally:
            self.last_usage.pop(phone_number, None, )

        logger.info("Account disconnected: %s", phone_number, )

        return True

    async def get(self, phone_number: str, ) -> ForwardBot:
        client = self.clients.get(phone_number)

        if not client:
            client = await self.connect(phone_number)

        self.touch(phone_number)

        return client

    def is_connected(self, phone_number: str, ) -> bool:
        return phone_number in self.clients

    def touch(self, phone_number: str, ):
        self.last_usage[phone_number] = time.monotonic()

    def active_accounts(self) -> list[str]:
        return list(self.clients.keys())

    async def _idle_monitor(self):
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)

                now = time.monotonic()

                for phone_number, last_used in list(self.last_usage.items()):
                    if now - last_used >= self.idle_timeout:
                        logger.info("Disconnecting idle account: %s", phone_number, )

                        await self.disconnect(phone_number)

            except asyncio.CancelledError:
                break

            except Exception:
                logger.exception("Account idle monitor failed")

    async def _cleanup_pending(self, phone_number: str, ):
        client = self.pending_auth.pop(
            phone_number,
            None,
        )

        self.pending_codes.pop(phone_number, None, )
        if client:
            try:
                await client.disconnect()
            except Exception:
                pass

#
# async def main():
#     manager = AccountManager(idle_timeout=300, check_interval=30,)
#     await manager.start()
#
#     phone = input("Phone number: ").strip()
#
#     try:
#         sent_code = await manager.new_client(phone)
#
#         code = input("Code: ").strip()
#
#         password = input(
#             "2FA Password (leave empty if none): "
#         ).strip()
#
#         client = await manager.verify_code(
#             phone_number=phone,
#             phone_code=code,
#             password=password or None,
#         )
#
#         print()
#         print("Login successful")
#         print(f"User ID: {client.me.id}")
#         print(f"Name: {client.me.first_name}")
#         print(f"Username: @{client.me.username}")
#
#         print()
#         print(
#             "Active accounts:",
#             manager.active_accounts(),
#         )
#
#         await asyncio.sleep(10)
#
#     finally:
#         await manager.stop()
#
#
# if __name__ == "__main__":
#     asyncio.run(main())
