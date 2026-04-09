from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.database import BaseModel

if TYPE_CHECKING:
    from models.vacancy import Vacancy


class Question(BaseModel):
    __tablename__ = "questions"

    vacancy_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("vacancies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    require_photo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    vacancy: Mapped["Vacancy"] = relationship("Vacancy", back_populates="questions")
