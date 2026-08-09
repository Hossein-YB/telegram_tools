from typing import TYPE_CHECKING

from conversation.utils.exceptions import ListenerTimeout
from utils.user_permissions import sudo_required
from db.models import UsersTBL
from pyrogram.types import Message, CallbackQuery

if TYPE_CHECKING:
    from client_manager.base import ClientManger


class UserManager:
    @sudo_required
    async def add_new_op(self: "ClientManger", clt, msg: CallbackQuery):
        try:
            while True:
                m = await self.ask(chat_id=msg.from_user.id,
                                   text=self.texts.FORWARD_OP_MSG,
                                   reply_markup=self.keys.generate_cancel_key(),
                                   timeout=self.timeout_second)

                if hasattr(m, "text"):
                    if m.text == self.keys.CANCEL_TXT:
                        return await m.reply_text(self.texts.CANCELED_COMMAND,
                                                  reply_markup=self.keys.generate_remove_keyboard())

                if hasattr(m, "forward_origin"):
                    if not hasattr(m.forward_origin, "sender_user"):
                        await m.reply_text(self.texts.FORWARD_FROM_A_USER)
                        await self.send_message(chat_id=msg.from_user.id, text=self.texts.OPRETION_START_AGAIN)
                        continue
                    user = m.forward_origin.sender_user
                    name, user_id = user.full_name, user.id
                    c = await self.ask(chat_id=msg.from_user.id,
                                       text=self.texts.generate_confirm_user_add(name, user_id),
                                       reply_markup=self.keys.generate_confirm_ok_cancel_key(),
                                       timeout=self.timeout_second)
                    if hasattr(c, "text"):
                        if c.text == self.keys.OK_TXT:
                            UsersTBL.insert_user(user_id, name)
                            return await c.reply_text(self.texts.USER_SUCCESSFULLY_INSERTED,
                                                      reply_markup=self.keys.generate_remove_keyboard())
                await self.send_message(chat_id=msg.from_user.id, text=self.texts.OPRETION_START_AGAIN)

        except ListenerTimeout as e:
            await self.send_message(msg.from_user.id, self.texts.TIME_OUT,
                                    reply_markup=self.keys.generate_remove_keyboard())

    @sudo_required
    async def add_new_op_from_start(self: "ClientManger", clt, msg: CallbackQuery):
        user_info = msg.message.text.split("\n")[0]
        name, user_id = user_info.split(":")[1:]
        UsersTBL.insert_user(user_id, name)
        await msg.message.reply_text(self.texts.USER_SUCCESSFULLY_INSERTED,
                                     reply_markup=self.keys.generate_remove_keyboard())
        return await self.send_message(int(user_id), self.texts.BOT_OPEN_LUCK)
