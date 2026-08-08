from .base import BaseException


class UserIsSudo(BaseException):
    def __init__(self, work: str):
        super().__init__(
            message=f"can not do {work} because user is sudo in bot"
        )
