import logging

from config import conf
from models import BotUser, Faq, Question, Vacancy  # noqa: F401
from models.database import db

from app.factory import create_bot, create_dispatcher, include_routers, setup_commands


async def run_polling() -> None:
    logging.basicConfig(level=logging.INFO)
    if not conf.bot.token:
        raise SystemExit(".env faylida BOT_TOKEN ni ko‘rsating")

    await db.create_all()

    bot = create_bot(conf.bot.token)
    dp = create_dispatcher()
    include_routers(dp)
    await setup_commands(bot)
    await dp.start_polling(bot)

