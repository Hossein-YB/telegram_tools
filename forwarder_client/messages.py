from typing import List

from pyrogram.types import Chat


class MessagesText:

    HELP = (
        "📖 راهنمای کامل ربات: `!help`\n\n"
        "🔹 لیست گروه ها:\n"
        "   `!group` - نمایش ایدی و نام گروه ها\n\n"

        "🔹 ارسال پیام یک بار برای تمام گروه ها:\n"
        "   `!fta` - روی پیام مورد نظر ریپلای کنید و این دستور رو ارسال کنید\n\n"

        "🔹 ثبت پیام جدید:\n"
        "   `!set` - تنظیم پیام برای ارسال همگانی \n\n"

        "🔹 فوروارد در گروه ها:\n"
        "   `!start `[num] - فروارد در گروه ها اگر بعد دستور یک عدد بزارید به اون تعداد در بازه زمانی پیام فروارد خواهد شد.\n\n"
        
        "🔹 لغو فروارد:\n"
        "   `!stop` - لغو فروارد پیام به گروه ها\n\n"

        "🔹 تغییر تایم بین فروارد ها:\n"
        "   `!time `[num] - بعد دستور یک فاصله قرار دهید و یه عدد به دقیقه وارد کنید\n\n"

        "🔹 عضو شدن در یک لینک:\n"
        "   `!join `[link] -  بعد دستور  یک فاصله گذاشته و لینک رو وارد کنید سپس ارسال کنید\n\n"
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
    def next_round_forward(cls, group_count, time):
        return f"پیام به تعداد {group_count} گروه ارسال شده بعد {time} دقیقه فروارد از سر گرفته میشود"

    @classmethod
    def get_group_list(cls, groups: List[Chat]) -> str:
        t = "لیست گروه های موجود در ربات نام ایدی:\n"
        t += f"تعدا کل گروه ها {len(groups)}\n"
        for group in groups:
            t+= f"{group.title} -> {group.id}\n"

        return t

    @classmethod
    def set_wait_time_between_forward(cls, num: int):
        return f"فاصله بین فروارد ها {num} خواهد بود با تشکر به ثانیه از حسن انتخاب شما:) "

    @classmethod
    def forward_success_count(cls, count):
        return f"فروارد به {count} گروه با موفقیت انجام شد "

    @classmethod
    def error_to_forward_in_group(cls, group_id, error_text):
        return f"فروارد به گروه {group_id} با مشکل مواجه شد متن ارور {error_text} "

    @classmethod
    def join_chat_success(cls, title, chat_id):
        return f"بات با موفقیت در {title} عضو شد ایدی گروه {chat_id}"