from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.database import BaseModel


class Faq(BaseModel):
    __tablename__ = "faqs"

    question:   Mapped[str] = mapped_column(Text,    nullable=False)
    question_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer:     Mapped[str] = mapped_column(Text,    nullable=False)
    answer_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
