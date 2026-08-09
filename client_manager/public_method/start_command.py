from typing import TYPE_CHECKING
from utils.user_permissions import admin_required
from db.models import UsersTBL
from pyrogram.types import Message

if TYPE_CHECKING:
    from client_manager.base import ClientManger


class StartCommand:
    async def send_admin(self: "ClientManger", msg: Message):
        admins = UsersTBL.get_sudo()

        if not admins:
            return

        for admin in admins:
            await self.send_message(admin.user_id,
                                    self.texts.generate_confirm_user_add_start(msg.from_user.full_name,
                                                                               msg.from_user.id),
                                    reply_markup=self.keys.generate_add_new_admin_from_start_keyboard())

    async def access_denied(self: "ClientManger", msg: Message):
        await self.send_admin(msg)
        return await msg.reply_text(self.texts.CAN_NOT_START_BOT)

    @admin_required
    async def start_command(self: "ClientManger", clt, msg: Message):
        return await msg.reply_text(self.texts.START_TEXT)
