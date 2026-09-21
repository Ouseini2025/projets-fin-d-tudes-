from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


EXPENSE_CATEGORIES = (
    "LOYER",
    "SALAIRES",
    "TRANSPORT",
    "ELECTRICITE",
    "INTERNET",
    "FOURNITURES",
    "MAINTENANCE",
    "MARKETING",
    "AUTRE",
)


class ExpenseCreate(BaseModel):
    category: str = Field(min_length=2, max_length=40)
    amount: Decimal = Field(gt=0)
    description: str | None = None
    expense_date: date


class ExpenseUpdate(BaseModel):
    category: str | None = Field(
        default=None,
        min_length=2,
        max_length=40,
    )
    amount: Decimal | None = Field(
        default=None,
        gt=0,
    )
    description: str | None = None
    expense_date: date | None = None


class ExpenseResponse(BaseModel):
    id: UUID
    company_id: UUID
    user_id: UUID
    category: str
    amount: Decimal
    description: str | None
    expense_date: date
    created_at: datetime

    model_config = {"from_attributes": True}