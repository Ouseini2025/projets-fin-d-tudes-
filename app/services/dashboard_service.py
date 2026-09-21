from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import DashboardSummary


class DashboardError(Exception):
    pass


class DashboardService:

    def __init__(self):
        self.repository = DashboardRepository()

    def _money(self, value: Decimal) -> Decimal:
        return value.quantize(Decimal("0.01"))

    def get_summary(
        self,
        db: Session,
        user,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> DashboardSummary:

        if date_from and date_to and date_from > date_to:
            raise DashboardError(
                "La date de début doit être antérieure ou égale à la date de fin."
            )

        company_id = user.company_id

        # Pour les ventes, la date de fin est exclusive.
        # On ajoute donc un jour afin d'inclure toute la journée demandée.
        sales_date_to = (
            date_to + timedelta(days=1)
            if date_to
            else None
        )

        total_sales = self._money(
            self.repository.total_sales(
                db,
                company_id,
                date_from=date_from,
                date_to=sales_date_to,
            )
        )

        total_expenses = self._money(
            self.repository.total_expenses(
                db,
                company_id,
                date_from=date_from,
                date_to=date_to,
            )
        )

        sales_count = self.repository.sales_count(
            db,
            company_id,
            date_from=date_from,
            date_to=sales_date_to,
        )

        total_paid = self._money(
            self.repository.total_paid(
                db,
                company_id,
            )
        )

        total_receivables = self._money(
            self.repository.total_receivables(
                db,
                company_id,
            )
        )

        overdue_receivables = self._money(
            self.repository.overdue_receivables(
                db,
                company_id,
                today=date.today(),
            )
        )

        active_credits = self.repository.active_credits(
            db,
            company_id,
        )

        stock_value = self._money(
            self.repository.stock_value(
                db,
                company_id,
            )
        )

        low_stock_products = self.repository.low_stock_products(
            db,
            company_id,
        )

        out_of_stock_products = self.repository.out_of_stock_products(
            db,
            company_id,
        )

        average_sale = (
            self._money(total_sales / sales_count)
            if sales_count > 0
            else Decimal("0.00")
        )

        net_result = self._money(
            total_sales - total_expenses
        )

        return DashboardSummary(
            total_sales=total_sales,
            total_expenses=total_expenses,
            net_result=net_result,
            sales_count=sales_count,
            average_sale=average_sale,
            total_paid=total_paid,
            total_receivables=total_receivables,
            overdue_receivables=overdue_receivables,
            active_credits=active_credits,
            stock_value=stock_value,
            low_stock_products=low_stock_products,
            out_of_stock_products=out_of_stock_products,
        )