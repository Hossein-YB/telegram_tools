from pyrogram.enums import ButtonStyle
from pyrogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,\
    InlineKeyboardButton, InlineKeyboardMarkup


class Keyboards:
    # public keyboards
    OK_TXT = "تایید✅"
    CANCEL_TXT = "لغو ❌"

    @classmethod
    def generate_cancel_key(cls):
        return ReplyKeyboardMarkup([
            [KeyboardButton(text=cls.CANCEL_TXT, style=ButtonStyle.DANGER)],
        ], resize_keyboard=True)

    @classmethod
    def generate_confirm_ok_cancel_key(cls):
        return ReplyKeyboardMarkup([
            [KeyboardButton(text=cls.OK_TXT, style=ButtonStyle.SUCCESS)],
            [KeyboardButton(text=cls.CANCEL_TXT, style=ButtonStyle.DANGER)],
        ], resize_keyboard=True)

    @classmethod
    def generate_remove_keyboard(cls):
        return ReplyKeyboardRemove()

    # admin keyboards
    SHOW_USERS_TXT = "کاربران"
    SHOW_USERS_CALL = "a_sh_users"

    ADD_NEW_OPERATOR_TXT = "اضافه کردن کاربر"
    ADD_NEW_OPERATOR_CALL = "a_ad_user"

    SHOW_ACCOUNTS_TXT = "اکانت ها"
    SHOW_ACCOUNTS_CALL = "a_sh_account"

    ADD_NEW_ACCOUNT_TXT = "اضافه کردن اکانت"
    ADD_NEW_ACCOUNT_CALL = "a_ad_account"

    SHOW_GROUPS_TXT = "گروه ها"
    SHOW_GROUPS_CALL = "a_groups"

    @classmethod
    def generate_admin_keyboards(cls):
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(text=cls.ADD_NEW_OPERATOR_TXT, callback_data=cls.ADD_NEW_OPERATOR_CALL),
                InlineKeyboardButton(text=cls.SHOW_USERS_TXT, callback_data=cls.SHOW_USERS_CALL)
            ],
            [
                InlineKeyboardButton(text=cls.ADD_NEW_ACCOUNT_TXT, callback_data=cls.ADD_NEW_ACCOUNT_CALL),
                InlineKeyboardButton(text=cls.SHOW_ACCOUNTS_TXT, callback_data=cls.SHOW_ACCOUNTS_CALL)
            ],
            [
                InlineKeyboardButton(text=cls.SHOW_GROUPS_TXT, callback_data=cls.SHOW_GROUPS_CALL)
            ],
        ])


