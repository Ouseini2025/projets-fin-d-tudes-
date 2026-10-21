from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field, model_validator


class CustomerCreate(BaseModel):
    first_name: str
    last_name: str
    phone: str
    email: str | None = None
    address: str | None = None
    notes: str | None = None


class CustomerUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class CustomerResponse(CustomerCreate):
    id: UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class SaleLineCreate(BaseModel):
    product_id: UUID
    quantity: int = Field(gt=0)
    discount: Decimal = Field(default=Decimal("0"), ge=0)


class SaleCreate(BaseModel):
    customer_id: UUID | None = None
    items: list[SaleLineCreate] = Field(min_length=1)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    payment_method: str = Field(
        pattern="^(CASH|MOBILE_MONEY|BANK_TRANSFER|OTHER)$"
    )
    amount_paid: Decimal = Field(default=Decimal("0"), ge=0)
    due_date: date | None = None


class SaleItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str = ""
    quantity: int
    unit_price: Decimal
    discount: Decimal
    subtotal: Decimal
    created_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def get_product_name(cls, value):
        product = getattr(value, "product", None)

        if product:
            data = {
                "id": value.id,
                "product_id": value.product_id,
                "product_name": product.name,
                "quantity": value.quantity,
                "unit_price": value.unit_price,
                "discount": value.discount,
                "subtotal": value.subtotal,
                "created_at": value.created_at,
            }
            return data

        return value


class SaleResponse(BaseModel):
    id: UUID
    sale_number: str
    customer_id: UUID | None = None
    user_id: UUID
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    amount_paid: Decimal
    payment_status: str
    payment_method: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SaleDetailResponse(SaleResponse):
    items: list[SaleItemResponse] = Field(default_factory=list)


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0)
    payment_method: str = Field(
        pattern="^(CASH|MOBILE_MONEY|BANK_TRANSFER|OTHER)$"
    )
    reference: str | None = None
    notes: str | None = None


class PaymentResponse(BaseModel):
    id: UUID
    credit_id: UUID
    customer_id: UUID
    user_id: UUID
    amount: Decimal
    payment_method: str
    reference: str | None = None
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CreditResponse(BaseModel):
    id: UUID
    customer_id: UUID
    sale_id: UUID
    original_amount: Decimal
    amount_paid: Decimal
    remaining_amount: Decimal
    status: str
    due_date: date | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CreditDetailResponse(CreditResponse):
    payments: list[PaymentResponse] = Field(default_factory=list)

