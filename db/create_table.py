from typing import Iterable

from db.models import TABLES, UsersTBL, database


def init_database(sudo_ids: Iterable[int]) -> None:
    with database:
        database.create_tables(TABLES, safe=True)

        for index, sudo_id in enumerate(sudo_ids):
            UsersTBL.insert_user(
                sudo_id,
                f"sudo{index}",
                True,
            )
