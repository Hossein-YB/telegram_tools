from functools import wraps
from db.models import UsersTBL


def admin_required(func):
    @wraps(func)
    async def wrapper(self, clt, msg, *args, **kwargs):
        if UsersTBL.check_is_admin(msg.from_user.id):
            return await func(self, clt, msg, *args, **kwargs)
        else:
            return await clt.access_denied(msg)

    return wrapper


def sudo_required(func):
    @wraps(func)
    async def wrapper(self, clt, msg, *args, **kwargs):
        if UsersTBL.check_is_sudo(msg.from_user.id):
            return await func(self, clt, msg, *args, **kwargs)
        else:
            return

    return wrapper
