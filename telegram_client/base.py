from typing import Any, Optional
from pyrogram import Client
from utils.logger import get_logger


logger = get_logger(__name__)


class TelegramClient(Client):

    def __init__(self, name: str, api_id: int, api_hash: str, phone_number: Optional[str] = None, ):
        super().__init__(name=name, api_id=api_id, api_hash=api_hash, phone_number=phone_number, )
        self.me = None

    async def login(self, phone_number: Optional[str] = None):
        phone = phone_number or self.phone_number
        if not phone:
            raise ValueError("phone_number is required")
        authorized = await self.connect()
        if authorized:
            await self.load_me()
        return authorized

    async def load_me(self):
        self.me = await self.get_me()
        return self.me

    async def get_me_info(self):
        return await self.load_me()

    async def get_chat(self, chat_id: int | str):
        return await super().get_chat(chat_id)

    async def get_dialogs(self, limit: Optional[int] = None) -> list[Any]:
        dialogs = []
        async for dialog in super().get_dialogs():
            dialogs.append(dialog)
            if limit is not None and len(dialogs) >= limit:
                break
        return dialogs

    async def get_groups(self, limit: Optional[int] = None) -> list[Any]:
        groups = []
        async for dialog in super().get_dialogs():
            chat = dialog.chat
            if chat.type in ("group", "supergroup"):
                groups.append(chat)
                if limit is not None and len(groups) >= limit:
                    break
        return groups

    async def join_group(self, chat_or_link: int | str):
        return await super().join_chat(chat_or_link)

    async def leave_group(self, chat_id: int | str):
        return await super().leave_chat(chat_id)

    async def send_message_to(self, chat_id: int | str, text: str, **kwargs):
        return await super().send_message(chat_id, text, **kwargs)

    async def forward_message_to(self, chat_id: int | str, from_chat_id: int | str, message_id: int):
        return await super().forward_messages(chat_id, from_chat_id, message_id)

    async def get_messages_from(self, chat_id: int | str, message_ids: int | list[int]):
        return await super().get_messages(chat_id, message_ids)

    async def disconnect_client(self):
        if self.is_connected:
            await self.disconnect()


# Temporary import compatibility for old modules. New code should use TelegramClient.
ForwardBot = TelegramClient
