import re
from typing import Optional, List


def extract_links(text: str) -> List[str]:
    url_pattern = r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/?=&%:\w.-]*'
    return re.findall(url_pattern, text)


def parse_time_to_minutes(time_str: str) -> int:
    if ':' in time_str:
        h, m = map(int, time_str.split(':'))
        return h * 60 + m
    return int(time_str)


def is_valid_group_link(link: str) -> bool:
    patterns = [
        r'https://t\.me/joinchat/[\w-]+',
        r'https://t\.me/[\w_]+',
        r't\.me/joinchat/[\w-]+'
    ]
    return any(re.match(pattern, link) for pattern in patterns)


def format_message_stats(message) -> str:
    created = message.created_at.strftime('%Y-%m-%d %H:%M')
    return (
        f"📝 شناسه: {message.id}\n"
        f"👤 فرستنده: @{message.sender_username or 'نامشخص'}\n"
        f"📅 تاریخ: {created}\n"
        f"🔄 ارسال‌ها: {message.forward_count}\n"
        f"📎 مدیا: {'✅' if message.has_media else '❌'}"
    )


def safe_parse_int(value) -> Optional[int]:
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
