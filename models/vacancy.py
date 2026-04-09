from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.database import BaseModel

if TYPE_CHECKING:
    from models.question import Question


class Vacancy(BaseModel):
    __tablename__ = "vacancies"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    title_ru: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title_uz: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    description_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    test_task_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_task_text_ru: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_task_text_uz: Mapped[str | None] = mapped_column(Text, nullable=True)
    test_task_file_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    test_task_file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="vacancy",
        cascade="all, delete-orphan",
    )
