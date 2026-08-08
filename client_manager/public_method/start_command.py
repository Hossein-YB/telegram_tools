from typing import TYPE_CHECKING
from utils.user_permissions import admin_required

from pyrogram.types import Message

if TYPE_CHECKING:
    from client_manager.base import ClientManger


class StartCommand:
    async def access_denied(self: "ClientManger", msg: Message):
        return await msg.reply_text(self.texts.CAN_NOT_START_BOT)

    @admin_required
    async def start_command(self: "ClientManger", clt, msg: Message):
        return await msg.reply_text(self.texts.START_TEXT)
