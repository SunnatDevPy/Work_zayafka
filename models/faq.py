from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.database import BaseModel


class Faq(BaseModel):
    __tablename__ = "faqs"

    question:   Mapped[str] = mapped_column(Text,    nullable=False)
    answer:     Mapped[str] = mapped_column(Text,    nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
