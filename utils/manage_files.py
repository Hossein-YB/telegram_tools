import os
from config import LOG_FILE_PATH


def log_directory() -> str:
    if not os.path.exists(LOG_FILE_PATH):
        os.makedirs(LOG_FILE_PATH)
    return LOG_FILE_PATH


def generate_log_files(name: str) -> str:
    return os.path.join(log_directory(), name)

