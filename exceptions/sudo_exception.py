from .base import BotBaseException


class UserIsSudo(BotBaseException):
    def __init__(self, user_id: int | str, work: str):
        super().__init__(
            message=f"can not do {work} because user is sudo in bot"
        )
