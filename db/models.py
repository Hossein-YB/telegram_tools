from datetime import datetime
from typing import List, Optional
from peewee import (Model, BooleanField, BigIntegerField, CharField, TextField, ForeignKeyField,
                    DateField, DateTimeField, AutoField, DoesNotExist)
from playhouse.shortcuts import ReconnectMixin
from playhouse.pool import PooledMySQLDatabase

from exceptions import UserIsSudo
from utils.logger import get_logger
from config import DB_NAME, DB_USER, DB_USER_PASS, DB_PORT


class ReconnectMySQLDatabase(ReconnectMixin, PooledMySQLDatabase):
    pass


logger = get_logger(__name__)
database = ReconnectMySQLDatabase(database=DB_NAME, user=DB_USER, passwd=DB_USER_PASS,
                                  port=DB_PORT, charset='utf8mb4')


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
            return cls.create(user_id=user_id, name=name, is_sudo=is_sudo)
        except Exception as e:
            logger.error(f"insert_user failed for {user_id}: {e}")
            raise

    @classmethod
    def change_status(cls, user_id: int) -> "UsersTBL":
        try:
            u = cls.get_or_none(UsersTBL.user_id == user_id)
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
    def get_admins(cls) -> List["UsersTBL"]:
        try:
            return cls.select()
        except Exception as e:
            logger.error(f"get_admins failed: {e}")
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
        if cls.get_or_none(cls.user_id == user_id, cls.is_active == True):
            return True
        else:
            return False

    @classmethod
    def check_is_sudo(cls, user_id: int) -> bool:
        if cls.get_or_none(cls.user_id == user_id, cls.is_sudo == True):
            return True
        else:
            return False
