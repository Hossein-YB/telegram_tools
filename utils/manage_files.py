import os
from config import LOG_FILE_PATH, SESSIONS_PATH, BASE_DIR


def log_directory() -> str:
    if not os.path.exists(LOG_FILE_PATH):
        os.makedirs(LOG_FILE_PATH)
    return LOG_FILE_PATH


def generate_log_files(name: str) -> str:
    return os.path.join(log_directory(), name)


def session_directory() -> str:
    if not os.path.exists(SESSIONS_PATH):
        os.makedirs(SESSIONS_PATH)
    return SESSIONS_PATH


def generate_session_path(name: str) -> str:
    name = name.replace("+", "")
    return os.path.join(session_directory(), name)


def delete_session_file(name: str = None, path: str = None):
    if not path and name:
        path = generate_session_path(name)

    if os.path.exists(path):
        os.remove(path)
    return True

