from conversation.message_handler import CustomMessageHandler as MessageHandler
# from conversation.callback_query_handler import CallbackQueryHandler
from pyrogram.handlers import CallbackQueryHandler
from pyrogram import filters
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from client_manager.base import ClientManger

class Handlers:

    def set_handlers(self: "ClientManger"):
        self.set_handlers_public_methods()
        self.set_handlers_admin()

    def set_handlers_public_methods(self: "ClientManger"):
        self.add_handler(MessageHandler(self.start_command, filters.command("start")))

    def set_handlers_admin(self: "ClientManger"):
        self.add_handler(MessageHandler(self.admin_panel, filters.command("admin")))
        # user handlers
        self.add_handler(CallbackQueryHandler(self.add_new_op, filters.regex(f"^{self.keys.ADD_NEW_OPERATOR_CALL}$")))
        self.add_handler(CallbackQueryHandler(self.add_new_op_from_start, filters.regex(f"^{self.keys.ADD_ADMIN_FROM_START_call}$")))

        # account handlers
        self.add_handler(CallbackQueryHandler(self.add_new_account, filters.regex(f"^{self.keys.ADD_NEW_ACCOUNT_CALL}$")))


