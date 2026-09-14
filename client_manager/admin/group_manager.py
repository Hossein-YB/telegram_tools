from typing import TYPE_CHECKING

from pyrogram.types import CallbackQuery

from conversation.utils.exceptions import ListenerTimeout
from db.models import AccountGroupTBL
from utils.logger import get_logger
from utils.user_permissions import admin_required

if TYPE_CHECKING:
    from client_manager.base import ClientManager


logger = get_logger(__name__)


class GroupManager:
    @admin_required
    async def show_groups(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
    ):
        manager = self.get_account_manager(msg.from_user.id)
        accounts = [
            account
            for account in manager.get_accounts()
            if account.is_active and account.is_authorized
        ]

        await msg.answer()
        await msg.message.edit_text(
            self.texts.NO_ACCOUNTS if not accounts else self.texts.SELECT_ACCOUNT_FOR_GROUPS,
            reply_markup=self.keys.generate_group_accounts_keyboard(accounts),
        )

    @admin_required
    async def show_account_groups(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
        account_id: int,
    ):
        manager = self.get_account_manager(msg.from_user.id)
        account = manager.get_account(account_id)

        await msg.answer()
        await msg.message.edit_text(self.texts.FETCHING_GROUPS)

        try:
            relations = await manager.sync_account_groups(account_id)
        except Exception as exc:
            logger.error("sync_account_groups failed: %s", exc, exc_info=True)
            await msg.message.edit_text(
                f"دریافت لیست گروه‌ها ناموفق بود: {exc}",
                reply_markup=self.keys.generate_account_groups_keyboard(account_id),
            )
            return

        await msg.message.edit_text(
            self.texts.account_groups_list(account, relations),
            reply_markup=self.keys.generate_account_groups_keyboard(account_id),
        )

    @admin_required
    async def refresh_account_groups(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
        account_id: int,
    ):
        await self.show_account_groups(clt, msg, account_id)

    @admin_required
    async def join_group_by_link(
        self: "ClientManager",
        clt,
        msg: CallbackQuery,
        account_id: int,
    ):
        manager = self.get_account_manager(msg.from_user.id)
        account = manager.get_account(account_id)

        await msg.answer()

        try:
            while True:
                response = await self.ask(
                    chat_id=msg.from_user.id,
                    text=self.texts.JOIN_GROUP_PROMPT,
                    reply_markup=self.keys.generate_cancel_key(),
                    timeout=self.timeout_second,
                )

                if not response or not response.text:
                    continue

                if response.text == self.keys.CANCEL_TXT:
                    break

                link = response.text.strip()

                try:
                    group = await manager.join_group(account_id, link)
                    await response.reply_text(
                        self.texts.group_joined(group),
                        reply_markup=self.keys.generate_cancel_key(),
                    )
                except Exception as exc:
                    logger.error("join_group failed: %s", exc, exc_info=True)
                    await response.reply_text(
                        f"❌ عضویت در «{link}» ناموفق بود: {exc}",
                        reply_markup=self.keys.generate_cancel_key(),
                    )
        except ListenerTimeout:
            await self.send_message(
                msg.from_user.id,
                self.texts.TIME_OUT,
                reply_markup=self.keys.generate_remove_keyboard(),
            )

        relations = list(
            AccountGroupTBL.get_account_groups(account_id, joined_only=True)
        )
        await self.send_message(
            msg.from_user.id,
            self.texts.CANCELED_COMMAND,
            reply_markup=self.keys.generate_remove_keyboard(),
        )
        await self.send_message(
            msg.from_user.id,
            self.texts.account_groups_list(account, relations),
            reply_markup=self.keys.generate_account_groups_keyboard(account_id),
        )

    # --- callback data adapters (see client_manager/handlers/handler.py) ---

    async def show_account_groups_callback(self, clt, query):
        _, account_id = query.data.split(":")
        return await self.show_account_groups(clt, query, int(account_id))

    async def refresh_account_groups_callback(self, clt, query):
        _, _, account_id = query.data.split(":")
        return await self.refresh_account_groups(clt, query, int(account_id))

    async def join_group_callback(self, clt, query):
        _, _, account_id = query.data.split(":")
        return await self.join_group_by_link(clt, query, int(account_id))
