from pyrogram import enums


class Messages:
    CAN_NOT_START_BOT = "شما دسترسی استفاده از ربات را ندارید. درخواست شما برای ادمین اصلی ارسال شد."
    CANCELED_COMMAND = "عملیات لغو شد."
    START_TEXT = "سلام 👋\nاز پنل زیر می‌توانید اکانت‌های خود را مدیریت کنید."
    ADMIN_PANEL = "پنل مدیریت اکانت‌ها و عملیات"
    SUDO_PANEL = "پنل مدیریت اصلی (SUDO)"
    TIME_OUT = "زمان عملیات به پایان رسید. لطفاً دوباره تلاش کنید."
    OPERATION_ERROR = "در اجرای عملیات خطایی رخ داد. لطفاً دوباره تلاش کنید."

    FORWARD_OP_MSG = "برای اضافه کردن اوپراتور، یک پیام از کاربر مورد نظر برای من فروارد کنید."
    FORWARD_FROM_A_USER = "کاربر یافت نشد. اگر فروارد خود را بسته است، لطفاً از او بخواهید ربات را استارت کند."
    USER_SUCCESSFULLY_INSERTED = "کاربر با موفقیت به لیست اوپراتورها اضافه شد."
    BOT_OPEN_LUCK = "دسترسی ربات برای شما فعال شد."

    ACCOUNT_NAME = "یک نام برای اکانت وارد کنید."
    ACCOUNT_PHONE = "شماره اکانت تلگرام را با فرمت بین‌المللی وارد کنید."
    ACCOUNT_PASSWORD = "این اکانت تأیید دو مرحله‌ای دارد. رمز دو مرحله‌ای را وارد کنید."
    NO_ACCOUNTS = "هنوز هیچ اکانتی برای شما ثبت نشده است."

    FORWARD_PANEL = "پیام آماده ارسال است. با کدام اکانت می‌خواهید فروارد کنید؟"
    NO_GROUPS = "برای این اکانت هیچ گروهی ثبت نشده است. ابتدا گروه‌ها را دریافت کنید یا به گروه‌ها جوین شوید."
    FORWARD_STARTED = "فروارد شروع شد..."
    FORWARD_FINISHED = "فروارد تمام شد."
    FORWARD_FAILED = "فروارد با خطا تمام شد."

    @classmethod
    def generate_confirm_user_add(cls, name, user_id):
        return (
            f"کاربر [{name}](tg://user?id={user_id}) یافت شد.\n"
            f"در صورت درست بودن اطلاعات تأیید کنید."
        )

    @classmethod
    def generate_confirm_user_add_start(cls, name, user_id):
        return (
            f"کاربر [{name}](tg://user?id={user_id}) ربات را استارت کرد.\n"
            f"در صورت تأیید، او را به لیست اوپراتورها اضافه کنید."
        )

    @classmethod
    def get_code_telegram_in_app(cls, sent_code):
        descriptions = {
            enums.SentCodeType.APP: "برنامه تلگرام",
            enums.SentCodeType.SMS: "پیامک",
            enums.SentCodeType.CALL: "تماس تلفنی",
            enums.SentCodeType.FLASH_CALL: "تماس سریع",
            enums.SentCodeType.FRAGMENT_SMS: "Fragment",
            enums.SentCodeType.EMAIL_CODE: "ایمیل",
        }
        code_type = descriptions.get(sent_code.type, "تلگرام")
        return f"کد ورود به اکانت از طریق {code_type} ارسال شد. کد را وارد کنید."

    @classmethod
    def account_added(cls, account):
        return (
            f"اکانت {account.display_name} با موفقیت اضافه شد.\n"
            f"شناسه: {account.account_id}"
        )

    @classmethod
    def accounts_list(cls, accounts, manager):
        lines = ["لیست اکانت‌ها:"]

        for account in accounts:
            connected = manager.is_connected(account.account_id)
            state = "🟢 متصل" if connected else f"⚪ {account.status}"
            active = "فعال" if account.is_active else "خاموش"
            lines.append(
                f"#{account.account_id} | {account.display_name}\n"
                f"شماره: {account.phone_number}\n"
                f"وضعیت: {active} | {state}"
            )

        return "\n\n".join(lines)

    @classmethod
    def account_details(cls, account, connected: bool):
        connection = "🟢 متصل" if connected else "⚪ قطع"
        active = "🟢 فعال" if account.is_active else "🔴 غیرفعال"
        authorized = "تأیید شده" if account.is_authorized else "تأیید نشده"

        return (
            f"📱 {account.display_name}\n"
            f"شناسه: #{account.account_id}\n"
            f"شماره: {account.phone_number}\n\n"
            f"اتصال: {connection}\n"
            f"وضعیت: {account.status}\n"
            f"فعال بودن: {active}\n"
            f"مجوز تلگرام: {authorized}"
        )

    @classmethod
    def operation_report(cls, operations, title="گزارش عملیات"):
        lines = [title]

        for item in operations:
            actor_id = item.actor_id if item.actor_id else "-"
            lines.append(
                f"{item.created_at} | actor={actor_id} | "
                f"account={item.account_id} | {item.operation} | {item.status}"
            )

        return "\n".join(lines) if len(lines) > 1 else f"{title}\nموردی ثبت نشده است."
