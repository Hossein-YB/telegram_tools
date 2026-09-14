from typing import TYPE_CHECKING

from db.models import UsersTBL
from pyrogram.types import Message

from utils.user_permissions import admin_required

if TYPE_CHECKING:
    from client_manager.base import ClientManager


class StartCommand:
    async def send_admin(
        self: "ClientManager",
        msg: Message,
    ):
        for admin in UsersTBL.get_sudo():
            await self.send_message(
                admin.user_id,
                self.texts.generate_confirm_user_add_start(
                    msg.from_user.full_name,
                    msg.from_user.id,
                ),
                reply_markup=self.keys.generate_add_new_admin_from_start_keyboard(
                    msg.from_user.id,
                ),
            )

    async def access_denied(
        self: "ClientManager",
        msg: Message,
    ):
        await self.send_admin(msg)
        return await msg.reply_text(self.texts.CAN_NOT_START_BOT)

    @admin_required
    async def start_command(
        self: "ClientManager",
        clt,
        msg: Message,
    ):
        return await msg.reply_text(
            self.texts.ADMIN_PANEL,
            reply_markup=self.keys.generate_admin_keyboards(
                is_sudo=False,
            ),
        )
