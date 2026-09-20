from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, Field

UNITS = {"pièce", "carton", "kilogramme", "litre", "mètre", "autre"}


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    is_active: bool | None = None


class CategoryResponse(BaseModel):
    id: UUID; name: str; description: str | None; is_active: bool; created_at: datetime; updated_at: datetime
    model_config = {"from_attributes": True}


class ProductCreate(BaseModel):
    category_id: UUID | None = None
    name: str = Field(min_length=1, max_length=160)
    sku: str | None = Field(default=None, max_length=80)
    barcode: str | None = Field(default=None, max_length=80)
    description: str | None = None
    purchase_price: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    selling_price: Decimal = Field(default=Decimal("0"), ge=0, max_digits=14, decimal_places=2)
    current_stock: int = Field(default=0, ge=0)
    minimum_stock: int = Field(default=0, ge=0)
    unit: str = "pièce"


class ProductUpdate(BaseModel):
    category_id: UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=160)
    sku: str | None = Field(default=None, max_length=80)
    barcode: str | None = Field(default=None, max_length=80)
    description: str | None = None
    purchase_price: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    selling_price: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)
    minimum_stock: int | None = Field(default=None, ge=0)
    unit: str | None = None
    is_active: bool | None = None


class ProductResponse(BaseModel):
    id: UUID; category_id: UUID | None; name: str; sku: str | None; barcode: str | None; description: str | None
    purchase_price: Decimal; selling_price: Decimal; current_stock: int; minimum_stock: int; unit: str; is_active: bool
    created_at: datetime; updated_at: datetime
    model_config = {"from_attributes": True}
