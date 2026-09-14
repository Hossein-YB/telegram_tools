from typing import TYPE_CHECKING

from pyrogram import filters

from db.models import UsersTBL
from pyrogram.handlers import CallbackQueryHandler

from conversation.message_handler import CustomMessageHandler as MessageHandler

if TYPE_CHECKING:
    from client_manager.base import ClientManager


class Handlers:
    def set_handlers(self: "ClientManager"):
        self.set_handlers_public_methods()
        self.set_handlers_admin()
        self.set_handlers_forward()

    def set_handlers_public_methods(self: "ClientManager"):
        self.add_handler(
            MessageHandler(
                self.start_command,
                filters.command("start"),
            )
        )
        self.add_handler(
            MessageHandler(
                self.sudo_panel,
                filters.command("admin"),
            )
        )

    def set_handlers_admin(self: "ClientManager"):
        self.add_handler(
            CallbackQueryHandler(
                self.add_new_op,
                filters.regex(r"^s_add_operator$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.add_new_op_from_start,
                filters.regex(r"^a_add_op_st:\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.add_new_account,
                filters.regex(r"^a_ad_account$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.show_accounts,
                filters.regex(r"^a_sh_account$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.show_history,
                filters.regex(r"^a_history$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.show_users,
                filters.regex(r"^a_sh_users$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.show_groups,
                filters.regex(r"^a_groups$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.join_group_callback,
                filters.regex(r"^grp:join:\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.refresh_account_groups_callback,
                filters.regex(r"^grp:refresh:\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.show_account_groups_callback,
                filters.regex(r"^grp:\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.sudo_panel,
                filters.regex(r"^s_panel$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.sudo_reports,
                filters.regex(r"^s_reports$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.operator_reports,
                filters.regex(r"^s_operator_reports$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.operator_report,
                filters.regex(r"^s:operator:\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.connected_accounts,
                filters.regex(r"^s_connected$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.account_details_callback,
                filters.regex(r"^acct:\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.account_toggle_callback,
                filters.regex(r"^acct:(enable|disable):\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.connect_account_callback,
                filters.regex(r"^acct:connect:\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.disconnect_account_callback,
                filters.regex(r"^acct:disconnect:\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.account_report_callback,
                filters.regex(r"^acct:report:\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.account_retry_callback,
                filters.regex(r"^acct:retry:\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.account_delete_callback,
                filters.regex(r"^acct:delete:\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.back_admin_callback,
                filters.regex(r"^back:admin$"),
            )
        )

    def set_handlers_forward(self: "ClientManager"):
        operator_filter = filters.create(
            lambda _, __, message: bool(
                message.from_user
                and UsersTBL.check_is_admin(message.from_user.id)
            )
        )
        self.add_handler(
            MessageHandler(
                self.forward_message_received,
                operator_filter & ~filters.command([
                    "start",
                    "admin",
                ]),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.forward_account_callback,
                filters.regex(r"^fwd:a:\d+:\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.forward_all_callback,
                filters.regex(r"^fwd:all:\d+:\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.forward_group_callback,
                filters.regex(r"^fwd:g:\d+:\d+:-?\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.forward_send_callback,
                filters.regex(r"^fwd:send:\d+:\d+$"),
            )
        )
        self.add_handler(
            CallbackQueryHandler(
                self.forward_back_callback,
                filters.regex(r"^fwd:back:\d+$"),
            )
        )
