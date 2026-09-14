from typing import TYPE_CHECKING

from pyrogram.types import CallbackQuery

from conversation.utils.exceptions import ListenerTimeout
from db.models import UsersTBL
from utils.user_permissions import sudo_required

if TYPE_CHECKING:
    from client_manager.base import ClientManager


class OperatorManager:
    @sudo_required
    async def add_new_op(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
    ):
        try:
            while True:
                response = await self.ask(
                    chat_id=msg.from_user.id,
                    text=self.texts.FORWARD_OP_MSG,
                    reply_markup=self.keys.generate_cancel_key(),
                    timeout=self.timeout_second,
                )

                if response and response.text == self.keys.CANCEL_TXT:
                    return await response.reply_text(
                        self.texts.CANCELED_COMMAND,
                        reply_markup=self.keys.generate_remove_keyboard(),
                    )

                if not response or not response.forward_origin:
                    await self.send_message(
                        chat_id=msg.from_user.id,
                        text=self.texts.FORWARD_FROM_A_USER,
                    )
                    continue

                sender_user = getattr(
                    response.forward_origin,
                    "sender_user",
                    None,
                )

                if not sender_user:
                    await self.send_message(
                        chat_id=msg.from_user.id,
                        text=self.texts.FORWARD_FROM_A_USER,
                    )
                    continue

                name = sender_user.full_name
                user_id = sender_user.id

                confirm = await self.ask(
                    chat_id=msg.from_user.id,
                    text=self.texts.generate_confirm_user_add(
                        name,
                        user_id,
                    ),
                    reply_markup=self.keys.generate_confirm_ok_cancel_key(),
                    timeout=self.timeout_second,
                )

                if confirm and confirm.text == self.keys.OK_TXT:
                    UsersTBL.insert_user(user_id, name)
                    return await confirm.reply_text(
                        self.texts.USER_SUCCESSFULLY_INSERTED,
                        reply_markup=self.keys.generate_remove_keyboard(),
                    )

        except ListenerTimeout:
            return await self.send_message(
                msg.from_user.id,
                self.texts.TIME_OUT,
                reply_markup=self.keys.generate_remove_keyboard(),
            )

    @sudo_required
    async def add_new_op_from_start(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
    ):
        parts = msg.data.split(":")
        if len(parts) != 2:
            return await msg.answer("درخواست نامعتبر است", show_alert=True)

        user_id = int(parts[1])
        user = await self.get_users(user_id)
        if not user:
            return await msg.answer("کاربر پیدا نشد", show_alert=True)

        UsersTBL.insert_user(user.id, user.full_name)
        await msg.answer("کاربر اضافه شد")
        await msg.message.edit_reply_markup(None)

        return await self.send_message(
            user.id,
            self.texts.BOT_OPEN_LUCK,
        )
