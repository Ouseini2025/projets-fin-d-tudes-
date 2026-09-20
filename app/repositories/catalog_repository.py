from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.catalog import Category, Product


class CatalogRepository:
    def category(self, db: Session, company_id: UUID, category_id: UUID) -> Category | None:
        return db.scalar(select(Category).where(Category.id == category_id, Category.company_id == company_id))
    def product(self, db: Session, company_id: UUID, product_id: UUID, lock: bool = False) -> Product | None:
        query = select(Product).where(Product.id == product_id, Product.company_id == company_id)
        return db.scalar(query.with_for_update() if lock else query)
