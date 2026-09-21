from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.catalog import Product
from app.models.commerce import Credit, Sale
from app.models.expense import Expense


class DashboardRepository:

    def total_sales(
        self,
        db: Session,
        company_id: UUID,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> Decimal:
        query = select(
            func.coalesce(
                func.sum(Sale.total),
                Decimal("0.00"),
            )
        ).where(
            Sale.company_id == company_id
        )

        if date_from:
            query = query.where(
                Sale.created_at >= datetime.combine(
                    date_from,
                    datetime.min.time(),
                )
            )

        if date_to:
            query = query.where(
                Sale.created_at < datetime.combine(
                    date_to,
                    datetime.min.time(),
                )
            )

        return Decimal(db.scalar(query) or 0)

    def sales_count(
        self,
        db: Session,
        company_id: UUID,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> int:
        query = select(
            func.count(Sale.id)
        ).where(
            Sale.company_id == company_id
        )

        if date_from:
            query = query.where(
                Sale.created_at >= datetime.combine(
                    date_from,
                    datetime.min.time(),
                )
            )

        if date_to:
            query = query.where(
                Sale.created_at < datetime.combine(
                    date_to,
                    datetime.min.time(),
                )
            )

        return int(db.scalar(query) or 0)

    def total_expenses(
        self,
        db: Session,
        company_id: UUID,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> Decimal:
        query = select(
            func.coalesce(
                func.sum(Expense.amount),
                Decimal("0.00"),
            )
        ).where(
            Expense.company_id == company_id
        )

        if date_from:
            query = query.where(
                Expense.expense_date >= date_from
            )

        if date_to:
            query = query.where(
                Expense.expense_date <= date_to
            )

        return Decimal(db.scalar(query) or 0)

    def total_paid(
        self,
        db: Session,
        company_id: UUID,
    ) -> Decimal:
        query = select(
            func.coalesce(
                func.sum(Sale.amount_paid),
                Decimal("0.00"),
            )
        ).where(
            Sale.company_id == company_id
        )

        return Decimal(db.scalar(query) or 0)

    def total_receivables(
        self,
        db: Session,
        company_id: UUID,
    ) -> Decimal:
        query = select(
            func.coalesce(
                func.sum(Credit.remaining_amount),
                Decimal("0.00"),
            )
        ).where(
            Credit.company_id == company_id,
            Credit.remaining_amount > 0,
        )

        return Decimal(db.scalar(query) or 0)

    def active_credits(
        self,
        db: Session,
        company_id: UUID,
    ) -> int:
        query = select(
            func.count(Credit.id)
        ).where(
            Credit.company_id == company_id,
            Credit.remaining_amount > 0,
        )

        return int(db.scalar(query) or 0)

    def overdue_receivables(
        self,
        db: Session,
        company_id: UUID,
        today: date,
    ) -> Decimal:
        query = select(
            func.coalesce(
                func.sum(Credit.remaining_amount),
                Decimal("0.00"),
            )
        ).where(
            Credit.company_id == company_id,
            Credit.remaining_amount > 0,
            Credit.due_date.is_not(None),
            Credit.due_date < today,
        )

        return Decimal(db.scalar(query) or 0)

    def stock_value(
        self,
        db: Session,
        company_id: UUID,
    ) -> Decimal:
        query = select(
            func.coalesce(
                func.sum(
                    Product.current_stock * Product.purchase_price
                ),
                Decimal("0.00"),
            )
        ).where(
            Product.company_id == company_id
        )

        return Decimal(db.scalar(query) or 0)

    def low_stock_products(
        self,
        db: Session,
        company_id: UUID,
    ) -> int:
        query = select(
            func.count(Product.id)
        ).where(
            Product.company_id == company_id,
            Product.current_stock > 0,
            Product.current_stock <= Product.minimum_stock,
        )

        return int(db.scalar(query) or 0)

    def out_of_stock_products(
        self,
        db: Session,
        company_id: UUID,
    ) -> int:
        query = select(
            func.count(Product.id)
        ).where(
            Product.company_id == company_id,
            Product.current_stock <= 0,
        )

        return int(db.scalar(query) or 0)