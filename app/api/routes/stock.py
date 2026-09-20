from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from app.api.deps import DbSession, require_roles
from app.models.catalog import Product
from app.models.user import User
from app.repositories.stock_repository import StockRepository
from app.schemas.catalog import ProductResponse
from app.schemas.stock import StockAlertResponse, StockMovementCreate, StockMovementResponse
from app.services.stock_service import InsufficientStockError, ProductNotFoundError, StockDomainError, StockService

router=APIRouter(prefix="/stock",tags=["stock"])
read=Depends(require_roles("ADMIN","GERANT","GESTIONNAIRE","EMPLOYE"))
move_permission=Depends(require_roles("ADMIN","GERANT","GESTIONNAIRE"))

@router.get("/movements",response_model=list[StockMovementResponse])
def movements(db: DbSession,user: User=read,product_id:UUID|None=None,movement_type:str|None=None,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100)):
    return StockRepository().list(db,user.company_id,product_id=product_id,movement_type=movement_type,offset=offset,limit=limit)

@router.post("/movements",response_model=StockMovementResponse,status_code=201)
def create_movement(data:StockMovementCreate,db:DbSession,user:User=move_permission):
    try:
        movement=StockService().move(db,company_id=user.company_id,user_id=user.id,**data.model_dump())
        db.commit(); db.refresh(movement); return movement
    except ProductNotFoundError as e:
        db.rollback(); raise HTTPException(404,str(e)) from e
    except (InsufficientStockError,StockDomainError) as e:
        db.rollback(); raise HTTPException(422,str(e)) from e

@router.get("/products/{product_id}",response_model=ProductResponse)
def stock_product(product_id:UUID,db:DbSession,user:User=read):
    product=db.scalar(select(Product).where(Product.id==product_id,Product.company_id==user.company_id))
    if not product: raise HTTPException(404,"Produit introuvable dans votre entreprise.")
    return product

@router.get("/alerts",response_model=list[StockAlertResponse])
def alerts(db:DbSession,user:User=read):
    products=db.scalars(select(Product).where(Product.company_id==user.company_id,Product.is_active.is_(True),Product.current_stock<=Product.minimum_stock)).all()
    return [StockAlertResponse(product_id=p.id,product_name=p.name,current_stock=p.current_stock,minimum_stock=p.minimum_stock,status="OUT_OF_STOCK" if p.current_stock==0 else "LOW_STOCK") for p in products]
