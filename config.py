from pathlib import Path
from decouple import config

# telegram_client api config
API_ID = config("API_ID", cast=int)
API_HASH = config("API_HASH")
TOKEN = config("TOKEN")

# sudo config
SUDO_IDS = config("SUDO_ID", cast=lambda v: [int(s.strip()) for s in v.split(',')])

# mysql config
DB_NAME = config("DB_NAME")
DB_USER = config("DB_USER")
DB_USER_PASS = config("DB_USER_PASS")
DB_PORT = config("DB_PORT", cast=int)

# Base directory
BASE_DIR = Path(__file__).parent.resolve()

# Logs directory
LOG_FILE_PATH = BASE_DIR / 'logs'

# Sessions directory
SESSIONS_PATH = BASE_DIR / 'sessions'

# Optional: Create directories on import
LOG_FILE_PATH.mkdir(parents=True, exist_ok=True)
SESSIONS_PATH.mkdir(parents=True, exist_ok=True)
