from typing import TYPE_CHECKING

from pyrogram.types import CallbackQuery

from db.models import AccountsTBL, TelegramOperationTBL, UsersTBL
from utils.user_permissions import sudo_required

if TYPE_CHECKING:
    from client_manager.base import ClientManager


class SudoManager:
    @sudo_required
    async def show_global_history(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
    ):
        operations = TelegramOperationTBL.get_operations(limit=100)
        await msg.answer()
        await msg.message.reply_text(
            self.texts.operation_report(
                operations,
                title="گزارش کلی عملیات",
            )
        )

    @sudo_required
    async def show_users(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
    ):
        users = UsersTBL.get_users()
        lines = ["لیست کاربران:"]

        for user in users:
            role = "SUDO" if user.is_sudo else "OPERATOR"
            state = "فعال" if user.is_active else "غیرفعال"
            lines.append(
                f"{user.user_id} | {user.name} | {role} | {state}"
            )

        await msg.answer()
        await msg.message.reply_text("\n".join(lines))

    @sudo_required
    async def sudo_reports(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
    ):
        operations = TelegramOperationTBL.get_operations(limit=100)
        total = len(operations)
        failed = sum(item.status == "failed" for item in operations)
        successful = total - failed
        users = list(UsersTBL.get_users())
        operators = [user for user in users if not user.is_sudo]
        accounts = list(AccountsTBL.get_accounts())
        active_accounts = [account for account in accounts if account.is_active]
        connected_accounts = [
            account
            for account in active_accounts
            if self.get_account_manager(account.admin_id).is_connected(
                account.account_id
            )
        ]

        text = (
            "گزارش کلی\n\n"
            f"اوپراتورها: {len(operators)}\n"
            f"کل اکانت‌ها: {len(accounts)}\n"
            f"اکانت‌های فعال: {len(active_accounts)}\n"
            f"اکانت‌های متصل: {len(connected_accounts)}\n"
            f"کل عملیات ثبت‌شده: {total}\n"
            f"موفق: {successful}\n"
            f"ناموفق: {failed}"
        )
        await msg.answer()
        await msg.message.reply_text(text)

    @sudo_required
    async def operator_reports(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
    ):
        users = list(UsersTBL.get_users(active_only=False))
        operators = [user for user in users if not user.is_sudo]
        await msg.answer()
        await msg.message.edit_text(
            "اوپراتور مورد نظر را انتخاب کنید:",
            reply_markup=self.keys.generate_operator_list(operators),
        )

    @sudo_required
    async def operator_report(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
        operator_id: int,
    ):
        user = UsersTBL.get_user(operator_id)
        if not user or user.is_sudo:
            return await msg.answer("اوپراتور پیدا نشد", show_alert=True)

        accounts = list(AccountsTBL.get_admin_accounts(operator_id))
        operations = TelegramOperationTBL.get_operator_operations(
            operator_id,
            limit=50,
        )
        manager = self.get_account_manager(operator_id)
        connected = sum(
            manager.is_connected(account.account_id)
            for account in accounts
        )
        active = sum(account.is_active for account in accounts)

        text = (
            f"گزارش اوپراتور: {user.name}\n"
            f"شناسه: {operator_id}\n"
            f"اکانت‌ها: {len(accounts)}\n"
            f"اکانت‌های فعال: {active}\n"
            f"اکانت‌های متصل: {connected}\n"
            f"تعداد عملیات: {len(operations)}\n\n"
            f"{self.texts.operation_report(operations, 'آخرین عملیات')}"
        )
        await msg.answer()
        await msg.message.reply_text(text)

    @sudo_required
    async def connected_accounts(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
    ):
        accounts = [
            account
            for account in AccountsTBL.get_accounts(active_only=True)
            if self.get_account_manager(account.admin_id).is_connected(account.account_id)
        ]

        if not accounts:
            text = "در حال حاضر هیچ اکانتی متصل نیست."
        else:
            lines = ["اکانت‌های متصل:"]
            for account in accounts:
                owner = UsersTBL.get_user(account.admin_id)
                lines.append(
                    f"🟢 {account.display_name} | "
                    f"operator={owner.name if owner else account.admin_id}"
                )
            text = "\n".join(lines)

        await msg.answer()
        await msg.message.reply_text(text)

