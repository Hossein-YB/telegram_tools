from typing import Optional

from pyrogram import Client
from pyrogram.errors import UserNotParticipant
from pyrogram.types import Chat, User, Dialog, SentCode


class TelegramClient(Client):
    def __init__(
        self,
        name: str,
        api_id: int,
        api_hash: str,
        phone_number: Optional[str] = None,
    ):
        self.me: Optional[User] = None
        super().__init__(
            name=name,
            api_id=api_id,
            api_hash=api_hash,
            phone_number=phone_number,
        )

    async def login(self, phone_number: Optional[str] = None) -> bool:
        phone = phone_number or self.phone_number
        if not phone:
            raise ValueError("phone_number is required")
        authorized = await self.connect()
        if authorized:
            await self.load_me()
        return authorized

    async def send_code(self, phone_number: Optional[str] = None) -> SentCode:
        phone = phone_number or self.phone_number
        if not phone:
            raise ValueError("phone_number is required")
        return await super().send_code(phone)

    async def sign_in(
        self,
        phone_number: str,
        phone_code_hash: str,
        phone_code: str,
    ) -> User:
        return await super().sign_in(
            phone_number=phone_number,
            phone_code_hash=phone_code_hash,
            phone_code=phone_code,
        )

    async def check_password(self, password: str) -> User:
        return await super().check_password(password)

    async def load_me(self) -> User:
        self.me = await self.get_me()
        return self.me

    async def get_me_info(self) -> User:
        return await self.load_me()

    async def get_me_dialogs(self, limit: Optional[int] = None) -> list[Dialog]:
        dialogs: list[Dialog] = []
        async for dialog in super().get_dialogs():
            dialogs.append(dialog)
            if limit is not None and len(dialogs) >= limit:
                break
        return dialogs

    async def get_groups(self, limit: Optional[int] = None) -> list[Chat]:
        groups: list[Chat] = []
        async for dialog in super().get_dialogs():
            chat = dialog.chat
            if chat.type in ("group", "supergroup"):
                groups.append(chat)
                if limit is not None and len(groups) >= limit:
                    break
        return groups

    async def join_group(self, chat_or_link: int | str) -> Chat:
        return await super().join_chat(chat_or_link)

    async def leave_group(self, chat_id: int | str) -> Chat:
        return await super().leave_chat(chat_id)

    async def is_member(self, chat_id: int | str) -> bool:
        if self.me is None:
            await self.load_me()
        try:
            await self.get_chat_member(chat_id, self.me.id)
            return True
        except UserNotParticipant:
            return False

    async def disconnect_client(self) -> None:
        if self.is_connected:
            await self.disconnect()
