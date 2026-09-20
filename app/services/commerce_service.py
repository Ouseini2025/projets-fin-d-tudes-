from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.catalog import Product
from app.models.commerce import Credit, Customer, Payment, Sale, SaleItem
from app.services.stock_service import StockService


class CommerceError(Exception):
    pass


def credit_status(remaining: Decimal, due: date | None) -> str:
    if remaining == Decimal("0"):
        return "PAYE"

    if due and due < date.today():
        return "EN_RETARD"

    return "PARTIELLEMENT_PAYE"


class SaleService:
    def create(self, db: Session, user, data):
        customer = None

        if data.customer_id:
            customer = db.scalar(
                select(Customer).where(
                    Customer.id == data.customer_id,
                    Customer.company_id == user.company_id,
                )
            )

        if data.customer_id and not customer:
            raise CommerceError(
                "Client introuvable dans votre entreprise."
            )

        subtotal = Decimal("0")
        lines = []

        for line in data.items:
            product = db.scalar(
                select(Product)
                .where(
                    Product.id == line.product_id,
                    Product.company_id == user.company_id,
                )
                .with_for_update()
            )

            if not product:
                raise CommerceError(
                    "Produit introuvable dans votre entreprise."
                )

            value = (
                product.selling_price * line.quantity
                - line.discount
            )

            if value < 0:
                raise CommerceError(
                    "Remise de ligne invalide."
                )

            subtotal += value
            lines.append((product, line, value))

        total = subtotal - data.discount

        if total < 0 or data.amount_paid > total:
            raise CommerceError(
                "Montant de paiement ou remise invalide."
            )

        if data.amount_paid < total and not customer:
            raise CommerceError(
                "Un client est obligatoire pour une vente à crédit."
            )

        if data.amount_paid == total:
            payment_status = "PAID"
        elif data.amount_paid == Decimal("0"):
            payment_status = "CREDIT"
        else:
            payment_status = "PARTIALLY_PAID"

        count = db.scalar(
            select(func.count(Sale.id)).where(
                Sale.company_id == user.company_id
            )
        ) + 1

        sale = Sale(
            company_id=user.company_id,
            customer_id=data.customer_id,
            user_id=user.id,
            sale_number=f"VTE-{date.today():%Y%m%d}-{count:04d}",
            subtotal=subtotal,
            discount=data.discount,
            total=total,
            amount_paid=data.amount_paid,
            payment_status=payment_status,
            payment_method=data.payment_method,
        )

        db.add(sale)
        db.flush()

        for product, line, value in lines:
            StockService().move(
                db,
                company_id=user.company_id,
                user_id=user.id,
                product_id=product.id,
                movement_type="EXIT",
                quantity=line.quantity,
                reason=f"Vente {sale.sale_number}",
            )

            db.add(
                SaleItem(
                    sale_id=sale.id,
                    product_id=product.id,
                    quantity=line.quantity,
                    unit_price=product.selling_price,
                    discount=line.discount,
                    subtotal=value,
                )
            )

        if data.amount_paid < total:
            remaining = total - data.amount_paid

            db.add(
                Credit(
                    company_id=user.company_id,
                    customer_id=customer.id,
                    sale_id=sale.id,
                    original_amount=total,
                    amount_paid=data.amount_paid,
                    remaining_amount=remaining,
                    due_date=data.due_date,
                    status=credit_status(
                        remaining,
                        data.due_date,
                    ),
                )
            )

        return sale


class CreditService:
    def pay(self, db: Session, user, credit_id, data):
        credit = db.scalar(
            select(Credit)
            .where(
                Credit.id == credit_id,
                Credit.company_id == user.company_id,
            )
            .with_for_update()
        )

        if not credit:
            raise CommerceError(
                "Crédit introuvable dans votre entreprise."
            )

        if credit.remaining_amount == Decimal("0"):
            raise CommerceError(
                "Ce crédit est déjà entièrement payé."
            )

        if data.amount > credit.remaining_amount:
            raise CommerceError(
                "Versement invalide pour ce crédit."
            )

        payment = Payment(
            company_id=user.company_id,
            credit_id=credit.id,
            customer_id=credit.customer_id,
            user_id=user.id,
            amount=data.amount,
            payment_method=data.payment_method,
            reference=data.reference,
            notes=data.notes,
        )

        db.add(payment)

        credit.amount_paid += data.amount
        credit.remaining_amount -= data.amount

        credit.status = credit_status(
            credit.remaining_amount,
            credit.due_date,
        )

        db.flush()

        return credit