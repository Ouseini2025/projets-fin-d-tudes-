from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.expense import Expense


class ExpenseRepository:
    def list(
        self,
        db: Session,
        company_id: UUID,
        category: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Expense]:
        query = select(Expense).where(
            Expense.company_id == company_id
        )

        if category:
            query = query.where(Expense.category == category)

        if date_from:
            query = query.where(Expense.expense_date >= date_from)

        if date_to:
            query = query.where(Expense.expense_date <= date_to)

        query = query.order_by(
            Expense.expense_date.desc(),
            Expense.created_at.desc(),
        )

        return list(db.scalars(query).all())

    def get(
        self,
        db: Session,
        company_id: UUID,
        expense_id: UUID,
    ) -> Expense | None:
        return db.scalar(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.company_id == company_id,
            )
        )

    def create(
        self,
        db: Session,
        expense: Expense,
    ) -> Expense:
        db.add(expense)
        db.flush()
        return expense

    def delete(
        self,
        db: Session,
        expense: Expense,
    ) -> None:
        db.delete(expense)
        db.flush()