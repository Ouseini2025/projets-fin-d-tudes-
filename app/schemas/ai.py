from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field

class AiInsightResponse(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    severity: str  # 'info', 'warning', 'critical'
    category: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True

class StockForecastResponse(BaseModel):
    product_id: UUID
    product_name: str
    predicted_need: int
    horizon: int  # days forecast horizon
    method: str | None = None

    class Config:
        from_attributes = True

# New schemas required by the AI service
class TopProduct(BaseModel):
    product_id: UUID
    product_name: str
    quantity: int

    class Config:
        from_attributes = True

class LowRotationProduct(BaseModel):
    product_id: UUID
    product_name: str
    quantity: int

    class Config:
        from_attributes = True
