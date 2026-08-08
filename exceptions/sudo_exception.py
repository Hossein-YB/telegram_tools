from .base import BaseException


class UserIsSudo(BaseException):
    def __init__(self, user_id: int | str, work: str):
        super().__init__(
            message=f"can not do {work} because user is sudo in bot"
        )
