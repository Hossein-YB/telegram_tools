from typing import Optional


class BaseException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
