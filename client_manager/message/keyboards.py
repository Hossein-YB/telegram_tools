from pyrogram.enums import ButtonStyle
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)


class Keyboards:
    OK_TXT = "تایید✅"
    CANCEL_TXT = "لغو ❌"

    SHOW_USERS_TXT = "کاربران"
    SHOW_USERS_CALL = "a_sh_users"

    SHOW_ACCOUNTS_TXT = "اکانت ها"
    SHOW_ACCOUNTS_CALL = "a_sh_account"

    ADD_NEW_ACCOUNT_TXT = "اضافه کردن اکانت"
    ADD_NEW_ACCOUNT_CALL = "a_ad_account"

    SHOW_GROUPS_TXT = "گروه ها"
    SHOW_GROUPS_CALL = "a_groups"

    SHOW_HISTORY_TXT = "تاریخچه"
    SHOW_HISTORY_CALL = "a_history"

    SUDO_PANEL_TXT = "پنل سودو"
    SUDO_PANEL_CALL = "s_panel"

    REPORTS_TXT = "گزارش کلی"
    REPORTS_CALL = "s_reports"

    OPERATOR_REPORTS_TXT = "گزارش اوپراتورها"
    OPERATOR_REPORTS_CALL = "s_operator_reports"

    CONNECTED_ACCOUNTS_TXT = "اکانت های متصل"
    CONNECTED_ACCOUNTS_CALL = "s_connected"

    ADD_NEW_OPERATOR_TXT = "اضافه کردن کاربر"
    ADD_NEW_OPERATOR_CALL = "s_add_operator"

    BACK_TXT = "بازگشت ↩️"
    BACK_CALL = "back:admin"

    ACCOUNT_ENABLE_TXT = "فعال کردن"
    ACCOUNT_DISABLE_TXT = "غیرفعال کردن"
    ACCOUNT_CONNECT_TXT = "اتصال 🔌"
    ACCOUNT_DISCONNECT_TXT = "قطع اتصال ⛔"
    ACCOUNT_REPORT_TXT = "گزارش اکانت"
    ACCOUNT_RETRY_TXT = "تلاش مجدد ورود"
    ACCOUNT_DELETE_TXT = "حذف اکانت"

    ADD_ADMIN_FROM_START_TXT = "اضافه کردن به لیست اوپراتورها"
    ADD_ADMIN_FROM_START_CALL = "a_add_op_st"

    FORWARD_ALL_TXT = "همه گروه ها"
    FORWARD_SEND_TXT = "فروارد 🚀"

    JOIN_GROUP_TXT = "➕ جوین با لینک"
    REFRESH_GROUPS_TXT = "🔄 بروزرسانی لیست"

    @classmethod
    def generate_cancel_key(cls):
        return ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton(
                        text=cls.CANCEL_TXT,
                        style=ButtonStyle.DANGER,
                    ),
                ],
            ],
            resize_keyboard=True,
        )

    @classmethod
    def generate_confirm_ok_cancel_key(cls):
        return ReplyKeyboardMarkup(
            [
                [
                    KeyboardButton(
                        text=cls.OK_TXT,
                        style=ButtonStyle.SUCCESS,
                    ),
                ],
                [
                    KeyboardButton(
                        text=cls.CANCEL_TXT,
                        style=ButtonStyle.DANGER,
                    ),
                ],
            ],
            resize_keyboard=True,
        )

    @classmethod
    def generate_remove_keyboard(cls):
        return ReplyKeyboardRemove()

    @classmethod
    def generate_admin_keyboards(cls, is_sudo: bool = False):
        rows = [
            [
                InlineKeyboardButton(
                    text=cls.ADD_NEW_ACCOUNT_TXT,
                    callback_data=cls.ADD_NEW_ACCOUNT_CALL,
                ),
                InlineKeyboardButton(
                    text=cls.SHOW_ACCOUNTS_TXT,
                    callback_data=cls.SHOW_ACCOUNTS_CALL,
                ),
            ],
            [
                InlineKeyboardButton(
                    text=cls.SHOW_GROUPS_TXT,
                    callback_data=cls.SHOW_GROUPS_CALL,
                ),
                InlineKeyboardButton(
                    text=cls.SHOW_HISTORY_TXT,
                    callback_data=cls.SHOW_HISTORY_CALL,
                ),
            ],
        ]

        if is_sudo:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=cls.SUDO_PANEL_TXT,
                        callback_data=cls.SUDO_PANEL_CALL,
                    ),
                ]
            )

        return InlineKeyboardMarkup(rows)

    @classmethod
    def generate_sudo_panel(cls):
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=cls.REPORTS_TXT,
                        callback_data=cls.REPORTS_CALL,
                    ),
                    InlineKeyboardButton(
                        text=cls.OPERATOR_REPORTS_TXT,
                        callback_data=cls.OPERATOR_REPORTS_CALL,
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text=cls.CONNECTED_ACCOUNTS_TXT,
                        callback_data=cls.CONNECTED_ACCOUNTS_CALL,
                    ),
                    InlineKeyboardButton(
                        text=cls.ADD_NEW_OPERATOR_TXT,
                        callback_data=cls.ADD_NEW_OPERATOR_CALL,
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text=cls.SHOW_USERS_TXT,
                        callback_data=cls.SHOW_USERS_CALL,
                    ),
                    InlineKeyboardButton(
                        text=cls.SHOW_HISTORY_TXT,
                        callback_data=cls.SHOW_HISTORY_CALL,
                    ),
                ],
            ]
        )

    @classmethod
    def generate_accounts_keyboard(cls, accounts, manager=None):
        rows = []

        for account in accounts:
            active = "🟢" if account.is_active else "🔴"
            authorized = "✓" if account.is_authorized else "!"
            connected = (
                bool(manager and manager.is_connected(account.account_id))
            )
            connection = "🟢" if connected else "⚪"

            # Keep buttons compact so long account names do not make the list
            # unreadable. Full information remains on the details screen.
            rows.append(
                [
                    InlineKeyboardButton(
                        text=(
                            f"{active} {connection} "
                            f"{account.display_name} · #{account.account_id} "
                            f"[{authorized}]"
                        ),
                        callback_data=f"acct:{account.account_id}",
                    ),
                ]
            )

        rows.extend(
            [
                [
                    InlineKeyboardButton(
                        text=f"➕ {cls.ADD_NEW_ACCOUNT_TXT}",
                        callback_data=cls.ADD_NEW_ACCOUNT_CALL,
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=cls.BACK_TXT,
                        callback_data=cls.BACK_CALL,
                    )
                ],
            ]
        )

        return InlineKeyboardMarkup(rows)

    @classmethod
    def generate_account_actions(cls, account, connected: bool = False):
        toggle_text = (
            cls.ACCOUNT_DISABLE_TXT
            if account.is_active
            else cls.ACCOUNT_ENABLE_TXT
        )
        toggle_call = (
            f"acct:disable:{account.account_id}"
            if account.is_active
            else f"acct:enable:{account.account_id}"
        )
        rows = []

        if account.is_authorized and account.is_active:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=(
                            cls.ACCOUNT_DISCONNECT_TXT
                            if connected
                            else cls.ACCOUNT_CONNECT_TXT
                        ),
                        callback_data=(
                            f"acct:disconnect:{account.account_id}"
                            if connected
                            else f"acct:connect:{account.account_id}"
                        ),
                    )
                ]
            )

        rows.append(
            [
                InlineKeyboardButton(
                    text=toggle_text,
                    callback_data=toggle_call,
                ),
                InlineKeyboardButton(
                    text=cls.ACCOUNT_REPORT_TXT,
                    callback_data=f"acct:report:{account.account_id}",
                ),
            ],
        )

        if not account.is_authorized or account.status in {
            "failed",
            "pending",
            "waiting_code",
        }:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=cls.ACCOUNT_RETRY_TXT,
                        callback_data=f"acct:retry:{account.account_id}",
                    ),
                ]
            )

        rows.append(
            [
                InlineKeyboardButton(
                    text=cls.ACCOUNT_DELETE_TXT,
                    callback_data=f"acct:delete:{account.account_id}",
                ),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=cls.BACK_TXT,
                    callback_data=cls.BACK_CALL,
                ),
            ]
        )

        return InlineKeyboardMarkup(rows)

    @classmethod
    def generate_forward_accounts(cls, accounts, message_id: int):
        rows = []

        for account in accounts:
            if not account.is_active or not account.is_authorized:
                continue

            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"📱 {account.display_name} · #{account.account_id}",
                        callback_data=f"fwd:a:{message_id}:{account.account_id}",
                    )
                ]
            )

        return InlineKeyboardMarkup(rows or [[
            InlineKeyboardButton(
                text=cls.BACK_TXT,
                callback_data=cls.BACK_CALL,
            )
        ]])

    @classmethod
    def generate_forward_groups(
        cls,
        message_id: int,
        account_id: int,
        groups,
        selected_ids: set[int],
    ):
        rows = []
        all_selected = bool(groups) and len(selected_ids) == len(groups)

        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{'☑️' if all_selected else '⬜'} {cls.FORWARD_ALL_TXT}",
                    callback_data=f"fwd:all:{message_id}:{account_id}",
                ),
            ]
        )

        for relation in groups:
            group = relation.group
            selected = group.group_id in selected_ids
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"{'☑️' if selected else '⬜'} {group.group_title[:28]}",
                        callback_data=(
                            f"fwd:g:{message_id}:{account_id}:{group.group_id}"
                        ),
                    ),
                ]
            )

        rows.append(
            [
                InlineKeyboardButton(
                    text=cls.FORWARD_SEND_TXT,
                    callback_data=f"fwd:send:{message_id}:{account_id}",
                ),
            ]
        )
        rows.append(
            [
                InlineKeyboardButton(
                    text=cls.BACK_TXT,
                    callback_data=f"fwd:back:{message_id}",
                ),
            ]
        )

        return InlineKeyboardMarkup(rows)

    @classmethod
    def generate_group_accounts_keyboard(cls, accounts):
        rows = []

        for account in accounts:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"📱 {account.display_name} · #{account.account_id}",
                        callback_data=f"grp:{account.account_id}",
                    )
                ]
            )

        rows.append(
            [
                InlineKeyboardButton(
                    text=cls.BACK_TXT,
                    callback_data=cls.BACK_CALL,
                )
            ]
        )

        return InlineKeyboardMarkup(rows)

    @classmethod
    def generate_account_groups_keyboard(cls, account_id: int):
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=cls.JOIN_GROUP_TXT,
                        callback_data=f"grp:join:{account_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text=cls.REFRESH_GROUPS_TXT,
                        callback_data=f"grp:refresh:{account_id}",
                    ),
                ],
                [
                    InlineKeyboardButton(
                        text=cls.BACK_TXT,
                        callback_data=cls.SHOW_GROUPS_CALL,
                    ),
                ],
            ]
        )

    @classmethod
    def generate_operator_list(cls, users):
        rows = []

        for user in users:
            if user.is_sudo:
                continue

            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"👤 {user.name} · #{user.user_id}",
                        callback_data=f"s:operator:{user.user_id}",
                    )
                ]
            )

        return InlineKeyboardMarkup(rows or [[
            InlineKeyboardButton(
                text=cls.BACK_TXT,
                callback_data=cls.BACK_CALL,
            )
        ]])

    @classmethod
    def generate_add_new_admin_from_start_keyboard(cls, user_id: int):
        return InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=cls.ADD_ADMIN_FROM_START_TXT,
                        callback_data=f"{cls.ADD_ADMIN_FROM_START_CALL}:{user_id}",
                    ),
                ],
            ]
        )
