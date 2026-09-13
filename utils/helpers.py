"""
Umumiy yordamchi funksiyalar.
"""
from datetime import datetime, timezone

from config import ONLINE_THRESHOLD_MINUTES
from database.models import User


def _minutes_since(last_activity: datetime) -> int:
    now = datetime.now(timezone.utc)
    last = last_activity
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    delta = now - last
    return max(0, int(delta.total_seconds() // 60))


def format_elapsed(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} daqiqa"
    hours = minutes // 60
    if hours < 24:
        return f"{hours} soat"
    days = hours // 24
    return f"{days} kun"


def build_partner_status_text(partner: User) -> str:
    minutes = _minutes_since(partner.last_activity)
    if minutes < ONLINE_THRESHOLD_MINUTES:
        return "🟢 Juftingiz online"
    return f"🔴 Juftingiz offline\nOxirgi faollik: {format_elapsed(minutes)} oldin"


def detect_message_type(message) -> str:
    if message.text:
        return "text"
    if message.photo:
        return "photo"
    if message.video:
        return "video"
    if message.voice:
        return "voice"
    if message.audio:
        return "audio"
    if message.video_note:
        return "video_note"
    if message.sticker:
        return "sticker"
    if message.document:
        return "document"
    if message.animation:
        return "animation"
    return "other"
