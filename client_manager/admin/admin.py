from client_manager.admin.admin_panel import AdminPanel
from client_manager.admin.user_manager import UserManager
from client_manager.admin.account_manager import AccountManager


class AdminCommand(
    AdminPanel,
    UserManager,
    AccountManager,
):
    pass
