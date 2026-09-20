from uuid import UUID
from fastapi import APIRouter,Depends,HTTPException,status,Query
from sqlalchemy import select,or_
from app.api.deps import DbSession,require_roles
from app.models.commerce import Customer,Credit,Payment,Sale
from app.models.user import User
from app.schemas.commerce import *
from app.services.commerce_service import CommerceError,CreditService,SaleService
r=APIRouter(tags=['commerce']); manage=Depends(require_roles('ADMIN','GERANT','GESTIONNAIRE'))
@r.get('/customers',response_model=list[CustomerResponse])
def customers(db:DbSession,user:User=manage,search:str|None=None,offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100)):
 q=select(Customer).where(Customer.company_id==user.company_id)
 if search:q=q.where(or_(Customer.first_name.ilike(f'%{search}%'),Customer.last_name.ilike(f'%{search}%'),Customer.phone.ilike(f'%{search}%')))
 return db.scalars(q.offset(offset).limit(limit)).all()
@r.post('/customers',response_model=CustomerResponse,status_code=201)
def customer(d:CustomerCreate,db:DbSession,user:User=manage): x=Customer(company_id=user.company_id,**d.model_dump());db.add(x);db.commit();db.refresh(x);return x
@r.get('/customers/{id}',response_model=CustomerResponse)
def get_customer(id:UUID,db:DbSession,user:User=manage):
 x=db.scalar(select(Customer).where(Customer.id==id,Customer.company_id==user.company_id))
 if not x:raise HTTPException(404,'Client introuvable.')
 return x
@r.patch('/customers/{id}',response_model=CustomerResponse)
def update_customer(id:UUID,d:CustomerUpdate,db:DbSession,user:User=manage):
 x=db.scalar(select(Customer).where(Customer.id==id,Customer.company_id==user.company_id))
 if not x:raise HTTPException(404,'Client introuvable.')
 for k,v in d.model_dump(exclude_unset=True).items():setattr(x,k,v)
 db.commit();db.refresh(x);return x
@r.delete('/customers/{id}',status_code=204)
def delete_customer(id:UUID,db:DbSession,user:User=manage):
 x=db.scalar(select(Customer).where(Customer.id==id,Customer.company_id==user.company_id))
 if not x:raise HTTPException(404,'Client introuvable.')
 x.is_active=False;db.commit()
@r.get('/sales',response_model=list[SaleResponse])
def sales(db:DbSession,user:User=manage,customer_id:UUID|None=None,payment_status:str|None=None,sale_number:str|None=None):
 q=select(Sale).where(Sale.company_id==user.company_id)
 if customer_id:q=q.where(Sale.customer_id==customer_id)
 if payment_status:q=q.where(Sale.payment_status==payment_status)
 if sale_number:q=q.where(Sale.sale_number==sale_number)
 return db.scalars(q).all()
@r.post('/sales',response_model=SaleResponse,status_code=201)
def sale(d:SaleCreate,db:DbSession,user:User=manage):
 try: x=SaleService().create(db,user,d);db.commit();db.refresh(x);return x
 except Exception as e: db.rollback();raise HTTPException(422,str(e))
@r.get('/sales/{id}',response_model=SaleResponse)
def get_sale(id:UUID,db:DbSession,user:User=manage):
 x=db.scalar(select(Sale).where(Sale.id==id,Sale.company_id==user.company_id))
 if not x:raise HTTPException(404,'Vente introuvable.')
 return x
@r.get('/credits',response_model=list[CreditResponse])
def credits(db:DbSession,user:User=manage,status_filter:str|None=None,customer_id:UUID|None=None):
 q=select(Credit).where(Credit.company_id==user.company_id)
 if status_filter:q=q.where(Credit.status==status_filter)
 if customer_id:q=q.where(Credit.customer_id==customer_id)
 return db.scalars(q).all()
@r.get('/credits/{id}',response_model=CreditResponse)
def credit(id:UUID,db:DbSession,user:User=manage):
 x=db.scalar(select(Credit).where(Credit.id==id,Credit.company_id==user.company_id))
 if not x:raise HTTPException(404,'Crédit introuvable.')
 return x
@r.get('/credits/{id}/payments')
def payments(id:UUID,db:DbSession,user:User=manage):
 c=db.scalar(select(Credit).where(Credit.id==id,Credit.company_id==user.company_id))
 if not c:raise HTTPException(404,'Crédit introuvable.')
 return db.scalars(select(Payment).where(Payment.credit_id==id,Payment.company_id==user.company_id)).all()
@r.post('/credits/{id}/payments',response_model=CreditResponse)
def pay(id:UUID,d:PaymentCreate,db:DbSession,user:User=manage):
 try:x=CreditService().pay(db,user,id,d);db.commit();db.refresh(x);return x
 except CommerceError as e:db.rollback();raise HTTPException(422,str(e))
