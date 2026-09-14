from datetime import datetime
from typing import Optional

from peewee import (
    AutoField,
    BigIntegerField,
    BooleanField,
    CharField,
    DateTimeField,
    ForeignKeyField,
    Model,
    ModelSelect,
    TextField,
)
from playhouse.pool import PooledMySQLDatabase
from playhouse.shortcuts import ReconnectMixin

from config import DB_HOST, DB_NAME, DB_PORT, DB_USER, DB_USER_PASS
from exceptions import UserIsSudo


class ReconnectMySQLDatabase(ReconnectMixin, PooledMySQLDatabase):
    pass


database = ReconnectMySQLDatabase(
    database=DB_NAME,
    user=DB_USER,
    passwd=DB_USER_PASS,
    host=DB_HOST,
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
    def insert_user(
        cls,
        user_id: int,
        name: str,
        is_sudo: bool = False,
    ) -> "UsersTBL":
        user = cls.get_user(user_id)

        if user:
            return user

        return cls.create(
            user_id=user_id,
            name=name,
            is_sudo=is_sudo,
        )

    @classmethod
    def update_user(
        cls,
        user_id: int,
        name: Optional[str] = None,
        is_sudo: Optional[bool] = None,
        is_active: Optional[bool] = None,
    ) -> Optional["UsersTBL"]:
        user = cls.get_user(user_id)

        if not user:
            return None

        if name is not None:
            user.name = name

        if is_sudo is not None:
            user.is_sudo = is_sudo

        if is_active is not None:
            user.is_active = is_active

        user.save()
        return user

    @classmethod
    def delete_user(cls, user_id: int) -> bool:
        user = cls.get_user(user_id)

        if not user:
            return False

        if user.is_sudo:
            raise UserIsSudo(user_id, "delete_user UsersTBL")

        return bool(user.delete_instance(recursive=True))

    @classmethod
    def get_user(cls, user_id: int) -> Optional["UsersTBL"]:
        return cls.get_or_none(cls.user_id == user_id)

    @classmethod
    def get_users(cls, active_only: bool = False) -> ModelSelect:
        query = cls.select().order_by(cls.created_at.desc())

        if active_only:
            query = query.where(cls.is_active == True)

        return query

    @classmethod
    def get_sudo(cls) -> ModelSelect:
        return cls.select().where(cls.is_sudo == True)

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
    def check_is_admin(cls, user_id: int) -> bool:
        return bool(
            cls.get_or_none(
                (cls.user_id == user_id) & (cls.is_active == True)
            )
        )

    @classmethod
    def check_is_sudo(cls, user_id: int) -> bool:
        return bool(
            cls.get_or_none(
                (cls.user_id == user_id) & (cls.is_sudo == True)
            )
        )


class AccountsTBL(BaseModel):
    account_id = AutoField(primary_key=True)
    admin = ForeignKeyField(
        UsersTBL,
        column_name="admin_id",
        field=UsersTBL.user_id,
        backref="accounts",
        on_delete="CASCADE",
    )
    display_name = CharField(max_length=100)
    phone_number = CharField(max_length=30, unique=True, index=True)
    session_path = CharField(max_length=500, null=True)
    telegram_user_id = BigIntegerField(null=True, index=True)
    status = CharField(max_length=30, default="pending", index=True)
    is_authorized = BooleanField(default=False)
    is_active = BooleanField(default=True)
    last_connected_at = DateTimeField(null=True)
    last_disconnected_at = DateTimeField(null=True)
    last_used_at = DateTimeField(null=True)

    @classmethod
    def insert_account(
        cls,
        admin: UsersTBL,
        display_name: str,
        phone_number: str,
        session_path: Optional[str] = None,
    ) -> "AccountsTBL":
        account = cls.get_by_phone(phone_number)

        if account:
            if account.admin_id != admin.user_id:
                raise ValueError(
                    "This Telegram account belongs to another operator"
                )
            return account

        return cls.create(
            admin=admin,
            display_name=display_name,
            phone_number=phone_number,
            session_path=session_path,
        )

    @classmethod
    def update_account(
        cls,
        account_id: int,
        display_name: Optional[str] = None,
        session_path: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional["AccountsTBL"]:
        account = cls.get_account(account_id)

        if not account:
            return None

        if display_name is not None:
            account.display_name = display_name

        if session_path is not None:
            account.session_path = session_path

        if is_active is not None:
            account.is_active = is_active

        account.save()
        return account

    @classmethod
    def delete_account(cls, account_id: int) -> bool:
        account = cls.get_account(account_id)

        if not account:
            return False

        return bool(account.delete_instance(recursive=True))

    @classmethod
    def get_account(cls, account_id: int) -> Optional["AccountsTBL"]:
        return cls.get_or_none(cls.account_id == account_id)

    @classmethod
    def get_by_phone(cls, phone_number: str) -> Optional["AccountsTBL"]:
        return cls.get_or_none(cls.phone_number == phone_number)

    @classmethod
    def get_admin_accounts(
        cls,
        admin_id: int,
        active_only: bool = False,
    ) -> ModelSelect:
        query = cls.select().where(cls.admin == admin_id)

        if active_only:
            query = query.where(cls.is_active == True)

        return query.order_by(cls.created_at.desc())

    @classmethod
    def get_accounts(cls, active_only: bool = False) -> ModelSelect:
        query = cls.select().order_by(cls.created_at.desc())

        if active_only:
            query = query.where(cls.is_active == True)

        return query

    @classmethod
    def update_login(
        cls,
        account_id: int,
        telegram_user,
        session_path: Optional[str] = None,
    ) -> "AccountsTBL":
        account = cls.get_account(account_id)

        if not account:
            raise ValueError(f"Account {account_id} not found")

        account.telegram_user_id = telegram_user.id
        account.session_path = session_path or account.session_path
        account.status = "active"
        account.is_authorized = True
        account.is_active = True
        account.last_connected_at = datetime.now()
        account.last_used_at = datetime.now()
        account.save()
        return account

    @classmethod
    def set_status(
        cls,
        account_id: int,
        status: str,
    ) -> Optional["AccountsTBL"]:
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

    @classmethod
    def activate(cls, account_id: int) -> Optional["AccountsTBL"]:
        account = cls.get_account(account_id)

        if not account:
            return None

        account.is_active = True
        account.status = "offline"
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
    def update_group(
        cls,
        group_id: int,
        group_title: Optional[str] = None,
        group_link: Optional[str] = None,
        group_username: Optional[str] = None,
        group_type: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> Optional["GroupsTBL"]:
        group = cls.get_group(group_id)

        if not group:
            return None

        if group_title is not None:
            group.group_title = group_title

        if group_link is not None:
            group.group_link = group_link

        if group_username is not None:
            group.group_username = group_username

        if group_type is not None:
            group.group_type = group_type

        if is_active is not None:
            group.is_active = is_active

        group.save()
        return group

    @classmethod
    def delete_group(cls, group_id: int) -> bool:
        group = cls.get_group(group_id)

        if not group:
            return False

        return bool(group.delete_instance(recursive=True))

    @classmethod
    def get_group(cls, group_id: int) -> Optional["GroupsTBL"]:
        return cls.get_or_none(cls.group_id == group_id)

    @classmethod
    def get_groups(cls, active_only: bool = False) -> ModelSelect:
        query = cls.select().order_by(cls.created_at.desc())

        if active_only:
            query = query.where(cls.is_active == True)

        return query

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
    account = ForeignKeyField(
        AccountsTBL,
        column_name="account_id",
        backref="categories",
        on_delete="CASCADE",
    )
    name = CharField(max_length=100)

    @classmethod
    def insert_category(
        cls,
        account: AccountsTBL,
        name: str,
    ) -> "AccountCategoryTBL":
        category = cls.get_or_none(
            (cls.account == account) & (cls.name == name)
        )

        if category:
            return category

        return cls.create(account=account, name=name)

    @classmethod
    def update_category(
        cls,
        category_id: int,
        name: str,
    ) -> Optional["AccountCategoryTBL"]:
        category = cls.get_category(category_id)

        if not category:
            return None

        category.name = name
        category.save()
        return category

    @classmethod
    def delete_category(cls, category_id: int) -> bool:
        category = cls.get_category(category_id)

        if not category:
            return False

        return bool(category.delete_instance())

    @classmethod
    def get_category(
        cls,
        category_id: int,
    ) -> Optional["AccountCategoryTBL"]:
        return cls.get_or_none(cls.category_id == category_id)

    @classmethod
    def get_account_categories(cls, account_id: int) -> ModelSelect:
        return cls.select().where(cls.account == account_id)


class AccountGroupTBL(BaseModel):
    relation_id = AutoField(primary_key=True)
    account = ForeignKeyField(
        AccountsTBL,
        column_name="account_id",
        backref="group_relations",
        on_delete="CASCADE",
    )
    group = ForeignKeyField(
        GroupsTBL,
        column_name="group_id",
        backref="account_relations",
        on_delete="CASCADE",
    )
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
        relation = cls.get_relation(
            account.account_id,
            group.group_id,
        )

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
    def update_relation(
        cls,
        relation_id: int,
        status: Optional[str] = None,
        category: Optional[AccountCategoryTBL] = None,
    ) -> Optional["AccountGroupTBL"]:
        relation = cls.get_relation_by_id(relation_id)

        if not relation:
            return None

        if status is not None:
            relation.status = status

        if category is not None:
            relation.category = category

        relation.save()
        return relation

    @classmethod
    def delete_relation(cls, relation_id: int) -> bool:
        relation = cls.get_relation_by_id(relation_id)

        if not relation:
            return False

        return bool(relation.delete_instance())

    @classmethod
    def get_relation_by_id(
        cls,
        relation_id: int,
    ) -> Optional["AccountGroupTBL"]:
        return cls.get_or_none(cls.relation_id == relation_id)

    @classmethod
    def get_relation(
        cls,
        account_id: int,
        group_id: int,
    ) -> Optional["AccountGroupTBL"]:
        return cls.get_or_none(
            (cls.account == account_id) & (cls.group == group_id)
        )

    @classmethod
    def get_account_groups(
        cls,
        account_id: int,
        joined_only: bool = False,
    ) -> ModelSelect:
        query = cls.select().where(cls.account == account_id)

        if joined_only:
            query = query.where(cls.status == "joined")

        return query.order_by(cls.created_at.desc())

    @classmethod
    def get_category_groups(
        cls,
        category_id: int,
    ) -> ModelSelect:
        return cls.select().where(cls.category == category_id)

    @classmethod
    def exists(
        cls,
        account_id: int,
        group_id: int,
    ) -> bool:
        return bool(
            cls.get_or_none(
                (cls.account == account_id) & (cls.group == group_id)
            )
        )

    @classmethod
    def mark_left(
        cls,
        account_id: int,
        group_id: int,
    ) -> Optional["AccountGroupTBL"]:
        relation = cls.get_relation(account_id, group_id)

        if not relation:
            return None

        relation.status = "left"
        relation.left_at = datetime.now()
        relation.save()
        return relation


class TelegramOperationTBL(BaseModel):
    operation_id = AutoField(primary_key=True)
    actor = ForeignKeyField(
        UsersTBL,
        column_name="actor_id",
        field=UsersTBL.user_id,
        backref="operations",
        null=True,
        on_delete="SET NULL",
    )
    account = ForeignKeyField(
        AccountsTBL,
        column_name="account_id",
        backref="operations",
        on_delete="CASCADE",
    )
    operation = CharField(max_length=80, index=True)
    target_type = CharField(max_length=50, null=True)
    target_id = BigIntegerField(null=True, index=True)
    status = CharField(max_length=30, default="success", index=True)
    result = TextField(null=True)
    error = TextField(null=True)
    metadata = TextField(null=True)

    @classmethod
    def insert_operation(
        cls,
        account: AccountsTBL,
        operation: str,
        actor: Optional[UsersTBL] = None,
        status: str = "success",
        target_type: Optional[str] = None,
        target_id: Optional[int] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[str] = None,
    ) -> "TelegramOperationTBL":
        return cls.create(
            actor=actor,
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
    def log(cls, *args, **kwargs) -> "TelegramOperationTBL":
        return cls.insert_operation(*args, **kwargs)

    @classmethod
    def update_operation(
        cls,
        operation_id: int,
        status: Optional[str] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
        metadata: Optional[str] = None,
    ) -> Optional["TelegramOperationTBL"]:
        operation = cls.get_operation(operation_id)

        if not operation:
            return None

        if status is not None:
            operation.status = status

        if result is not None:
            operation.result = result

        if error is not None:
            operation.error = error

        if metadata is not None:
            operation.metadata = metadata

        operation.save()
        return operation

    @classmethod
    def delete_operation(cls, operation_id: int) -> bool:
        operation = cls.get_operation(operation_id)

        if not operation:
            return False

        return bool(operation.delete_instance())

    @classmethod
    def get_operation(
        cls,
        operation_id: int,
    ) -> Optional["TelegramOperationTBL"]:
        return cls.get_or_none(cls.operation_id == operation_id)

    @classmethod
    def get_account_operations(
        cls,
        account_id: int,
        limit: int = 100,
    ) -> ModelSelect:
        return (
            cls.select()
            .where(cls.account == account_id)
            .order_by(cls.created_at.desc())
            .limit(limit)
        )

    @classmethod
    def get_actor_operations(
        cls,
        actor_id: int,
        limit: int = 100,
    ) -> ModelSelect:
        return (
            cls.select()
            .where(cls.actor == actor_id)
            .order_by(cls.created_at.desc())
            .limit(limit)
        )

    @classmethod
    def get_operator_operations(
        cls,
        operator_id: int,
        limit: int = 100,
    ) -> ModelSelect:
        return (
            cls.select()
            .join(AccountsTBL)
            .where(AccountsTBL.admin == operator_id)
            .order_by(cls.created_at.desc())
            .limit(limit)
        )

    @classmethod
    def get_operations(cls, limit: int = 100) -> ModelSelect:
        return (
            cls.select()
            .order_by(cls.created_at.desc())
            .limit(limit)
        )

    @classmethod
    def get_errors(cls, limit: int = 100) -> ModelSelect:
        return (
            cls.select()
            .where(cls.status == "failed")
            .order_by(cls.created_at.desc())
            .limit(limit)
        )


ForwardHistoryTBL = TelegramOperationTBL


TABLES = [
    UsersTBL,
    AccountsTBL,
    GroupsTBL,
    AccountCategoryTBL,
    AccountGroupTBL,
    TelegramOperationTBL,
]
