import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Expense(Base):
    __tablename__ = "expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id"),
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(40),
        index=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
    )

    description: Mapped[str | None] = mapped_column(
        Text,
    )

    expense_date: Mapped[date] = mapped_column(
        Date,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
    )