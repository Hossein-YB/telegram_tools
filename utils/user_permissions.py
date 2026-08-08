from functools import wraps
from db.models import UsersTBL


def admin_required(func):
    @wraps(func)
    async def wrapper(clt, msg, *args, **kwargs):
        if UsersTBL.get_or_none(UsersTBL.user_id == msg.from_user.id, UsersTBL.is_active == True):
            return await func(clt, msg, *args, **kwargs)
        else:
            return await clt.access_denied(msg)

    return wrapper


def sudo_required(func):
    @wraps(func)
    async def wrapper(clt, msg, *args, **kwargs):
        if UsersTBL.get_or_none(UsersTBL.user_id == msg.from_user.id, UsersTBL.is_active == True, UsersTBL.is_sudo == True):
            return await func(clt, msg, *args, **kwargs)
        else:
            return

    return wrapper
