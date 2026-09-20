from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from app.api.deps import DbSession, require_roles
from app.models.catalog import Category, Product
from app.models.user import User
from app.schemas.catalog import CategoryCreate, CategoryResponse, CategoryUpdate, ProductCreate, ProductResponse, ProductUpdate

router = APIRouter(tags=["catalogue"])
manage = Depends(require_roles("ADMIN", "GERANT"))
read = Depends(require_roles("ADMIN", "GERANT", "GESTIONNAIRE", "EMPLOYE"))

def not_found(): raise HTTPException(404, "Ressource introuvable.")
def category(db, user, item_id): return db.scalar(select(Category).where(Category.id == item_id, Category.company_id == user.company_id))
def product(db, user, item_id): return db.scalar(select(Product).where(Product.id == item_id, Product.company_id == user.company_id))

@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(db: DbSession, user: User = read): return db.scalars(select(Category).where(Category.company_id == user.company_id).order_by(Category.name)).all()
@router.post("/categories", response_model=CategoryResponse, status_code=201)
def create_category(data: CategoryCreate, db: DbSession, user: User = manage):
    item = Category(company_id=user.company_id, **data.model_dump()); db.add(item); db.commit(); db.refresh(item); return item
@router.get("/categories/{item_id}", response_model=CategoryResponse)
def get_category(item_id: UUID, db: DbSession, user: User = read):
    return category(db,user,item_id) or not_found()
@router.patch("/categories/{item_id}", response_model=CategoryResponse)
def update_category(item_id: UUID, data: CategoryUpdate, db: DbSession, user: User = manage):
    item=category(db,user,item_id)
    if not item: not_found()
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(item,k,v)
    db.commit(); db.refresh(item); return item
@router.delete("/categories/{item_id}", status_code=204)
def delete_category(item_id: UUID, db: DbSession, user: User = manage):
    item=category(db,user,item_id)
    if not item: not_found()
    item.is_active=False; db.commit()

@router.get("/products", response_model=list[ProductResponse])
def list_products(db: DbSession, user: User = read, search: str|None=None, category_id: UUID|None=None, sku: str|None=None, is_active: bool|None=None, offset: int=Query(0,ge=0), limit: int=Query(50,ge=1,le=100)):
    q=select(Product).where(Product.company_id==user.company_id)
    if search: q=q.where(Product.name.ilike(f"%{search}%"))
    if category_id: q=q.where(Product.category_id==category_id)
    if sku: q=q.where(Product.sku==sku)
    if is_active is not None: q=q.where(Product.is_active==is_active)
    return db.scalars(q.order_by(Product.name).offset(offset).limit(limit)).all()
@router.post("/products", response_model=ProductResponse, status_code=201)
def create_product(data: ProductCreate, db: DbSession, user: User = manage):
    payload=data.model_dump()
    if payload["category_id"] and not category(db,user,payload["category_id"]): raise HTTPException(422,"Catégorie introuvable dans votre entreprise.")
    item=Product(company_id=user.company_id,**payload); db.add(item); db.commit(); db.refresh(item); return item
@router.get("/products/{item_id}", response_model=ProductResponse)
def get_product(item_id: UUID, db: DbSession, user: User = read): return product(db,user,item_id) or not_found()
@router.patch("/products/{item_id}", response_model=ProductResponse)
def update_product(item_id: UUID, data: ProductUpdate, db: DbSession, user: User = manage):
    item=product(db,user,item_id)
    if not item: not_found()
    payload=data.model_dump(exclude_unset=True)
    if "category_id" in payload and payload["category_id"] and not category(db,user,payload["category_id"]): raise HTTPException(422,"Catégorie introuvable dans votre entreprise.")
    for k,v in payload.items(): setattr(item,k,v)
    db.commit(); db.refresh(item); return item
@router.delete("/products/{item_id}", status_code=204)
def delete_product(item_id: UUID, db: DbSession, user: User = manage):
    item=product(db,user,item_id)
    if not item: not_found()
    item.is_active=False; db.commit()
