from client_manager.message.Messages import Messages
from conversation.client import CustomClient
from client_manager.handlers.handler import Handlers
from .public_method import PublicMethods


class ClientManger(PublicMethods, Handlers, CustomClient):

    def __init__(self, name, api_id, api_hash, bot_token, **kwargs):
        self.texts = Messages()
        super().__init__(name=name, api_id=api_id, api_hash=api_hash, bot_token=bot_token, **kwargs)

    def start(self):
        self.set_handlers()
        return super().start()
