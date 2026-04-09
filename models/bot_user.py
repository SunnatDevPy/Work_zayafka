from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from models.database import BaseModel


class BotUser(BaseModel):
    """Пользователи бота — для рассылки рекламы."""

    __tablename__ = "bot_users"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # ru | uz; NULL — язык ещё не выбран при /start
    locale: Mapped[str | None] = mapped_column(String(8), nullable=True)
