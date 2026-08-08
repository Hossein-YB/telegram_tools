from conversation.message_handler import CustomMessageHandler as MessageHandler
from conversation.callback_query_handler import CallbackQueryHandler as QueryHandler
from pyrogram import filters
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from client_manager.base import ClientManger

class Handlers:

    def set_handlers(self: "ClientManger"):
        self.set_handlers_public_methods()

    def set_handlers_public_methods(self: "ClientManger"):
        self.add_handler(MessageHandler(self.start_command, filters.command("start")))
