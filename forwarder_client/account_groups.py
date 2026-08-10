from typing import TYPE_CHECKING
from db.models import GroupsTBL, AccountGroupTBL
from pyrogram.types import Message

if TYPE_CHECKING:
    from client_manager.base import ClientManger


class AccountGroups:

    async def group(self):
        pass