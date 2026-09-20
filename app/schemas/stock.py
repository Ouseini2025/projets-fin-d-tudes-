from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class StockMovementCreate(BaseModel):
    product_id: UUID
    movement_type: str = Field(pattern="^(ENTRY|EXIT|ADJUSTMENT|RETURN)$")
    quantity: int = Field(gt=0)
    reason: str | None = None
    reference: str | None = Field(default=None, max_length=100)


class StockMovementResponse(BaseModel):
    id: UUID; product_id: UUID; user_id: UUID; movement_type: str; quantity: int
    stock_before: int; stock_after: int; reason: str | None; reference: str | None; created_at: datetime
    model_config = {"from_attributes": True}


class StockAlertResponse(BaseModel):
    product_id: UUID; product_name: str; current_stock: int; minimum_stock: int; status: str
