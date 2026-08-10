from datetime import datetime
from typing import Optional, Any

from peewee import (
    Model,
    BooleanField,
    BigIntegerField,
    CharField,
    ForeignKeyField,
    DateTimeField,
    AutoField,
    DoesNotExist,
    ModelSelect,
)
from playhouse.shortcuts import ReconnectMixin
from playhouse.pool import PooledMySQLDatabase

from exceptions import UserIsSudo
from utils.logger import get_logger
from config import DB_NAME, DB_USER, DB_USER_PASS, DB_PORT


class ReconnectMySQLDatabase(ReconnectMixin, PooledMySQLDatabase):
    pass


logger = get_logger(__name__)

database = ReconnectMySQLDatabase(
    database=DB_NAME,
    user=DB_USER,
    passwd=DB_USER_PASS,
    port=DB_PORT,
    charset="utf8mb4",
)


class BaseModel(Model):
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)

    class Meta:
        database = database


class UsersTBL(BaseModel):
    user_id = BigIntegerField(primary_key=True, index=True)
    name = CharField(max_length=50)
    is_sudo = BooleanField(default=False)
    is_active = BooleanField(default=True)

    @classmethod
    def insert_user(cls, user_id, name, is_sudo=False) -> "UsersTBL":
        try:
            return cls.get(cls.user_id == user_id)
        except DoesNotExist:
            return cls.create(
                user_id=user_id,
                name=name,
                is_sudo=is_sudo
            )
        except Exception as e:
            logger.error(f"insert_user failed for {user_id}: {e}")
            raise

    @classmethod
    def change_status(cls, user_id: int) -> "UsersTBL":
        try:
            u = cls.get_or_none(cls.user_id == user_id)

            if not u:
                raise ValueError(f"User {user_id} not found")

            if u.is_sudo:
                raise UserIsSudo(user_id, "change_status UserTBL")

            u.is_active = not u.is_active
            u.save()

            return u

        except Exception as e:
            logger.error(f"change_status failed for {user_id}: {e}")
            raise

    @classmethod
    def get_admins(cls) -> ModelSelect["UsersTBL"] | list[Any]:
        try:
            return cls.select()
        except Exception as e:
            logger.error(f"get_admins failed: {e}")
            return []

    @classmethod
    def get_sudo(cls) -> ModelSelect["UsersTBL"] | list[Any]:
        try:
            return cls.select().where(cls.is_sudo == True)
        except Exception as e:
            logger.error(f"get_sudo failed: {e}")
            return []

    @classmethod
    def get_admin(cls, user_id) -> Optional["UsersTBL"]:
        try:
            return cls.get_or_none(cls.user_id == user_id)
        except Exception as e:
            logger.error(f"get_admin failed for {user_id}: {e}")
            return None

    @classmethod
    def check_is_admin(cls, user_id: int) -> bool:
        return bool(cls.get_or_none(cls.user_id == user_id, cls.is_active == True))

    @classmethod
    def check_is_sudo(cls, user_id: int) -> bool:
        return bool(cls.get_or_none(cls.user_id == user_id, cls.is_sudo == True))


class AccountsTBL(BaseModel):
    account_id = AutoField(primary_key=True)

    admin = ForeignKeyField(UsersTBL, column_name="admin_id", field=UsersTBL.user_id, backref="accounts",
                            on_delete="CASCADE", )
    phone_number = CharField(max_length=15, unique=True)
    session_link = CharField(max_length=400, null=True)
    last_usage = BigIntegerField(null=True)
    last_command = CharField(max_length=200, null=True)

    @classmethod
    def insert_account(cls, admin: UsersTBL, phone_number: str, session_link: Optional[str] = None, ) -> "AccountsTBL":
        try:
            account = cls.get_or_none(cls.phone_number == phone_number)

            if account:
                return account

            return cls.create(admin=admin, phone_number=phone_number, session_link=session_link, )
        except Exception as e:
            logger.error(f"insert_account failed for {phone_number}: {e}")
            raise

    @classmethod
    def get_account(cls, account_id: int):
        return cls.get_or_none(cls.account_id == account_id)

    @classmethod
    def get_admin_accounts(cls, admin_id: int):
        return cls.select().where(cls.admin == admin_id)

    @classmethod
    def update_session(cls, account_id: int, session_link: str):
        account = cls.get_or_none(cls.account_id == account_id)

        if not account:
            return None

        account.session_link = session_link
        account.save()

        return account


class GroupsTBL(BaseModel):
    group_id = BigIntegerField(primary_key=True)
    group_title = CharField(max_length=255)
    group_link = CharField(max_length=300, null=True)

    @classmethod
    def insert_group(cls, group_id: int, group_title: str, group_link: Optional[str] = None) -> "GroupsTBL":

        try:
            group = cls.get_or_none(cls.group_id == group_id)

            if group:
                group.group_title = group_title
                group.group_link = group_link
                group.save()

                return group

            return cls.create(
                group_id=group_id,
                group_title=group_title,
                group_link=group_link,
            )

        except Exception as e:
            logger.error(f"insert_group failed for {group_id}: {e}")
            raise

    @classmethod
    def get_group(cls, group_id: int):
        return cls.get_or_none(cls.group_id == group_id)


class AccountCategoryTBL(BaseModel):
    category_id = AutoField(primary_key=True)
    account = ForeignKeyField(AccountsTBL, column_name="account_id", backref="categories", on_delete="CASCADE", )
    name = CharField(max_length=100)

    @classmethod
    def insert_category(cls, account: AccountsTBL, name: str, ) -> "AccountCategoryTBL":
        try:
            category = cls.get_or_none((cls.account == account) & (cls.name == name))

            if category:
                return category

            return cls.create(account=account, name=name)

        except Exception as e:
            logger.error(f"insert_category failed: {e}")
            raise

    @classmethod
    def get_category(cls, category_id: int):
        return cls.get_or_none(cls.category_id == category_id)

    @classmethod
    def get_account_categories(cls, account_id: int):
        return cls.select().where(cls.account == account_id)


class AccountGroupTBL(BaseModel):
    relation_id = AutoField(primary_key=True)
    account = ForeignKeyField(AccountsTBL, column_name="account_id", backref="group_relations", on_delete="CASCADE", )
    group = ForeignKeyField(GroupsTBL, column_name="group_id", backref="account_relations", on_delete="CASCADE", )
    category = ForeignKeyField(AccountCategoryTBL, column_name="category_id", backref="group_relations",
                               on_delete="CASCADE", )

    @classmethod
    def insert_group(cls, account: AccountsTBL, group: GroupsTBL, category: AccountCategoryTBL, ) -> "AccountGroupTBL":

        try:
            relation = cls.get_or_none((cls.account == account) & (cls.group == group) & (cls.category == category))

            if relation:
                return relation

            return cls.create(account=account, group=group, category=category, )

        except Exception as e:
            logger.error(f"insert account-group failed: {e}")
            raise

    @classmethod
    def get_account_groups(cls, account_id: int):
        return cls.select().where(
            cls.account == account_id
        )

    @classmethod
    def get_category_groups(cls, category_id: int):
        return cls.select().where(cls.category == category_id)

    @classmethod
    def get_group_categories(cls, account_id: int, group_id: int):
        return cls.select().where((cls.account == account_id) & (cls.group == group_id))

    @classmethod
    def exists(cls, account_id: int, group_id: int, category_id: int) -> bool:

        return bool(
            cls.get_or_none((cls.account == account_id) & (cls.group == group_id) & (cls.category == category_id))
        )


class ForwardHistoryTBL(BaseModel):
    history_id = AutoField(primary_key=True)
    account = ForeignKeyField(AccountsTBL, column_name="account_id", backref="forward_histories", on_delete="CASCADE", )
    group = ForeignKeyField(GroupsTBL, column_name="group_id", backref="forward_histories", on_delete="CASCADE", )
    message_id = BigIntegerField()

    @classmethod
    def insert_history(cls, account: AccountsTBL, group: GroupsTBL, message_id: int, ) -> "ForwardHistoryTBL":

        try:
            return cls.create(account=account, group=group, message_id=message_id, )

        except Exception as e:
            logger.error(f"insert forward history failed: {e}")
            raise

    @classmethod
    def get_account_history(cls, account_id: int):
        return cls.select().where(cls.account == account_id)

    @classmethod
    def get_group_history(cls, group_id: int):
        return cls.select().where(cls.group == group_id)
