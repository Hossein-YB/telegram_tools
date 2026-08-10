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
    return os.path.join(session_directory(), name)


if __name__ == '__main__':
    print(BASE_DIR, generate_session_path("+989129875252"))