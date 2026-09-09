from datetime import datetime
from typing import Optional

from peewee import (
    Model,
    BooleanField,
    BigIntegerField,
    CharField,
    TextField,
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
    name = CharField(max_length=100)
    is_sudo = BooleanField(default=False)
    is_active = BooleanField(default=True)

    @classmethod
    def insert_user(cls, user_id: int, name: str, is_sudo: bool = False) -> "UsersTBL":
        user = cls.get_or_none(cls.user_id == user_id)
        if user:
            return user
        return cls.create(user_id=user_id, name=name, is_sudo=is_sudo)

    @classmethod
    def get_user(cls, user_id: int) -> Optional["UsersTBL"]:
        return cls.get_or_none(cls.user_id == user_id)

    @classmethod
    def change_status(cls, user_id: int) -> "UsersTBL":
        user = cls.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")
        if user.is_sudo:
            raise UserIsSudo(user_id, "change_status UsersTBL")
        user.is_active = not user.is_active
        user.save()
        return user

    @classmethod
    def get_admins(cls) -> ModelSelect:
        return cls.select()

    @classmethod
    def get_sudo(cls) -> ModelSelect:
        return cls.select().where(cls.is_sudo == True)

    @classmethod
    def check_is_admin(cls, user_id: int) -> bool:
        return bool(cls.get_or_none((cls.user_id == user_id) & (cls.is_active == True)))

    @classmethod
    def check_is_sudo(cls, user_id: int) -> bool:
        return bool(cls.get_or_none((cls.user_id == user_id) & (cls.is_sudo == True)))


class AccountsTBL(BaseModel):
    account_id = AutoField(primary_key=True)
    admin = ForeignKeyField(
        UsersTBL,
        column_name="admin_id",
        field=UsersTBL.user_id,
        backref="accounts",
        on_delete="CASCADE",
    )
    phone_number = CharField(max_length=30, unique=True, index=True)
    session_path = CharField(max_length=500, null=True)
    telegram_user_id = BigIntegerField(null=True, index=True)
    username = CharField(max_length=255, null=True)
    first_name = CharField(max_length=255, null=True)
    last_name = CharField(max_length=255, null=True)
    status = CharField(max_length=30, default="pending", index=True)
    is_authorized = BooleanField(default=False)
    is_active = BooleanField(default=True)
    last_connected_at = DateTimeField(null=True)
    last_disconnected_at = DateTimeField(null=True)
    last_used_at = DateTimeField(null=True)

    @classmethod
    def insert_account(cls, admin: UsersTBL, phone_number: str, session_path: Optional[str] = None) -> "AccountsTBL":
        account = cls.get_by_phone(phone_number)
        if account:
            return account
        return cls.create(admin=admin, phone_number=phone_number, session_path=session_path)

    @classmethod
    def get_account(cls, account_id: int) -> Optional["AccountsTBL"]:
        return cls.get_or_none(cls.account_id == account_id)

    @classmethod
    def get_by_phone(cls, phone_number: str) -> Optional["AccountsTBL"]:
        return cls.get_or_none(cls.phone_number == phone_number)

    @classmethod
    def get_admin_accounts(cls, admin_id: int) -> ModelSelect:
        return cls.select().where(cls.admin == admin_id)

    @classmethod
    def update_login(cls, account_id: int, telegram_user, session_path: Optional[str] = None) -> "AccountsTBL":
        account = cls.get_account(account_id)
        if not account:
            raise ValueError(f"Account {account_id} not found")
        account.telegram_user_id = telegram_user.id
        account.username = getattr(telegram_user, "username", None)
        account.first_name = getattr(telegram_user, "first_name", None)
        account.last_name = getattr(telegram_user, "last_name", None)
        account.session_path = session_path or account.session_path
        account.status = "active"
        account.is_authorized = True
        account.is_active = True
        account.last_connected_at = datetime.now()
        account.last_used_at = datetime.now()
        account.save()
        return account

    @classmethod
    def set_status(cls, account_id: int, status: str) -> Optional["AccountsTBL"]:
        account = cls.get_account(account_id)
        if not account:
            return None
        account.status = status
        account.save()
        return account

    @classmethod
    def mark_connected(cls, account_id: int) -> Optional["AccountsTBL"]:
        account = cls.get_account(account_id)
        if not account:
            return None
        account.status = "active"
        account.is_authorized = True
        account.last_connected_at = datetime.now()
        account.last_used_at = datetime.now()
        account.save()
        return account

    @classmethod
    def mark_disconnected(cls, account_id: int) -> Optional["AccountsTBL"]:
        account = cls.get_account(account_id)
        if not account:
            return None
        account.status = "offline"
        account.last_disconnected_at = datetime.now()
        account.save()
        return account

    @classmethod
    def touch(cls, account_id: int) -> Optional["AccountsTBL"]:
        account = cls.get_account(account_id)
        if not account:
            return None
        account.last_used_at = datetime.now()
        account.save()
        return account

    @classmethod
    def deactivate(cls, account_id: int) -> Optional["AccountsTBL"]:
        account = cls.get_account(account_id)
        if not account:
            return None
        account.is_active = False
        account.status = "disabled"
        account.save()
        return account


class GroupsTBL(BaseModel):
    group_id = BigIntegerField(primary_key=True, index=True)
    group_title = CharField(max_length=255)
    group_username = CharField(max_length=255, null=True)
    group_link = CharField(max_length=500, null=True)
    group_type = CharField(max_length=30, default="group")
    is_active = BooleanField(default=True)

    @classmethod
    def insert_group(
        cls,
        group_id: int,
        group_title: str,
        group_link: Optional[str] = None,
        group_username: Optional[str] = None,
        group_type: str = "group",
    ) -> "GroupsTBL":
        group = cls.get_group(group_id)
        if group:
            group.group_title = group_title or group.group_title
            group.group_link = group_link or group.group_link
            group.group_username = group_username or group.group_username
            group.group_type = group_type or group.group_type
            group.is_active = True
            group.save()
            return group
        return cls.create(
            group_id=group_id,
            group_title=group_title,
            group_link=group_link,
            group_username=group_username,
            group_type=group_type,
        )

    @classmethod
    def get_group(cls, group_id: int) -> Optional["GroupsTBL"]:
        return cls.get_or_none(cls.group_id == group_id)

    @classmethod
    def get_active_groups(cls) -> ModelSelect:
        return cls.select().where(cls.is_active == True)

    @classmethod
    def deactivate(cls, group_id: int) -> Optional["GroupsTBL"]:
        group = cls.get_group(group_id)
        if not group:
            return None
        group.is_active = False
        group.save()
        return group


class AccountCategoryTBL(BaseModel):
    category_id = AutoField(primary_key=True)
    account = ForeignKeyField(AccountsTBL, column_name="account_id", backref="categories", on_delete="CASCADE")
    name = CharField(max_length=100)

    @classmethod
    def insert_category(cls, account: AccountsTBL, name: str) -> "AccountCategoryTBL":
        category = cls.get_or_none((cls.account == account) & (cls.name == name))
        if category:
            return category
        return cls.create(account=account, name=name)

    @classmethod
    def get_category(cls, category_id: int) -> Optional["AccountCategoryTBL"]:
        return cls.get_or_none(cls.category_id == category_id)

    @classmethod
    def get_account_categories(cls, account_id: int) -> ModelSelect:
        return cls.select().where(cls.account == account_id)


class AccountGroupTBL(BaseModel):
    relation_id = AutoField(primary_key=True)
    account = ForeignKeyField(AccountsTBL, column_name="account_id", backref="group_relations", on_delete="CASCADE")
    group = ForeignKeyField(GroupsTBL, column_name="group_id", backref="account_relations", on_delete="CASCADE")
    category = ForeignKeyField(
        AccountCategoryTBL,
        column_name="category_id",
        backref="group_relations",
        null=True,
        on_delete="SET NULL",
    )
    status = CharField(max_length=30, default="joined", index=True)
    joined_at = DateTimeField(null=True)
    left_at = DateTimeField(null=True)

    @classmethod
    def insert_group(
        cls,
        account: AccountsTBL,
        group: GroupsTBL,
        category: Optional[AccountCategoryTBL] = None,
    ) -> "AccountGroupTBL":
        relation = cls.get_relation(account.account_id, group.group_id)
        if relation:
            relation.category = category or relation.category
            relation.status = "joined"
            relation.left_at = None
            relation.joined_at = relation.joined_at or datetime.now()
            relation.save()
            return relation
        return cls.create(
            account=account,
            group=group,
            category=category,
            status="joined",
            joined_at=datetime.now(),
        )

    @classmethod
    def get_relation(cls, account_id: int, group_id: int) -> Optional["AccountGroupTBL"]:
        return cls.get_or_none((cls.account == account_id) & (cls.group == group_id))

    @classmethod
    def get_account_groups(cls, account_id: int) -> ModelSelect:
        return cls.select().where(cls.account == account_id)

    @classmethod
    def get_category_groups(cls, category_id: int) -> ModelSelect:
        return cls.select().where(cls.category == category_id)

    @classmethod
    def get_group_categories(cls, account_id: int, group_id: int) -> ModelSelect:
        return cls.select().where((cls.account == account_id) & (cls.group == group_id))

    @classmethod
    def exists(cls, account_id: int, group_id: int, category_id: Optional[int] = None) -> bool:
        query = (cls.account == account_id) & (cls.group == group_id)
        if category_id is not None:
            query &= cls.category == category_id
        return bool(cls.get_or_none(query))

    @classmethod
    def mark_left(cls, account_id: int, group_id: int) -> Optional["AccountGroupTBL"]:
        relation = cls.get_relation(account_id, group_id)
        if not relation:
            return None
        relation.status = "left"
        relation.left_at = datetime.now()
        relation.save()
        return relation


class TelegramOperationTBL(BaseModel):
    operation_id = AutoField(primary_key=True)
    account = ForeignKeyField(AccountsTBL, column_name="account_id", backref="operations", on_delete="CASCADE")
    operation = CharField(max_length=80, index=True)
    target_type = CharField(max_length=50, null=True)
    target_id = BigIntegerField(null=True, index=True)
    status = CharField(max_length=30, default="success", index=True)
    result = TextField(null=True)
    error = TextField(null=True)
    metadata = TextField(null=True)

    @classmethod
    def log(
        cls,
        account: AccountsTBL,
        operation: str,
        status: str = "success",
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[str] = None,
    ) -> "TelegramOperationTBL":
        return cls.create(
            account=account,
            operation=operation,
            target_type=target_type,
            target_id=target_id,
            status=status,
            result=result,
            error=error,
            metadata=metadata,
        )

    @classmethod
    def get_operation(cls, operation_id: int) -> Optional["TelegramOperationTBL"]:
        return cls.get_or_none(cls.operation_id == operation_id)

    @classmethod
    def get_account_operations(cls, account_id: int, limit: int = 100) -> ModelSelect:
        return cls.select().where(cls.account == account_id).order_by(cls.created_at.desc()).limit(limit)

    @classmethod
    def get_operations(cls, limit: int = 100) -> ModelSelect:
        return cls.select().order_by(cls.created_at.desc()).limit(limit)


# Backward-compatible name for old code. New code should use TelegramOperationTBL.
ForwardHistoryTBL = TelegramOperationTBL


TABLES = [
    UsersTBL,
    AccountsTBL,
    GroupsTBL,
    AccountCategoryTBL,
    AccountGroupTBL,
    TelegramOperationTBL,
]
