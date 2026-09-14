from typing import TYPE_CHECKING

from pyrogram.types import CallbackQuery, Message

from db.models import AccountGroupTBL, AccountsTBL, TelegramOperationTBL, UsersTBL
from utils.user_permissions import admin_required, sudo_required

if TYPE_CHECKING:
    from client_manager.base import ClientManager


class AdminPanel:
    @admin_required
    async def admin_panel(
        self: "ClientManager",
        clt,
        msg: Message,
    ):
        await msg.reply_text(
            self.texts.ADMIN_PANEL,
            reply_markup=self.keys.generate_admin_keyboards(
                is_sudo=False,
            ),
        )

    @sudo_required
    async def sudo_panel(
        self: "ClientManager",
        clt,
        msg: Message | CallbackQuery,
    ):
        message = msg.message if isinstance(msg, CallbackQuery) else msg
        await message.reply_text(
            self.texts.SUDO_PANEL,
            reply_markup=self.keys.generate_sudo_panel(),
        )

    @admin_required
    async def show_accounts(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
    ):
        manager = self.get_account_manager(msg.from_user.id)
        accounts = manager.get_accounts()

        await msg.answer()
        await msg.message.edit_text(
            self.texts.NO_ACCOUNTS if not accounts else "اکانت‌های شما:",
            reply_markup=self.keys.generate_accounts_keyboard(
                accounts,
                manager=manager,
            ),
        )

    @admin_required
    async def account_details(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
        account_id: int,
    ):
        manager = self.get_account_manager(msg.from_user.id)
        account = manager.get_account(account_id)

        await msg.answer()
        await msg.message.edit_text(
            self.texts.account_details(
                account,
                manager.is_connected(account.account_id),
            ),
            reply_markup=self.keys.generate_account_actions(account),
        )

    @admin_required
    async def connect_account(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
        account_id: int,
    ):
        manager = self.get_account_manager(msg.from_user.id)
        account = manager.get_account(account_id)

        try:
            await manager.connect_account(account_id)
            await msg.answer("اکانت متصل شد 🟢")
        except Exception as exc:
            await msg.answer(f"اتصال اکانت ناموفق بود: {exc}", show_alert=True)

        account = manager.get_account(account_id)
        await msg.message.edit_text(
            self.texts.account_details(
                account,
                manager.is_connected(account.account_id),
            ),
            reply_markup=self.keys.generate_account_actions(
                account,
                connected=manager.is_connected(account.account_id),
            ),
        )

    @admin_required
    async def disconnect_account(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
        account_id: int,
    ):
        manager = self.get_account_manager(msg.from_user.id)
        account = manager.get_account(account_id)

        try:
            await manager.disconnect_account(account_id)
            await msg.answer("اتصال اکانت قطع شد ⚪")
        except Exception as exc:
            await msg.answer(f"قطع اتصال ناموفق بود: {exc}", show_alert=True)

        account = manager.get_account(account_id)
        await msg.message.edit_text(
            self.texts.account_details(
                account,
                manager.is_connected(account.account_id),
            ),
            reply_markup=self.keys.generate_account_actions(
                account,
                connected=manager.is_connected(account.account_id),
            ),
        )

    @admin_required
    async def toggle_account(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
        account_id: int,
        enabled: bool,
    ):
        manager = self.get_account_manager(msg.from_user.id)
        account = manager.get_account(account_id)

        if enabled:
            manager.activate_account(account_id)
        else:
            await manager.disable_account(account_id)

        account = manager.get_account(account_id)
        await msg.answer("انجام شد")
        await msg.message.edit_text(
            self.texts.account_details(
                account,
                manager.is_connected(account.account_id),
            ),
            reply_markup=self.keys.generate_account_actions(account),
        )

    @admin_required
    async def delete_account(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
        account_id: int,
    ):
        manager = self.get_account_manager(msg.from_user.id)
        await manager.delete_account(account_id)
        await msg.answer("اکانت حذف شد")
        await self.show_accounts(clt, msg)

    @admin_required
    async def account_report(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
        account_id: int,
    ):
        manager = self.get_account_manager(msg.from_user.id)
        manager.get_account(account_id)
        operations = TelegramOperationTBL.get_account_operations(
            account_id,
            limit=30,
        )
        await msg.answer()
        await msg.message.reply_text(
            self.texts.operation_report(
                operations,
                title=f"گزارش اکانت #{account_id}",
            )
        )

    @admin_required
    async def show_history(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
    ):
        if self.is_sudo(msg.from_user.id):
            return await self.show_global_history(clt, msg)

        operations = TelegramOperationTBL.get_operator_operations(
            msg.from_user.id,
            limit=50,
        )
        await msg.answer()
        await msg.message.reply_text(
            self.texts.operation_report(
                operations,
                title="تاریخچه عملیات شما",
            )
        )
