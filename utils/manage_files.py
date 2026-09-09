from pathlib import Path
from config import LOG_FILE_PATH, SESSIONS_PATH, BASE_DIR


def log_directory() -> Path:
    """Create and return logs directory path"""
    log_path = Path(LOG_FILE_PATH)
    log_path.mkdir(parents=True, exist_ok=True)
    return log_path


def generate_log_files(name: str) -> Path:
    """Generate full path for a log file"""
    return log_directory() / name


def session_directory() -> Path:
    """Create and return sessions directory path"""
    session_path = Path(SESSIONS_PATH)
    session_path.mkdir(parents=True, exist_ok=True)
    return session_path


def generate_session_path(name: str) -> Path:
    """Generate full path for a session file"""
    name = name.replace("+", "")
    return session_directory() / name


def delete_session_file(name: str = None, path: Path = None) -> bool:
    """Delete a session file by name or path"""
    if not path and name:
        path = generate_session_path(name)

    if path and Path(path).exists():
        Path(path).unlink()
        return True
    return False
