from typing import Optional

from conversation.client import CustomClient
from services.account_manager import AccountManager
from db.models import UsersTBL

from .admin.admin import AdminCommand
from .handlers.handler import Handlers
from .message.Messages import Messages
from .message.keyboards import Keyboards
from .public_method import PublicMethods


class ClientManager(
    AdminCommand,
    PublicMethods,
    Handlers,
    CustomClient,
):
    def __init__(
        self,
        name,
        api_id,
        api_hash,
        bot_token,
        **kwargs,
    ):
        self.texts = Messages()
        self.keys = Keyboards()
        self.timeout_second = 60
        self.account_managers: dict[int, AccountManager] = {}
        self.forward_sessions: dict[tuple[int, int], dict] = {}

        super().__init__(
            name=name,
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token,
            **kwargs,
        )

    def start(self):
        # Restore account/client objects before the bot starts handling
        # callbacks. Clients are created disconnected; Telegram connections
        # are opened only when an operator explicitly connects/uses an account.
        self.restore_account_managers()
        self.set_handlers()
        return super().start()

    def restore_account_managers(self) -> None:
        """Rebuild all operator AccountManager instances after a restart."""
        self.account_managers.clear()

        for user in UsersTBL.get_users(active_only=False):
            if user.is_sudo or not user.is_active:
                continue

            try:
                self.get_account_manager(
                    operator_id=user.user_id,
                    actor_id=user.user_id,
                )
            except ValueError:
                # A stale/incomplete operator row should not prevent the
                # management bot itself from starting.
                continue

    @staticmethod
    def is_sudo(user_id: int) -> bool:
        from db.models import UsersTBL

        return UsersTBL.check_is_sudo(user_id)


ClientManger = ClientManager
