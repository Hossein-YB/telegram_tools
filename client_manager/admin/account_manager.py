from typing import TYPE_CHECKING
from utils.user_permissions import sudo_required
from conversation.utils.exceptions import ListenerTimeout
from pyrogram.types import Message

if TYPE_CHECKING:
    from client_manager.base import ClientManger


class AccountManager:
    @sudo_required
    async def add_new_account(self: "ClientManger", clt, msg: Message):
        try:
            await self.ask()
        except ListenerTimeout as e:
            print(e)
