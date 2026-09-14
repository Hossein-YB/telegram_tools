from client_manager.admin.account_manager import AccountCommands
from client_manager.admin.admin_panel import AdminPanel
from client_manager.admin.operator_manager import OperatorManager
from client_manager.admin.sudo_manager import SudoManager
from client_manager.operator.forwarding import Forwarding


class AdminCommand(
    AdminPanel,
    OperatorManager,
    SudoManager,
    AccountCommands,
    Forwarding,
):
    pass
