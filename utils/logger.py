import logging
import logging.handlers
import sys
from typing import Optional

from utils.manage_files import generate_log_files


class LoggerSetup:
    _instance: Optional["LoggerSetup"] = None
    _initialized: bool = False

    def __new__(cls) -> "LoggerSetup":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._setup_handlers()
        self._initialized = True

    def _setup_handlers(self) -> None:
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(name)s] - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler = logging.handlers.RotatingFileHandler(
            generate_log_files('errors.log'),
            maxBytes=10_000_000,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(formatter)

        self.logger = logging.getLogger('logger')
        self.logger.setLevel(logging.ERROR)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.propagate = False

    def get_logger(self, name: str = None) -> logging.Logger:
        if name:
            logger = logging.getLogger(f'logger.{name}')
        else:
            logger = self.logger

        logger.setLevel(logging.ERROR)
        logger.propagate = True
        return logger


logger_setup = LoggerSetup()


def get_logger(name: str = None) -> logging.Logger:
    return logger_setup.get_logger(name)
