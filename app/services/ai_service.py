import uuid
from datetime import datetime, timedelta, date
from typing import List, Tuple

from sqlalchemy import func, select, desc
from sqlalchemy.orm import Session

from app.models.catalog import Product
from app.models.commerce import Sale, SaleItem
from app.models.stock import StockMovement
from app.schemas.ai import AiInsightResponse, StockForecastResponse, TopProduct, LowRotationProduct

class AIService:
    """Service generating deterministic AI insights for a company.
    All calculations are based on existing business data and use only the
    Python standard library + SQLAlchemy.
    """

    # ---------- Helper ----------
    def _current_month_range(self) -> Tuple[datetime, datetime]:
        now = datetime.utcnow()
        start = datetime(now.year, now.month, 1)
        # first day of next month
        if now.month == 12:
            end = datetime(now.year + 1, 1, 1)
        else:
            end = datetime(now.year, now.month + 1, 1)
        return start, end

    # ---------- Top products ----------
    def get_top_products(self, db: Session, company_id: uuid.UUID, limit: int = 10) -> List[TopProduct]:
        start, end = self._current_month_range()
        stmt = (
            select(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                func.sum(SaleItem.quantity).label("quantity"),
            )
            .join(SaleItem.product)
            .join(SaleItem.sale)
            .where(Sale.company_id == company_id, Sale.created_at >= start, Sale.created_at < end)
            .group_by(Product.id)
            .order_by(desc("quantity"))
            .limit(limit)
        )
        rows = db.execute(stmt).all()
        return [TopProduct(product_id=r.product_id, product_name=r.product_name, quantity=int(r.quantity or 0)) for r in rows]

    # ---------- Low rotation ----------
    def get_low_rotation_products(self, db: Session, company_id: uuid.UUID, threshold: int = 5) -> List[LowRotationProduct]:
        start, end = self._current_month_range()
        stmt = (
            select(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                func.coalesce(func.sum(SaleItem.quantity), 0).label("quantity"),
            )
            .join(SaleItem.product)
            .join(SaleItem.sale)
            .where(Sale.company_id == company_id, Sale.created_at >= start, Sale.created_at < end)
            .group_by(Product.id)
            .having(func.coalesce(func.sum(SaleItem.quantity), 0) <= threshold)
        )
        rows = db.execute(stmt).all()
        return [LowRotationProduct(product_id=r.product_id, product_name=r.product_name, quantity=int(r.quantity)) for r in rows]

    # ---------- Sales trend ----------
    def get_sales_trend(self, db: Session, company_id: uuid.UUID, days: int = 7) -> Tuple[float, str] | None:
        now = datetime.utcnow()
        recent_start = now - timedelta(days=days)
        previous_start = recent_start - timedelta(days=days)
        # recent period sum
        recent_sum = db.scalar(
            select(func.coalesce(func.sum(Sale.total), 0))
            .where(Sale.company_id == company_id, Sale.created_at >= recent_start, Sale.created_at < now)
        )
        # previous period sum
        previous_sum = db.scalar(
            select(func.coalesce(func.sum(Sale.total), 0))
            .where(Sale.company_id == company_id, Sale.created_at >= previous_start, Sale.created_at < recent_start)
        )
        if previous_sum == 0:
            # avoid division by zero – cannot determine trend reliably
            return None
        change = ((recent_sum - previous_sum) / previous_sum) * 100
        direction = "hausse" if change > 5 else "baisse" if change < -5 else "stable"
        return float(change), direction

    # ---------- Stock alerts ----------
    def get_stock_alerts(self, db: Session, company_id: uuid.UUID) -> List[dict]:
        stmt = (
            select(Product)
            .where(
                Product.company_id == company_id,
                Product.is_active.is_(True),
                Product.current_stock <= Product.minimum_stock,
            )
        )
        products = db.scalars(stmt).all()
        alerts = []
        for p in products:
            status = "OUT_OF_STOCK" if p.current_stock == 0 else "LOW_STOCK"
            message = f"Stock faible ({p.current_stock} unités)."
            alerts.append({"product_id": p.id, "product_name": p.name, "message": message, "status": status})
        return alerts

    # ---------- Stock forecast ----------
    def get_stock_forecast(self, db: Session, company_id: uuid.UUID, horizon_days: int = 7) -> List[StockForecastResponse]:
        # Compute average daily quantity sold for each product over the last 30 days
        now = datetime.utcnow()
        start = now - timedelta(days=30)
        stmt = (
            select(
                Product.id.label("product_id"),
                Product.name.label("product_name"),
                func.coalesce(func.sum(SaleItem.quantity), 0).label("total_quantity"),
            )
            .join(SaleItem.product)
            .join(SaleItem.sale)
            .where(Sale.company_id == company_id, Sale.created_at >= start, Sale.created_at < now)
            .group_by(Product.id)
        )
        rows = db.execute(stmt).all()
        forecasts = []
        for r in rows:
            avg_daily = float(r.total_quantity) / 30.0
            predicted = max(int(avg_daily * horizon_days), 0)
            forecasts.append(
                StockForecastResponse(
                    product_id=r.product_id,
                    product_name=r.product_name,
                    predicted_need=predicted,
                    horizon=horizon_days,
                )
            )
        return forecasts

    # ---------- Combined insights endpoint ----------
    def compute_insights(self, db: Session, company_id: uuid.UUID) -> List[AiInsightResponse]:
        insights: List[AiInsightResponse] = []
        # top products
        for prod in self.get_top_products(db, company_id):
            insights.append(
                AiInsightResponse(
                    id=uuid.uuid4(),
                    title=f"Produit le plus vendu: {prod.product_name}",
                    description=f"Vendu {prod.quantity} unités ce mois-ci.",
                    severity="info",
                    category="TOP_PRODUCTS",
                    created_at=datetime.utcnow(),
                )
            )
        # low rotation
        for prod in self.get_low_rotation_products(db, company_id):
            insights.append(
                AiInsightResponse(
                    id=uuid.uuid4(),
                    title=f"Faible rotation: {prod.product_name}",
                    description=f"Vendu seulement {prod.quantity} unités ce mois-ci.",
                    severity="warning",
                    category="LOW_ROTATION",
                    created_at=datetime.utcnow(),
                )
            )
        # trend
        trend = self.get_sales_trend(db, company_id)
        if trend:
            change, direction = trend
            insights.append(
                AiInsightResponse(
                    id=uuid.uuid4(),
                    title="Tendance des ventes",
                    description=f"Variation de {abs(change):.2f}% ({direction}) par rapport à la période précédente.",
                    severity="info",
                    category="TREND",
                    created_at=datetime.utcnow(),
                )
            )
        # stock alerts
        for a in self.get_stock_alerts(db, company_id):
            insights.append(
                AiInsightResponse(
                    id=uuid.uuid4(),
                    title=f"Alerte stock: {a['product_name']}",
                    description=a['message'],
                    severity="critical",
                    category="STOCK_ALERT",
                    created_at=datetime.utcnow(),
                )
            )
        return insights
