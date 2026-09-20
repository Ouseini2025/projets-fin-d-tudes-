from uuid import UUID
from sqlalchemy.orm import Session
from app.models.stock import StockMovement
from app.repositories.catalog_repository import CatalogRepository
from app.repositories.stock_repository import StockRepository


class StockDomainError(Exception): pass
class InsufficientStockError(StockDomainError): pass
class ProductNotFoundError(StockDomainError): pass


class StockService:
    def __init__(self, catalog=None, movements=None):
        self.catalog = catalog or CatalogRepository(); self.movements = movements or StockRepository()
    def move(self, db: Session, *, company_id: UUID, user_id: UUID, product_id: UUID, movement_type: str, quantity: int, reason=None, reference=None):
        product = self.catalog.product(db, company_id, product_id, lock=True)
        if product is None: raise ProductNotFoundError("Produit introuvable dans votre entreprise.")
        if quantity <= 0: raise StockDomainError("La quantité doit être supérieure à zéro.")
        before = product.current_stock
        after = quantity if movement_type == "ADJUSTMENT" else before + quantity if movement_type in {"ENTRY", "RETURN"} else before - quantity
        if after < 0: raise InsufficientStockError("Stock insuffisant pour cette sortie.")
        product.current_stock = after
        return self.movements.add(db, StockMovement(company_id=company_id, product_id=product.id, user_id=user_id, movement_type=movement_type, quantity=quantity, stock_before=before, stock_after=after, reason=reason, reference=reference))
