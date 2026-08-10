from pyrogram import enums


class Messages:
    CAN_NOT_START_BOT = " شما نمیتوانید ربات را استارت کنید. به پشتیبانی پیام دهید."
    CANCELED_COMMAND = "عملیات با موفقیت متوقف شد"
    START_TEXT = "سلام 👋👋👋\n"
    RESUMPTION_OF_OPERATIONS = "عملیات از سر گرفته شد لطفا اطلاعات صحیح را وارد کنید"
    ADMIN_PANEL = "پنل مدیریت ربات "
    TIME_OUT = "زمان عملیات به پایان رسید لطفا دوباره تلاش کنید"

    # admin operator manger
    FORWARD_OP_MSG = "برای اضافه کردن اوپراتور یک پیام از کاربر مورد نظر برای من فروارد کنید"
    FORWARD_FROM_A_USER = "کاربر یافت نشد\nاگر فروارد خود را بسته است لطفا از او بخواهید ربات را استارت کند"
    USER_SUCCESSFULLY_INSERTED = "کاربر با موفقیت. به لیست اوپراتور های ربات اضافه شد"
    BOT_OPEN_LUCK = "قفل ربات برای شما باز شد"

    @classmethod
    def generate_confirm_user_add(cls, name, user_id):
        return (
            f"کاربر [{name}](tg://user?id={user_id}) یافت شد\n"
            f"درصورت درست بودن اطلاعات تایید کنید"
        )

    @classmethod
    def generate_confirm_user_add_start(cls, name, user_id):
        return (
            f"info:{name}:{user_id}\n\n"
            f"کاربر [{name}](tg://user?id={user_id}) ربات را استارت کرد\n"
            f"درصورت تایید برای اضافه کردن کابری برای استفاده ربات از دکمه زیر استفاده کنید"
        )

    @classmethod
    def get_code_telegram_in_app(cls, sent_code):
        descriptions = {
            enums.SentCodeType.APP: "برنامه تلگرام",
            enums.SentCodeType.SMS: "پیامک",
            enums.SentCodeType.CALL: "تماس تلفنی",
            enums.SentCodeType.FLASH_CALL: "phone flash call",
            enums.SentCodeType.FRAGMENT_SMS: "Fragment",
            enums.SentCodeType.EMAIL_CODE: "ایمیل"
        }
