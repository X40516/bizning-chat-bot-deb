"""
Foydalanuvchini DBga yozib/topib beruvchi va oxirgi faollikni yangilovchi middleware.
"""
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from database.queries import get_or_create_user, touch_last_activity


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        tg_user = data.get("event_from_user")
        if tg_user is None:
            return await handler(event, data)

        session = data["session"]
        db_user = await get_or_create_user(
            session,
            telegram_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name or "",
        )
        await touch_last_activity(session, db_user.id)
        data["db_user"] = db_user

        return await handler(event, data)
