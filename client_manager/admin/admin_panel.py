from typing import TYPE_CHECKING
from utils.user_permissions import sudo_required

from pyrogram.types import Message

if TYPE_CHECKING:
    from client_manager.base import ClientManger


class AdminPanel:
    @sudo_required
    async def admin_panel(self: "ClientManger", clt, msg: Message):
        return await msg.reply_text(self.texts.ADMIN_PANEL,
                                    reply_markup=self.keys.generate_admin_keyboards())
