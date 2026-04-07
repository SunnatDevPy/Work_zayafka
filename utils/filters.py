from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from config import conf


class AdminFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        uid = event.from_user.id if event.from_user else None
        return uid is not None and uid in conf.bot.admin_ids
