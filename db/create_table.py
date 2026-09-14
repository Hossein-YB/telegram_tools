from typing import Iterable

from db.models import TABLES, UsersTBL, database


def init_database(sudo_ids: Iterable[int]) -> None:
    with database:
        database.create_tables(TABLES, safe=True)

        for index, sudo_id in enumerate(sudo_ids):
            user = UsersTBL.insert_user(
                sudo_id,
                f"sudo{index}",
                True,
            )
            # insert_user() is a no-op if the user already exists (e.g. was
            # previously added as a regular operator), so make sure anyone
            # listed in SUDO_ID is actually promoted to sudo.
            if not user.is_sudo:
                UsersTBL.update_user(sudo_id, is_sudo=True)
