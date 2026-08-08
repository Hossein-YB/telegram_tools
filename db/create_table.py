from typing import List
from db.models import database, UsersTBL
from config import SUDO_IDS


def init_database(sudo_ids: List[int]):
    with database:
        database.create_tables([
            UsersTBL,
        ])
        for sudo in sudo_ids:
            UsersTBL.insert_user(sudo, f"sudo{sudo_ids.index(sudo)}", True)


if __name__ == '__main__':
    init_database(sudo_ids=SUDO_IDS)
