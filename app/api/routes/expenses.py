from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import DbSession, require_roles
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseUpdate
from app.services.expense_service import ExpenseError, ExpenseService


router = APIRouter(tags=["expenses"])

manage = Depends(
    require_roles("ADMIN", "GERANT", "GESTIONNAIRE")
)

service = ExpenseService()


@router.get("", response_model=list[ExpenseResponse])
def list_expenses(
    db: DbSession,
    user=Depends(require_roles("ADMIN", "GERANT", "GESTIONNAIRE", "EMPLOYE")),
    category: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
):
    try:
        return service.list(
            db,
            user,
            category=category,
            date_from=date_from,
            date_to=date_to,
        )
    except ExpenseError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("", response_model=ExpenseResponse, dependencies=[manage])
def create_expense(
    data: ExpenseCreate,
    db: DbSession,
    user=Depends(require_roles("ADMIN", "GERANT", "GESTIONNAIRE")),
):
    try:
        expense = service.create(db, user, data)
        db.commit()
        db.refresh(expense)
        return expense
    except ExpenseError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse,
)
def get_expense(
    expense_id: UUID,
    db: DbSession,
    user=Depends(require_roles("ADMIN", "GERANT", "GESTIONNAIRE", "EMPLOYE")),
):
    try:
        return service.get(db, user, expense_id)
    except ExpenseError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch(
    "/{expense_id}",
    response_model=ExpenseResponse,
    dependencies=[manage],
)
def update_expense(
    expense_id: UUID,
    data: ExpenseUpdate,
    db: DbSession,
    user=Depends(require_roles("ADMIN", "GERANT", "GESTIONNAIRE")),
):
    try:
        expense = service.update(db, user, expense_id, data)
        db.commit()
        db.refresh(expense)
        return expense
    except ExpenseError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete(
    "/{expense_id}",
    status_code=204,
    dependencies=[manage],
)
def delete_expense(
    expense_id: UUID,
    db: DbSession,
    user=Depends(require_roles("ADMIN", "GERANT", "GESTIONNAIRE")),
):
    try:
        service.delete(db, user, expense_id)
        db.commit()
    except ExpenseError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc))