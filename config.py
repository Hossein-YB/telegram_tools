import os
from decouple import config

# telegram api config
API_ID = config("API_ID", cast=int)
API_HASH = config("API_HASH")

# sudo config
SUDO_IDS = config("SUDO_ID", cast=lambda v: [int(s.strip()) for s in v.split(',')])

# mysql config
DB_NAME = config("DB_NAME")
DB_USER = config("DB_USER")
DB_USER_PASS = config("DB_USER_PASS")
DB_PORT = config("DB_PORT", cast=int)


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOG_FILE_PATH = os.path.join(BASE_DIR, 'logs')
