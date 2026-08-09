from client_manager.admin.admin_panel import AdminPanel
from client_manager.admin.usermanger import UserManager


class AdminCommand(
    AdminPanel,
    UserManager,
):
    pass
