from decimal import Decimal

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_sales: Decimal
    total_expenses: Decimal
    net_result: Decimal

    sales_count: int
    average_sale: Decimal

    total_paid: Decimal
    total_receivables: Decimal
    overdue_receivables: Decimal

    active_credits: int

    stock_value: Decimal
    low_stock_products: int
    out_of_stock_products: int