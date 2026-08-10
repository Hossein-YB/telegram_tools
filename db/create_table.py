from typing import List
from db.models import (database, UsersTBL,
                       AccountsTBL,
                       GroupsTBL,
                       AccountCategoryTBL,
                       AccountGroupTBL,
                       ForwardHistoryTBL, )
from config import SUDO_IDS


def init_database(sudo_ids: List[int]):
    with database:
        database.create_tables([
            UsersTBL,
            AccountsTBL,
            GroupsTBL,
            AccountCategoryTBL,
            AccountGroupTBL,
            ForwardHistoryTBL
        ])
        for sudo in sudo_ids:
            UsersTBL.insert_user(sudo, f"sudo{sudo_ids.index(sudo)}", True)
