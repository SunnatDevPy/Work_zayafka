from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from handlers import admin, admin_broadcast, channel_review, user


def create_bot(token: str) -> Bot:
    return Bot(token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def create_dispatcher() -> Dispatcher:
    return Dispatcher(storage=MemoryStorage())


def include_routers(dp: Dispatcher) -> None:
    dp.include_router(channel_review.router)
    dp.include_router(admin.router)
    dp.include_router(admin_broadcast.router)
    dp.include_router(user.router)


async def setup_commands(bot: Bot) -> None:
    await bot.set_my_commands([
        BotCommand(command="start", description="Ishga tushirish / Запуск"),
        BotCommand(command="lang", description="Til / Язык"),
    ])
