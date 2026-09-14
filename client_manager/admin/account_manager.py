from typing import TYPE_CHECKING

from pyrogram.types import CallbackQuery

from services.account_manager import AccountManager as TelegramAccountManager
from utils.logger import get_logger
from utils.user_permissions import admin_required

if TYPE_CHECKING:
    from client_manager.base import ClientManager


logger = get_logger(__name__)


class AccountCommands:
    @admin_required
    async def add_new_account(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
    ):
        manager = self.get_account_manager(msg.from_user.id)

        try:
            name_message = await self.ask(
                chat_id=msg.from_user.id,
                text=self.texts.ACCOUNT_NAME,
                reply_markup=self.keys.generate_cancel_key(),
                timeout=self.timeout_second,
            )
            if not name_message or not name_message.text:
                return
            if name_message.text == self.keys.CANCEL_TXT:
                return await name_message.reply_text(
                    self.texts.CANCELED_COMMAND,
                    reply_markup=self.keys.generate_remove_keyboard(),
                )

            phone_message = await self.ask(
                chat_id=msg.from_user.id,
                text=self.texts.ACCOUNT_PHONE,
                reply_markup=self.keys.generate_cancel_key(),
                timeout=self.timeout_second,
            )
            if not phone_message or not phone_message.text:
                return
            if phone_message.text == self.keys.CANCEL_TXT:
                return await phone_message.reply_text(
                    self.texts.CANCELED_COMMAND,
                    reply_markup=self.keys.generate_remove_keyboard(),
                )

            phone_number = phone_message.text.strip()
            sent_code = await manager.start_login(
                phone_number=phone_number,
                display_name=name_message.text.strip(),
            )

            code_message = await self.ask(
                chat_id=msg.from_user.id,
                text=self.texts.get_code_telegram_in_app(sent_code),
                reply_markup=self.keys.generate_cancel_key(),
                timeout=self.timeout_second,
            )
            if not code_message or not code_message.text:
                return
            if code_message.text == self.keys.CANCEL_TXT:
                return await code_message.reply_text(
                    self.texts.CANCELED_COMMAND,
                    reply_markup=self.keys.generate_remove_keyboard(),
                )

            try:
                account = await manager.verify_login(
                    phone_number=phone_number,
                    phone_code=code_message.text.strip(),
                )
            except ValueError as exc:
                if "Two-step verification" not in str(exc):
                    raise

                password_message = await self.ask(
                    chat_id=msg.from_user.id,
                    text=self.texts.ACCOUNT_PASSWORD,
                    reply_markup=self.keys.generate_cancel_key(),
                    timeout=self.timeout_second,
                )
                if not password_message or not password_message.text:
                    return
                if password_message.text == self.keys.CANCEL_TXT:
                    return await password_message.reply_text(
                        self.texts.CANCELED_COMMAND,
                        reply_markup=self.keys.generate_remove_keyboard(),
                    )

                account = await manager.verify_login(
                    phone_number=phone_number,
                    phone_code=code_message.text.strip(),
                    password=password_message.text,
                )

            return await msg.message.reply_text(
                self.texts.account_added(account),
                reply_markup=self.keys.generate_remove_keyboard(),
            )

        except Exception as exc:
            logger.error("add_new_account failed: %s", exc, exc_info=True)
            return await msg.message.reply_text(
                f"{self.texts.OPERATION_ERROR}\n{exc}",
                reply_markup=self.keys.generate_remove_keyboard(),
            )

    @admin_required
    async def retry_account_login(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
        account_id: int,
    ):
        manager = self.get_account_manager(msg.from_user.id)
        account = manager.get_account(account_id)

        try:
            sent_code = await manager.start_login(
                phone_number=account.phone_number,
                display_name=account.display_name,
            )
            code_message = await self.ask(
                chat_id=msg.from_user.id,
                text=self.texts.get_code_telegram_in_app(sent_code),
                reply_markup=self.keys.generate_cancel_key(),
                timeout=self.timeout_second,
            )
            if not code_message or not code_message.text:
                return

            try:
                account = await manager.verify_login(
                    account.phone_number,
                    code_message.text.strip(),
                )
            except ValueError as exc:
                if "Two-step verification" not in str(exc):
                    raise

                password_message = await self.ask(
                    chat_id=msg.from_user.id,
                    text=self.texts.ACCOUNT_PASSWORD,
                    reply_markup=self.keys.generate_cancel_key(),
                    timeout=self.timeout_second,
                )
                account = await manager.verify_login(
                    account.phone_number,
                    code_message.text.strip(),
                    password=password_message.text.strip(),
                )

            await msg.message.reply_text(
                self.texts.account_added(account),
                reply_markup=self.keys.generate_remove_keyboard(),
            )
        except Exception as exc:
            logger.error("retry_account_login failed: %s", exc, exc_info=True)
            await msg.message.reply_text(
                f"{self.texts.OPERATION_ERROR}\n{exc}",
                reply_markup=self.keys.generate_remove_keyboard(),
            )

    def get_account_manager(
        self: "ClientManager",
        operator_id: int,
        actor_id: int | None = None,
    ) -> TelegramAccountManager:
        manager = self.account_managers.get(operator_id)

        if manager is None:
            manager = TelegramAccountManager(
                operator_id=operator_id,
                actor_id=actor_id or operator_id,
            )
            self.account_managers[operator_id] = manager
        elif actor_id is not None:
            manager.actor_id = actor_id

        return manager
