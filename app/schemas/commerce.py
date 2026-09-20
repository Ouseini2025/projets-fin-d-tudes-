from datetime import date,datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel,Field
class CustomerCreate(BaseModel): first_name:str; last_name:str; phone:str; email:str|None=None; address:str|None=None; notes:str|None=None
class CustomerUpdate(BaseModel): first_name:str|None=None; last_name:str|None=None; phone:str|None=None; email:str|None=None; address:str|None=None; notes:str|None=None; is_active:bool|None=None
class CustomerResponse(CustomerCreate): id:UUID; is_active:bool; created_at:datetime; model_config={'from_attributes':True}
class SaleLineCreate(BaseModel): product_id:UUID; quantity:int=Field(gt=0); discount:Decimal=Field(default=Decimal('0'),ge=0)
class SaleCreate(BaseModel): customer_id:UUID|None=None; items:list[SaleLineCreate]=Field(min_length=1); discount:Decimal=Field(default=Decimal('0'),ge=0); payment_method:str=Field(pattern='^(CASH|MOBILE_MONEY|BANK_TRANSFER|OTHER)$'); amount_paid:Decimal=Field(default=Decimal('0'),ge=0); due_date:date|None=None
class SaleResponse(BaseModel): id:UUID;sale_number:str;subtotal:Decimal;discount:Decimal;total:Decimal;amount_paid:Decimal;payment_status:str; model_config={'from_attributes':True}
class PaymentCreate(BaseModel): amount:Decimal=Field(gt=0);payment_method:str=Field(pattern='^(CASH|MOBILE_MONEY|BANK_TRANSFER|OTHER)$');reference:str|None=None;notes:str|None=None
class CreditResponse(BaseModel): id:UUID;original_amount:Decimal;amount_paid:Decimal;remaining_amount:Decimal;status:str;due_date:date|None=None;model_config={'from_attributes':True}
