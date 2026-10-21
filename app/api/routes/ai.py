import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from app.api.deps import DbSession, require_roles
from app.schemas.ai import AiInsightResponse, StockForecastResponse
from app.services.ai_service import AiService

router = APIRouter(prefix="/ai", tags=["ai"])
read = Depends(require_roles("ADMIN", "GERANT", "GESTIONNAIRE", "EMPLOYE"))

@router.get("/insights", response_model=List[AiInsightResponse])
def get_insights(db: DbSession, user: "User" = read):
    service = AiService()
    insights = []
    # Top products
    top = service.get_top_products(db, user.company_id)
    for prod in top:
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
    # Low rotation
    low = service.get_low_rotation_products(db, user.company_id)
    for prod in low:
        insights.append(
            AiInsightResponse(
                id=uuid.uuid4(),
                title=f"Faible rotation: {prod['product_name']}",
                description=f"Vendu seulement {prod['quantity']} unités ce mois-ci.",
                severity="warning",
                category="LOW_ROTATION",
                created_at=datetime.utcnow(),
            )
        )
    # Trend
    trend = service.get_sales_trend(db, user.company_id)
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
    # Stock alerts (reuse existing logic)
    alerts = service.get_stock_alerts(db, user.company_id)
    for a in alerts:
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

@router.get("/stock-forecast", response_model=List[StockForecastResponse])
def get_stock_forecast(db: DbSession, user: "User" = read):
    service = AiService()
    forecasts = service.get_stock_forecast(db, user.company_id)
    # Convert to response objects
    return [
        StockForecastResponse(
            product_id=record['product_id'],
            product_name=record['product_name'],
            predicted_need=record['predicted_need'],
            horizon=record['horizon'],
        )
        for record in forecasts
    ]
