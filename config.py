from decouple import config, Csv


API_ID = config("API_ID", cast=int)
API_HASH = config("API_HASH")

SUDO_IDS = config("SUDO_ID", cast=lambda v: [int(s.strip()) for s in v.split(',')])
FORWARD_INTERVAL_MINUTES = 20
JOIN_DELAY_MINUTES = 2

DATABASE_NAME = "database.db"
LOG_FILE = "bot.log"
LOG_LEVEL = "INFO"

