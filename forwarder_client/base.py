
import logging

logger = logging.getLogger(__name__)

import logging

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler

logger = logging.getLogger(__name__)


class ForwardBot(Client):

    def __init__(
        self,
        name: str,
        api_id: int,
        api_hash: str,
        phone_number: str | None = None,
    ):
        super().__init__(
            name=name,
            api_id=api_id,
            api_hash=api_hash,
            phone_number=phone_number,
        )

        self.is_work = False
        self._initialized = False

    async def initialize_after_login(self):
        if not self.is_connected:
            raise RuntimeError(
                "Client must be connected before initialization"
            )

        if self._initialized:
            return self

        try:
            self.me = await self.get_me()
            await self.initialize()

            self.add_handler(
                MessageHandler(
                    self.send_hello,
                    filters.me,
                )
            )

            self.is_work = True
            self._initialized = True

            logger.info(
                "Account initialized: %s (%s)",
                self.me.first_name,
                self.me.id,
            )

            return self

        except Exception:
            logger.exception(
                "Failed to initialize account"
            )
            raise

    async def send_hello(self, client, message):
        await message.reply_text("hi")

    async def shutdown(self):
        self.is_work = False
        self._initialized = False

        if self.is_connected:
            await self.disconnect()
