from datetime import date, datetime, time, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import DbSession, require_roles
from app.models.commerce import Customer, Credit, Payment, Sale
from app.models.user import User
from app.schemas.commerce import (
    CreditDetailResponse,
    CreditResponse,
    CustomerCreate,
    CustomerResponse,
    CustomerUpdate,
    PaymentCreate,
    PaymentResponse,
    SaleCreate,
    SaleDetailResponse,
    SaleResponse,
)
from app.services.commerce_service import (
    CommerceError,
    CreditService,
    SaleService,
)


r = APIRouter(tags=["commerce"])

manage = Depends(
    require_roles("ADMIN", "GERANT", "GESTIONNAIRE")
)


@r.get(
    "/customers",
    response_model=list[CustomerResponse],
)
def customers(
    db: DbSession,
    user: User = manage,
    search: str | None = None,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    q = select(Customer).where(
        Customer.company_id == user.company_id
    )

    if search:
        q = q.where(
            or_(
                Customer.first_name.ilike(f"%{search}%"),
                Customer.last_name.ilike(f"%{search}%"),
                Customer.phone.ilike(f"%{search}%"),
            )
        )

    q = q.order_by(Customer.created_at.desc())

    return db.scalars(
        q.offset(offset).limit(limit)
    ).all()


@r.post(
    "/customers",
    response_model=CustomerResponse,
    status_code=201,
)
def customer(
    data: CustomerCreate,
    db: DbSession,
    user: User = manage,
):
    customer_obj = Customer(
        company_id=user.company_id,
        **data.model_dump(),
    )

    db.add(customer_obj)
    db.commit()
    db.refresh(customer_obj)

    return customer_obj


@r.get(
    "/customers/{id}",
    response_model=CustomerResponse,
)
def get_customer(
    id: UUID,
    db: DbSession,
    user: User = manage,
):
    customer_obj = db.scalar(
        select(Customer).where(
            Customer.id == id,
            Customer.company_id == user.company_id,
        )
    )

    if not customer_obj:
        raise HTTPException(
            404,
            "Client introuvable.",
        )

    return customer_obj


@r.patch(
    "/customers/{id}",
    response_model=CustomerResponse,
)
def update_customer(
    id: UUID,
    data: CustomerUpdate,
    db: DbSession,
    user: User = manage,
):
    customer_obj = db.scalar(
        select(Customer).where(
            Customer.id == id,
            Customer.company_id == user.company_id,
        )
    )

    if not customer_obj:
        raise HTTPException(
            404,
            "Client introuvable.",
        )

    for key, value in data.model_dump(
        exclude_unset=True
    ).items():
        setattr(customer_obj, key, value)

    db.commit()
    db.refresh(customer_obj)

    return customer_obj


@r.delete(
    "/customers/{id}",
    status_code=204,
)
def delete_customer(
    id: UUID,
    db: DbSession,
    user: User = manage,
):
    customer_obj = db.scalar(
        select(Customer).where(
            Customer.id == id,
            Customer.company_id == user.company_id,
        )
    )

    if not customer_obj:
        raise HTTPException(
            404,
            "Client introuvable.",
        )

    customer_obj.is_active = False

    db.commit()


@r.get(
    "/sales",
    response_model=list[SaleResponse],
)
def sales(
    db: DbSession,
    user: User = manage,
    customer_id: UUID | None = None,
    payment_status: str | None = None,
    sale_number: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail="date_from doit être antérieure ou égale à date_to.",
        )

    q = select(Sale).where(
        Sale.company_id == user.company_id
    )

    if customer_id:
        q = q.where(
            Sale.customer_id == customer_id
        )

    if payment_status:
        q = q.where(
            Sale.payment_status == payment_status
        )

    if sale_number:
        q = q.where(
            Sale.sale_number == sale_number
        )

    if date_from:
        start = datetime.combine(
            date_from,
            time.min,
        )
        q = q.where(
            Sale.created_at >= start
        )

    if date_to:
        end = datetime.combine(
            date_to + timedelta(days=1),
            time.min,
        )
        q = q.where(
            Sale.created_at < end
        )

    q = q.order_by(Sale.created_at.desc())

    return db.scalars(q).all()


@r.post(
    "/sales",
    response_model=SaleResponse,
    status_code=201,
)
def sale(
    data: SaleCreate,
    db: DbSession,
    user: User = manage,
):
    try:
        sale_obj = SaleService().create(
            db,
            user,
            data,
        )

        db.commit()
        db.refresh(sale_obj)

        return sale_obj

    except CommerceError as exc:
        db.rollback()

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )


@r.get(
    "/sales/{id}",
    response_model=SaleDetailResponse,
)
def get_sale(
    id: UUID,
    db: DbSession,
    user: User = manage,
):
    sale_obj = db.scalar(
        select(Sale)
        .options(selectinload(Sale.items))
        .where(
            Sale.id == id,
            Sale.company_id == user.company_id,
        )
    )

    if not sale_obj:
        raise HTTPException(
            404,
            "Vente introuvable.",
        )

    return sale_obj


@r.get(
    "/credits",
    response_model=list[CreditResponse],
)
def credits(
    db: DbSession,
    user: User = manage,
    status_filter: str | None = None,
    customer_id: UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
):
    if date_from and date_to and date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail="date_from doit être antérieure ou égale à date_to.",
        )

    q = select(Credit).where(
        Credit.company_id == user.company_id
    )

    if status_filter:
        q = q.where(
            Credit.status == status_filter
        )

    if customer_id:
        q = q.where(
            Credit.customer_id == customer_id
        )

    if date_from:
        start = datetime.combine(
            date_from,
            time.min,
        )
        q = q.where(
            Credit.created_at >= start
        )

    if date_to:
        end = datetime.combine(
            date_to + timedelta(days=1),
            time.min,
        )
        q = q.where(
            Credit.created_at < end
        )

    q = q.order_by(Credit.created_at.desc())

    return db.scalars(q).all()


@r.get(
    "/credits/{id}",
    response_model=CreditDetailResponse,
)
def credit(
    id: UUID,
    db: DbSession,
    user: User = manage,
):
    credit_obj = db.scalar(
        select(Credit)
        .options(selectinload(Credit.payments))
        .where(
            Credit.id == id,
            Credit.company_id == user.company_id,
        )
    )

    if not credit_obj:
        raise HTTPException(
            404,
            "Crédit introuvable.",
        )

    return credit_obj


@r.get(
    "/credits/{id}/payments",
    response_model=list[PaymentResponse],
)
def payments(
    id: UUID,
    db: DbSession,
    user: User = manage,
):
    credit_obj = db.scalar(
        select(Credit).where(
            Credit.id == id,
            Credit.company_id == user.company_id,
        )
    )

    if not credit_obj:
        raise HTTPException(
            404,
            "Crédit introuvable.",
        )

    return db.scalars(
        select(Payment)
        .where(
            Payment.credit_id == id,
            Payment.company_id == user.company_id,
        )
        .order_by(Payment.created_at.desc())
    ).all()


@r.post(
    "/credits/{id}/payments",
    response_model=CreditResponse,
)
def pay(
    id: UUID,
    data: PaymentCreate,
    db: DbSession,
    user: User = manage,
):
    try:
        credit_obj = CreditService().pay(
            db,
            user,
            id,
            data,
        )

        db.commit()
        db.refresh(credit_obj)

        return credit_obj

    except CommerceError as exc:
        db.rollback()

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )