from typing import TYPE_CHECKING

from pyrogram.types import CallbackQuery, Message

from db.models import AccountGroupTBL, AccountsTBL, UsersTBL
from utils.logger import get_logger
from utils.user_permissions import admin_required

if TYPE_CHECKING:
    from client_manager.base import ClientManager


logger = get_logger(__name__)


class Forwarding:
    @admin_required
    async def forward_message_received(
        self: "ClientManager",
        clt,
        msg: Message,
    ):
        manager = self.get_account_manager(msg.from_user.id)
        accounts = [
            account
            for account in manager.get_accounts()
            if account.is_active and account.is_authorized
        ]

        if not accounts:
            return await msg.reply_text(self.texts.NO_ACCOUNTS)

        self.forward_sessions[msg.from_user.id, msg.id] = {
            "chat_id": msg.chat.id,
            "message_ids": [msg.id],
            "account_id": None,
            "selected_ids": set(),
        }
        await msg.reply_text(
            self.texts.FORWARD_PANEL,
            reply_markup=self.keys.generate_forward_accounts(accounts, msg.id),
        )

    @admin_required
    async def forward_account_callback(
        self: "ClientManager",
        clt,
        query: CallbackQuery,
    ):
        _, _, message_id, account_id = query.data.split(":")
        message_id = int(message_id)
        account_id = int(account_id)
        manager = self.get_account_manager(query.from_user.id)
        manager.get_account(account_id)

        groups = list(
            AccountGroupTBL.get_account_groups(
                account_id,
                joined_only=True,
            )
        )
        if not groups:
            return await query.answer(self.texts.NO_GROUPS, show_alert=True)

        selected_ids = {relation.group_id for relation in groups}
        self.forward_sessions[query.from_user.id, message_id] = {
            "chat_id": query.message.reply_to_message.chat.id
            if query.message.reply_to_message
            else self.forward_sessions[query.from_user.id, message_id]["chat_id"],
            "message_ids": [message_id],
            "account_id": account_id,
            "selected_ids": selected_ids,
        }
        await query.answer()
        await query.message.edit_text(
            "گروه‌های مقصد را انتخاب کنید. به‌صورت پیش‌فرض همه انتخاب شده‌اند:",
            reply_markup=self.keys.generate_forward_groups(
                message_id,
                account_id,
                groups,
                selected_ids,
            ),
        )

    @admin_required
    async def forward_all_callback(
        self: "ClientManager",
        clt,
        query: CallbackQuery,
    ):
        _, _, message_id, account_id = query.data.split(":")
        message_id = int(message_id)
        account_id = int(account_id)
        state = self.forward_sessions.get((query.from_user.id, message_id))
        if not state:
            return await query.answer("جلسه فروارد منقضی شده است", show_alert=True)

        groups = list(AccountGroupTBL.get_account_groups(account_id, joined_only=True))
        selected = set(state["selected_ids"])
        all_ids = {relation.group_id for relation in groups}
        state["selected_ids"] = set() if selected == all_ids else all_ids

        await query.answer()
        await query.message.edit_reply_markup(
            self.keys.generate_forward_groups(
                message_id,
                account_id,
                groups,
                state["selected_ids"],
            )
        )

    @admin_required
    async def forward_group_callback(
        self: "ClientManager",
        clt,
        query: CallbackQuery,
    ):
        _, _, message_id, account_id, group_id = query.data.split(":")
        message_id = int(message_id)
        account_id = int(account_id)
        group_id = int(group_id)
        state = self.forward_sessions.get((query.from_user.id, message_id))
        if not state:
            return await query.answer("جلسه فروارد منقضی شده است", show_alert=True)

        selected = state["selected_ids"]
        if group_id in selected:
            selected.remove(group_id)
        else:
            selected.add(group_id)

        groups = list(AccountGroupTBL.get_account_groups(account_id, joined_only=True))
        await query.answer()
        await query.message.edit_reply_markup(
            self.keys.generate_forward_groups(
                message_id,
                account_id,
                groups,
                selected,
            )
        )

    @admin_required
    async def forward_send_callback(
        self: "ClientManager",
        clt,
        query: CallbackQuery,
    ):
        _, _, message_id, account_id = query.data.split(":")
        message_id = int(message_id)
        account_id = int(account_id)
        state = self.forward_sessions.pop((query.from_user.id, message_id), None)
        if not state:
            return await query.answer("جلسه فروارد منقضی شده است", show_alert=True)

        selected_ids = list(state["selected_ids"])
        if not selected_ids:
            return await query.answer("حداقل یک گروه را انتخاب کنید", show_alert=True)

        manager = self.get_account_manager(query.from_user.id)
        account = manager.get_account(account_id)
        await query.answer("فروارد شروع شد")
        await query.message.edit_text(self.texts.FORWARD_STARTED)

        await self.notify_sudos(
            f"👤 کاربر {query.from_user.full_name} در حال فروارد پیام "
            f"به وسیله اکانت {account.display_name} است.\n"
            f"تعداد گروه‌ها: {len(selected_ids)}"
        )

        results = await manager.forward_to_selected_groups(
            account_id=account_id,
            from_chat_id=state["chat_id"],
            message_ids=state["message_ids"],
            group_ids=selected_ids,
        )
        success = sum(item.success for item in results)
        failed = len(results) - success

        text = (
            f"{self.texts.FORWARD_FINISHED}\n\n"
            f"اکانت: {account.display_name}\n"
            f"موفق: {success}\n"
            f"ناموفق: {failed}"
        )
        if failed:
            text += "\n\n" + "\n".join(
                f"❌ {item.target_id}: {item.error}"
                for item in results
                if not item.success
            )

        await query.message.edit_text(text)

    @admin_required
    async def forward_back_callback(
        self: "ClientManager",
        clt,
        query: CallbackQuery,
    ):
        _, _, message_id = query.data.split(":")
        state = self.forward_sessions.get((query.from_user.id, int(message_id)))
        if not state:
            return await query.answer("جلسه فروارد منقضی شده است", show_alert=True)

        manager = self.get_account_manager(query.from_user.id)
        accounts = [
            account
            for account in manager.get_accounts()
            if account.is_active and account.is_authorized
        ]
        await query.answer()
        await query.message.edit_text(
            self.texts.FORWARD_PANEL,
            reply_markup=self.keys.generate_forward_accounts(accounts, int(message_id)),
        )

    async def notify_sudos(self: "ClientManager", text: str):
        for sudo in UsersTBL.get_sudo():
            try:
                await self.send_message(sudo.user_id, text)
            except Exception as exc:
                logger.error("Failed to notify sudo %s: %s", sudo.user_id, exc)

    async def account_details_callback(self, clt, query):
        _, account_id = query.data.split(":")
        return await self.account_details(clt, query, int(account_id))

    async def connect_account_callback(self, clt, query):
        _, _, account_id = query.data.split(":")
        return await self.connect_account(clt, query, int(account_id))

    async def disconnect_account_callback(self, clt, query):
        _, _, account_id = query.data.split(":")
        return await self.disconnect_account(clt, query, int(account_id))

    async def account_toggle_callback(self, clt, query):
        _, action, account_id = query.data.split(":")
        return await self.toggle_account(
            clt,
            query,
            int(account_id),
            action == "enable",
        )

    async def account_report_callback(self, clt, query):
        _, _, account_id = query.data.split(":")
        return await self.account_report(clt, query, int(account_id))

    async def account_retry_callback(self, clt, query):
        _, _, account_id = query.data.split(":")
        return await self.retry_account_login(clt, query, int(account_id))

    async def account_delete_callback(self, clt, query):
        _, _, account_id = query.data.split(":")
        return await self.delete_account(clt, query, int(account_id))

    async def back_admin_callback(self, clt, query):
        await query.answer()
        await query.message.edit_text(
            self.texts.ADMIN_PANEL,
            reply_markup=self.keys.generate_admin_keyboards(
                is_sudo=False,
            ),
        )
