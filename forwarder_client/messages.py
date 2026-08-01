class MessagesText:
    HELP = (
        "📖 راهنمای کامل ربات:\n\n"
        "🔹 ثبت پیام جدید:\n"
        "   روی پیام ریپلای کنید و `!set` را بزنید\n\n"

        "🔹 مشاهده آمار:\n"
        "   `!check` - نمایش آمار کلی\n\n"

        "🔹 لغو فروارد:\n"
        "   `!stop` - لغو فروارد پیام به گروه ها\n\n"

        "🔹 لیست پیام‌ها:\n"
        "   /list - نمایش پیام‌های فعال\n\n"
        "🔹 حذف پیام:\n"
        "   /remove [شناسه] - حذف پیام از فروارد\n\n"
        "🔹 مدیریت گروه‌ها:\n"
        "   /groups - نمایش وضعیت گروه‌ها\n"
        "   /enable [آیدی] - فعال‌سازی فروارد به گروه\n"
        "   /disable [آیدی] - غیرفعال‌سازی فروارد به گروه\n\n"
        "🔹 مدیریت بن:\n"
        "   /ban [آیدی] - بن کردن گروه\n"
        "   /unban [آیدی] - رفع بن گروه"
    )
    STOP_FORWARDING = "عملیات فروارد با موفقیت غیرفعال شد ✅"
    ERROR_NO_REPLY = "❌ لطفاً روی یک پیام ریپلای کنید و دستور /fta را بزنید."
    ALREADY_FORWARDING = "در حال حاضر یک فروارد در حال انجام است لطفا اول ان را خاموش کنید"
    GROUPS_NOT_FOUND = "گروهی برای ارسال پیام پیدا نشد"
    MESSAGE_NOT_FOUND = "هیچ پیامی برای ارسال یا فروارد وجود ندارد"

    SET_NEW_MESSAGE_SUCCESS = "پیام با موفقیت در صف قرار گرقت."

    FORWARD_SUCCESS = "ارسال موفق"
    FORWARD_FAILED = "ارسال ناموفق"

    @classmethod
    def status_text(cls, total_messages="", active_messages="", send_status="",
                    total_groups="", enabled_groups="", disabled_groups=""):
        text = f"""
        📊 آمار ربات فروارد:\n\n
        وضعیت ارسال: {send_status} 
        📝 کل پیام‌ها: {total_messages}\n
        ✅ پیام‌ فعال: {active_messages}\n
        👥 کل گروه‌ها: {total_groups}\n
        🟢 گروه‌های فعال: {enabled_groups}\n
        🔴 گروه‌های غیرفعال: {disabled_groups}
        """
        return text

    @classmethod
    def start_forward_group_count(cls, group_count: int = 0) -> str:
        return f"ارسال پیام به گروه ها شروع شد\nتعداد {group_count} گروه یافت شد"

    @classmethod
    def next_round_forward(cls, group_count):
        return f"پیام به تعداد {group_count} گروه ارسال شده بعد 20 دیقه فروارد از سر گرفته میشود"


