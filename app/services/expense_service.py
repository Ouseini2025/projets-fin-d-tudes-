from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.repositories.expense_repository import ExpenseRepository


class ExpenseError(Exception):
    pass


class ExpenseService:
    def __init__(self):
        self.repository = ExpenseRepository()

    def list(
        self,
        db: Session,
        user,
        category: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[Expense]:
        if date_from and date_to and date_from > date_to:
            raise ExpenseError(
                "La date de début doit être antérieure ou égale à la date de fin."
            )

        return self.repository.list(
            db,
            company_id=user.company_id,
            category=category,
            date_from=date_from,
            date_to=date_to,
        )

    def get(
        self,
        db: Session,
        user,
        expense_id: UUID,
    ) -> Expense:
        expense = self.repository.get(
            db,
            company_id=user.company_id,
            expense_id=expense_id,
        )

        if not expense:
            raise ExpenseError(
                "Dépense introuvable dans votre entreprise."
            )

        return expense

    def create(
        self,
        db: Session,
        user,
        data,
    ) -> Expense:
        expense = Expense(
            company_id=user.company_id,
            user_id=user.id,
            category=data.category,
            amount=data.amount,
            description=data.description,
            expense_date=data.expense_date,
        )

        return self.repository.create(db, expense)

    def update(
        self,
        db: Session,
        user,
        expense_id: UUID,
        data,
    ) -> Expense:
        expense = self.get(
            db,
            user,
            expense_id,
        )

        values = data.model_dump(exclude_unset=True)

        for field, value in values.items():
            setattr(expense, field, value)

        db.flush()

        return expense

    def delete(
        self,
        db: Session,
        user,
        expense_id: UUID,
    ) -> None:
        expense = self.get(
            db,
            user,
            expense_id,
        )

        self.repository.delete(db, expense)