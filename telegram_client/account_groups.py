from datetime import datetime
from typing import Optional

from db.models import AccountsTBL, GroupsTBL, AccountGroupTBL, AccountCategoryTBL


class AccountGroups:
    """Simple DB helper for account/group relations.

    Telegram API calls belong to TelegramClient/AccountManager; this class only
    persists the relation.
    """

    @staticmethod
    def add(account_id: int, group_id: int, title: str, username: str | None = None,
            link: str | None = None, category_id: int | None = None):
        account = AccountsTBL.get_account(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")

        group = GroupsTBL.insert_group(group_id=group_id, group_title=title, group_username=username, group_link=link, )
        category = AccountCategoryTBL.get_category(category_id) if category_id else None
        return AccountGroupTBL.insert_group(account, group, category)

    @staticmethod
    def list(account_id: int):
        return AccountGroupTBL.get_account_groups(account_id)

    @staticmethod
    def remove(account_id: int, group_id: int):
        return AccountGroupTBL.mark_left(account_id, group_id)
