from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, FLOAT, Date
from datetime import date, datetime


class Base(DeclarativeBase):
    pass


class Users(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(Integer, unique=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    height: Mapped[int] = mapped_column(Integer, nullable=True, default=None)
    weight: Mapped[float] = mapped_column(FLOAT, nullable=True, default=None)
    gender: Mapped[str] = mapped_column(String(255), nullable=True, default=None)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[str] = mapped_column(String, default=datetime.utcnow().isoformat())
