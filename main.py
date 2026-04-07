import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import conf
from handlers import admin, ai_chat, channel_review, faq, user
from models import BotUser, Faq, Question, Vacancy  # noqa: F401 — регистрация таблиц
from models.database import db


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    if not conf.bot.token:
        raise SystemExit(".env faylida BOT_TOKEN ni ko‘rsating")

    await db.create_all()

    bot = Bot(conf.bot.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(channel_review.router)
    dp.include_router(admin.router)
    dp.include_router(ai_chat.router)
    dp.include_router(faq.router)
    dp.include_router(user.router)

    await bot.set_my_commands([
        BotCommand(command="start", description="Botni ishga tushirish"),
    ])

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
