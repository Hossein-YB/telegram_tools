from conversation.client import CustomClient
from .message.Messages import Messages
from .handlers.handler import Handlers
from .message.keyboards import Keyboards
from .public_method import PublicMethods


class ClientManger(PublicMethods, Handlers, CustomClient):

    def __init__(self, name, api_id, api_hash, bot_token, **kwargs):
        self.texts = Messages()
        self.keys = Keyboards()
        super().__init__(name=name, api_id=api_id, api_hash=api_hash, bot_token=bot_token, **kwargs)

    def start(self):
        self.set_handlers()
        return super().start()
