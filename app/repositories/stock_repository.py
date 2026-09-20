from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.stock import StockMovement


class StockRepository:
    def add(self, db: Session, movement: StockMovement) -> StockMovement:
        db.add(movement); db.flush(); return movement
    def list(self, db: Session, company_id: UUID, **filters):
        query = select(StockMovement).where(StockMovement.company_id == company_id)
        if filters.get("product_id"): query = query.where(StockMovement.product_id == filters["product_id"])
        if filters.get("movement_type"): query = query.where(StockMovement.movement_type == filters["movement_type"])
        return db.scalars(query.order_by(StockMovement.created_at.desc()).offset(filters["offset"]).limit(filters["limit"])).all()
