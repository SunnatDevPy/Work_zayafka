from sqlalchemy import select

from locales.messages import LANG_UZ, norm_lang
from models.bot_user import BotUser
from models.database import db


async def get_user_locale(telegram_id: int) -> str | None:
    r = await db.execute(select(BotUser.locale).where(BotUser.telegram_id == telegram_id))
    loc = r.scalar_one_or_none()
    return loc


async def set_user_locale(telegram_id: int, locale: str) -> None:
    locale = norm_lang(locale)
    r = await db.execute(select(BotUser).where(BotUser.telegram_id == telegram_id))
    row = r.scalar_one_or_none()
    if row is None:
        return
    await BotUser.update(row.id, locale=locale)


async def ensure_bot_user(telegram_id: int, username: str | None, first_name: str | None) -> BotUser:
    r = await db.execute(select(BotUser).where(BotUser.telegram_id == telegram_id))
    row = r.scalar_one_or_none()
    if row:
        return row
    return await BotUser.create(
        telegram_id=telegram_id,
        username=username,
        first_name=first_name,
        locale=None,
    )
