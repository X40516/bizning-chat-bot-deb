"""
Bizning Chat Bot - sevishgan juftliklar uchun maxsus chat va media kutubxonasi.
Asosiy ishga tushirish fayli.
"""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from database.database import init_db
from handlers import admin, chat, content, couple, start
from middlewares.db import DBSessionMiddleware
from middlewares.user import UserMiddleware

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    await init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.update.outer_middleware.register(DBSessionMiddleware())
    dp.update.outer_middleware.register(UserMiddleware())

    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(couple.router)
    dp.include_router(chat.router)
    dp.include_router(content.router)

    await bot.delete_webhook(drop_pending_updates=True)
    me = await bot.get_me()
    logger.info("Bot ishga tushdi: @%s", me.username)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
