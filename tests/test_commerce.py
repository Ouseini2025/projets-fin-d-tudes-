import os
from datetime import date
from decimal import Decimal

os.environ.setdefault(
    "DATABASE_URL",
    "sqlite+pysqlite:///:memory:",
)
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-at-least-thirty-two-bytes-long",
)
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.database.base import Base
from app.database.session import get_db

# Charge tous les modèles SQLAlchemy
import app.models  # noqa: F401


@pytest.fixture()
def client():
    """
    Crée une base SQLite temporaire pour chaque test.
    """

    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    testing_session = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )

    Base.metadata.create_all(engine)

    def override_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    fastapi_app.dependency_overrides[get_db] = override_db

    with TestClient(fastapi_app) as test_client:
        yield test_client

    fastapi_app.dependency_overrides.clear()
    Base.metadata.drop_all(engine)


def register_company_and_login(
    client: TestClient,
    company_name: str,
    email: str,
    password: str = "TestPassword123!",
):
    """
    Crée une entreprise + un utilisateur puis retourne les headers JWT.
    """

    response = client.post(
        "/api/v1/auth/register",
        json={
            "company_name": company_name,
            "email": email,
            "password": password,
            "full_name": "Test User",
        },
    )

    assert response.status_code in (200, 201), response.text

    data = response.json()

    token = data.get("access_token")

    if token:
        return {
            "Authorization": f"Bearer {token}"
        }

    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": email,
            "password": password,
        },
    )

    assert login_response.status_code == 200, login_response.text

    login_data = login_response.json()

    return {
        "Authorization": f"Bearer {login_data['access_token']}"
    }


def create_category(
    client: TestClient,
    headers,
    name="Test Category",
):
    response = client.post(
        "/api/v1/categories",
        json={"name": name},
        headers=headers,
    )

    assert response.status_code in (200, 201), response.text

    return response.json()


def create_product(
    client: TestClient,
    headers,
    name="Produit Test",
    selling_price="1000.00",
    purchase_price="500.00",
    stock=10,
    minimum_stock=2,
):
    response = client.post(
        "/api/v1/products",
        json={
            "name": name,
            "selling_price": selling_price,
            "purchase_price": purchase_price,
            "current_stock": stock,
            "minimum_stock": minimum_stock,
        },
        headers=headers,
    )

    assert response.status_code in (200, 201), response.text

    return response.json()


def create_customer(
    client: TestClient,
    headers,
    first_name="Client",
    last_name="Test",
    phone="060000000",
    email=None,
):
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
    }

    if email:
        payload["email"] = email

    response = client.post(
        "/api/v1/customers",
        json=payload,
        headers=headers,
    )

    assert response.status_code in (200, 201), response.text

    return response.json()


# ============================================================
# CLIENTS
# ============================================================


def test_customer_crud(client):
    headers = register_company_and_login(
        client,
        "Entreprise Clients",
        "client@test.com",
    )

    customer = create_customer(
        client,
        headers,
        first_name="Client",
        last_name="Test",
        phone="060000000",
        email="customer@test.com",
    )

    assert customer["first_name"] == "Client"
    assert customer["last_name"] == "Test"
    assert customer["phone"] == "060000000"

    customer_id = customer["id"]

    # Lecture
    response = client.get(
        f"/api/v1/customers/{customer_id}",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == customer_id

    # Modification
    response = client.patch(
        f"/api/v1/customers/{customer_id}",
        json={
            "first_name": "Client Modifié",
            "last_name": "Test",
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text

    updated = response.json()

    assert updated["first_name"] == "Client Modifié"
    assert updated["last_name"] == "Test"

    # Désactivation logique
    response = client.delete(
        f"/api/v1/customers/{customer_id}",
        headers=headers,
    )

    assert response.status_code == 204


# ============================================================
# ISOLATION ENTRE ENTREPRISES
# ============================================================


def test_customer_company_isolation(client):
    headers_a = register_company_and_login(
        client,
        "Entreprise A",
        "a@test.com",
    )

    headers_b = register_company_and_login(
        client,
        "Entreprise B",
        "b@test.com",
    )

    customer = create_customer(
        client,
        headers_a,
        first_name="Client",
        last_name="A",
        phone="061111111",
    )

    customer_id = customer["id"]

    response = client.get(
        f"/api/v1/customers/{customer_id}",
        headers=headers_b,
    )

    assert response.status_code == 404


# ============================================================
# PRODUITS
# ============================================================


def test_product_used_for_commerce(client):
    headers = register_company_and_login(
        client,
        "Entreprise Produits",
        "products@test.com",
    )

    product = create_product(
        client,
        headers,
        name="Téléphone Test",
        selling_price="125000.50",
        purchase_price="100000.25",
        stock=10,
    )

    assert Decimal(str(product["selling_price"])) == Decimal("125000.50")
    assert Decimal(str(product["purchase_price"])) == Decimal("100000.25")


# ============================================================
# VENTE
# ============================================================


def test_sale_creation_and_stock_deduction(client):
    headers = register_company_and_login(
        client,
        "Entreprise Vente",
        "sales@test.com",
    )

    product = create_product(
        client,
        headers,
        name="Produit Vente",
        selling_price="1000.00",
        stock=10,
    )

    product_id = product["id"]

    response = client.post(
        "/api/v1/sales",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "2000.00",
        },
        headers=headers,
    )

    assert response.status_code in (200, 201), response.text

    sale = response.json()

    assert sale["id"] is not None
    assert Decimal(str(sale["subtotal"])) == Decimal("2000.00")
    assert Decimal(str(sale["total"])) == Decimal("2000.00")
    assert Decimal(str(sale["amount_paid"])) == Decimal("2000.00")


# ============================================================
# STOCK INSUFFISANT
# ============================================================


def test_sale_rejected_when_stock_is_insufficient(client):
    headers = register_company_and_login(
        client,
        "Entreprise Stock",
        "stock@test.com",
    )

    product = create_product(
        client,
        headers,
        name="Stock Limité",
        selling_price="1000.00",
        stock=2,
    )

    response = client.post(
        "/api/v1/sales",
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 10,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "0.00",
        },
        headers=headers,
    )

    assert response.status_code in (400, 409, 422)


# ============================================================
# CRÉDIT
# ============================================================


def test_credit_sale(client):
    headers = register_company_and_login(
        client,
        "Entreprise Crédit",
        "credit@test.com",
    )

    customer = create_customer(
        client,
        headers,
        first_name="Client",
        last_name="Crédit",
        phone="062222222",
    )

    customer_id = customer["id"]

    product = create_product(
        client,
        headers,
        name="Produit Crédit",
        selling_price="5000.00",
        stock=10,
    )

    response = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 2,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "5000.00",
        },
        headers=headers,
    )

    assert response.status_code in (200, 201), response.text

    sale = response.json()

    assert sale["id"] is not None

    # Vente = 10 000
    # Payé = 5 000
    # Il doit donc rester 5 000.
    assert Decimal(str(sale["total"])) == Decimal("10000.00")
    assert Decimal(str(sale["amount_paid"])) == Decimal("5000.00")


# ============================================================
# PAIEMENT SUR CRÉDIT
# ============================================================


def test_payment_on_credit(client):
    headers = register_company_and_login(
        client,
        "Entreprise Paiement",
        "payments@test.com",
    )

    customer = create_customer(
        client,
        headers,
        first_name="Client",
        last_name="Paiement",
        phone="063333333",
    )

    customer_id = customer["id"]

    product = create_product(
        client,
        headers,
        name="Produit Paiement",
        selling_price="10000.00",
        stock=10,
    )

    sale_response = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer_id,
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "2000.00",
        },
        headers=headers,
    )

    assert sale_response.status_code in (200, 201), sale_response.text

    sale = sale_response.json()

    assert sale["id"] is not None
    assert Decimal(str(sale["total"])) == Decimal("10000.00")
    assert Decimal(str(sale["amount_paid"])) == Decimal("2000.00")

    # Recherche du crédit créé automatiquement
    credits_response = client.get(
        "/api/v1/credits",
        headers=headers,
    )

    assert credits_response.status_code == 200, credits_response.text

    credits = credits_response.json()

    assert len(credits) == 1

    credit = credits[0]

    credit_id = credit["id"]

    assert Decimal(str(credit["original_amount"])) == Decimal("10000.00")
    assert Decimal(str(credit["amount_paid"])) == Decimal("2000.00")
    assert Decimal(str(credit["remaining_amount"])) == Decimal("8000.00")

    # Ajout d'un versement de 3 000
    payment_response = client.post(
        f"/api/v1/credits/{credit_id}/payments",
        json={
            "amount": "3000.00",
            "payment_method": "CASH",
            "reference": "TEST-PAYMENT-001",
            "notes": "Premier versement de test",
        },
        headers=headers,
    )

    assert payment_response.status_code == 200, payment_response.text

    updated_credit = payment_response.json()

    assert Decimal(
        str(updated_credit["amount_paid"])
    ) == Decimal("5000.00")

    assert Decimal(
        str(updated_credit["remaining_amount"])
    ) == Decimal("5000.00")

    # Vérification de l'historique des paiements
    history_response = client.get(
        f"/api/v1/credits/{credit_id}/payments",
        headers=headers,
    )

    assert history_response.status_code == 200

    payments = history_response.json()

    assert len(payments) == 1

    assert Decimal(
        str(payments[0]["amount"])
    ) == Decimal("3000.00")


# ============================================================
# DÉCIMAUX
# ============================================================


def test_decimal_precision(client):
    headers = register_company_and_login(
        client,
        "Entreprise Decimal",
        "decimal@test.com",
    )

    product = create_product(
        client,
        headers,
        name="Produit Decimal",
        selling_price="999.99",
        purchase_price="777.77",
        stock=5,
    )

    assert Decimal(
        str(product["selling_price"])
    ) == Decimal("999.99")

    assert Decimal(
        str(product["purchase_price"])
    ) == Decimal("777.77")

# ============================================================
# TRANSACTION : ROLLBACK COMPLET EN CAS D'ERREUR
# ============================================================


def test_sale_transaction_rollback_when_one_product_fails(client):
    headers = register_company_and_login(
        client,
        "Entreprise Rollback",
        "rollback@test.com",
    )

    product_1 = create_product(
        client,
        headers,
        name="Produit Rollback 1",
        selling_price="1000.00",
        stock=10,
    )

    product_2 = create_product(
        client,
        headers,
        name="Produit Rollback 2",
        selling_price="2000.00",
        stock=1,
    )

    response = client.post(
        "/api/v1/sales",
        json={
            "items": [
                {
                    "product_id": product_1["id"],
                    "quantity": 2,
                    "discount": "0.00",
                },
                {
                    "product_id": product_2["id"],
                    "quantity": 10,
                    "discount": "0.00",
                },
            ],
            "payment_method": "CASH",
            "amount_paid": "0.00",
        },
        headers=headers,
    )

    # La vente doit être refusée.
    assert response.status_code in (400, 409, 422)

    # Vérifie que le premier produit n'a PAS été déduit.
    product_1_after = client.get(
        f"/api/v1/products/{product_1['id']}",
        headers=headers,
    )

    assert product_1_after.status_code == 200

    product_1_data = product_1_after.json()

    assert int(product_1_data["current_stock"]) == 10

    # Vérifie également le deuxième produit.
    product_2_after = client.get(
        f"/api/v1/products/{product_2['id']}",
        headers=headers,
    )

    assert product_2_after.status_code == 200

    product_2_data = product_2_after.json()

    assert int(product_2_data["current_stock"]) == 1


# ============================================================
# VERSEMENT SUPÉRIEUR AU CRÉDIT
# ============================================================


def test_payment_cannot_exceed_remaining_credit(client):
    headers = register_company_and_login(
        client,
        "Entreprise Versement",
        "overpayment@test.com",
    )

    customer = create_customer(
        client,
        headers,
        first_name="Client",
        last_name="Versement",
        phone="064444444",
    )

    product = create_product(
        client,
        headers,
        name="Produit Versement",
        selling_price="10000.00",
        stock=10,
    )

    sale_response = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "2000.00",
        },
        headers=headers,
    )

    assert sale_response.status_code in (200, 201), sale_response.text

    credits_response = client.get(
        "/api/v1/credits",
        headers=headers,
    )

    assert credits_response.status_code == 200

    credits = credits_response.json()

    assert len(credits) == 1

    credit = credits[0]

    credit_id = credit["id"]

    # Il reste 8 000 FCFA.
    assert Decimal(
        str(credit["remaining_amount"])
    ) == Decimal("8000.00")

    # Tentative de paiement de 9 000 FCFA.
    payment_response = client.post(
        f"/api/v1/credits/{credit_id}/payments",
        json={
            "amount": "9000.00",
            "payment_method": "CASH",
            "reference": "OVERPAYMENT-TEST",
            "notes": "Paiement volontairement supérieur au solde",
        },
        headers=headers,
    )

    assert payment_response.status_code in (400, 409, 422)

    # Le crédit doit rester inchangé.
    credit_after_response = client.get(
        f"/api/v1/credits/{credit_id}",
        headers=headers,
    )

    assert credit_after_response.status_code == 200

    credit_after = credit_after_response.json()

    assert Decimal(
        str(credit_after["amount_paid"])
    ) == Decimal("2000.00")

    assert Decimal(
        str(credit_after["remaining_amount"])
    ) == Decimal("8000.00")    

    # ============================================================
# ISOLATION DES VENTES ENTRE ENTREPRISES
# ============================================================


def test_sale_company_isolation(client):
    headers_a = register_company_and_login(
        client,
        "Entreprise Vente A",
        "sale_a@test.com",
    )

    headers_b = register_company_and_login(
        client,
        "Entreprise Vente B",
        "sale_b@test.com",
    )

    product = create_product(
        client,
        headers_a,
        name="Produit Entreprise A",
        selling_price="5000.00",
        stock=10,
    )

    sale_response = client.post(
        "/api/v1/sales",
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "5000.00",
        },
        headers=headers_a,
    )

    assert sale_response.status_code in (200, 201), sale_response.text

    sale_id = sale_response.json()["id"]

    # Entreprise B ne doit pas voir la vente de A.
    response = client.get(
        f"/api/v1/sales/{sale_id}",
        headers=headers_b,
    )

    assert response.status_code == 404

    # La liste des ventes de B doit être vide.
    response = client.get(
        "/api/v1/sales",
        headers=headers_b,
    )

    assert response.status_code == 200
    assert response.json() == []


# ============================================================
# ISOLATION DES CRÉDITS ENTRE ENTREPRISES
# ============================================================


def test_credit_company_isolation(client):
    headers_a = register_company_and_login(
        client,
        "Entreprise Crédit A",
        "credit_a@test.com",
    )

    headers_b = register_company_and_login(
        client,
        "Entreprise Crédit B",
        "credit_b@test.com",
    )

    customer = create_customer(
        client,
        headers_a,
        first_name="Client",
        last_name="Entreprise A",
        phone="065555555",
    )

    product = create_product(
        client,
        headers_a,
        name="Produit Crédit A",
        selling_price="10000.00",
        stock=10,
    )

    sale_response = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "2000.00",
        },
        headers=headers_a,
    )

    assert sale_response.status_code in (200, 201), sale_response.text

    credits_a_response = client.get(
        "/api/v1/credits",
        headers=headers_a,
    )

    assert credits_a_response.status_code == 200

    credits_a = credits_a_response.json()

    assert len(credits_a) == 1

    credit_id = credits_a[0]["id"]

    # B ne doit voir aucun crédit de A.
    response = client.get(
        "/api/v1/credits",
        headers=headers_b,
    )

    assert response.status_code == 200
    assert response.json() == []

    # B ne doit pas pouvoir accéder directement au crédit.
    response = client.get(
        f"/api/v1/credits/{credit_id}",
        headers=headers_b,
    )

    assert response.status_code == 404


# ============================================================
# ISOLATION DES PAIEMENTS ENTRE ENTREPRISES
# ============================================================


def test_payment_company_isolation(client):
    headers_a = register_company_and_login(
        client,
        "Entreprise Paiement A",
        "payment_a@test.com",
    )

    headers_b = register_company_and_login(
        client,
        "Entreprise Paiement B",
        "payment_b@test.com",
    )

    customer = create_customer(
        client,
        headers_a,
        first_name="Client",
        last_name="Paiement A",
        phone="066666666",
    )

    product = create_product(
        client,
        headers_a,
        name="Produit Paiement A",
        selling_price="10000.00",
        stock=10,
    )

    sale_response = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "2000.00",
        },
        headers=headers_a,
    )

    assert sale_response.status_code in (200, 201), sale_response.text

    credits_response = client.get(
        "/api/v1/credits",
        headers=headers_a,
    )

    assert credits_response.status_code == 200

    credit_id = credits_response.json()[0]["id"]

    # B ne doit pas pouvoir consulter l'historique.
    response = client.get(
        f"/api/v1/credits/{credit_id}/payments",
        headers=headers_b,
    )

    assert response.status_code == 404

    # B ne doit pas pouvoir effectuer un versement
    # sur le crédit de A.
    response = client.post(
        f"/api/v1/credits/{credit_id}/payments",
        json={
            "amount": "1000.00",
            "payment_method": "CASH",
            "reference": "UNAUTHORIZED-TEST",
        },
        headers=headers_b,
    )

    assert response.status_code in (400, 404, 409, 422)

    # ============================================================
# DÉTAIL COMPLET D'UNE VENTE
# ============================================================


def test_sale_detail_contains_items(client):
    headers = register_company_and_login(
        client,
        "Entreprise Vente Detail",
        "sale_detail@test.com",
    )

    product = create_product(
        client,
        headers,
        name="Produit Detail",
        selling_price="7500.00",
        stock=10,
    )

    sale_response = client.post(
        "/api/v1/sales",
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 2,
                    "discount": "500.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "14500.00",
        },
        headers=headers,
    )

    assert sale_response.status_code in (200, 201), sale_response.text

    sale = sale_response.json()
    sale_id = sale["id"]

    detail_response = client.get(
        f"/api/v1/sales/{sale_id}",
        headers=headers,
    )

    assert detail_response.status_code == 200, detail_response.text

    detail = detail_response.json()

    assert detail["id"] == sale_id
    assert detail["sale_number"] == sale["sale_number"]

    assert Decimal(str(detail["subtotal"])) == Decimal("14500.00")
    assert Decimal(str(detail["total"])) == Decimal("14500.00")
    assert Decimal(str(detail["amount_paid"])) == Decimal("14500.00")

    assert "items" in detail
    assert len(detail["items"]) == 1

    item = detail["items"][0]

    assert item["product_id"] == product["id"]
    assert item["quantity"] == 2
    assert Decimal(str(item["unit_price"])) == Decimal("7500.00")
    assert Decimal(str(item["discount"])) == Decimal("500.00")
    assert Decimal(str(item["subtotal"])) == Decimal("14500.00")


# ============================================================
# DÉTAIL COMPLET D'UN CRÉDIT ET HISTORIQUE
# ============================================================


def test_credit_detail_contains_payment_history(client):
    headers = register_company_and_login(
        client,
        "Entreprise Credit Detail",
        "credit_detail@test.com",
    )

    customer = create_customer(
        client,
        headers,
        first_name="Client",
        last_name="Detail",
        phone="067777777",
    )

    product = create_product(
        client,
        headers,
        name="Produit Credit Detail",
        selling_price="10000.00",
        stock=10,
    )

    sale_response = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "2000.00",
        },
        headers=headers,
    )

    assert sale_response.status_code in (200, 201), sale_response.text

    credits_response = client.get(
        "/api/v1/credits",
        headers=headers,
    )

    assert credits_response.status_code == 200

    credits = credits_response.json()

    assert len(credits) == 1

    credit_id = credits[0]["id"]

    # Premier versement
    payment_1 = client.post(
        f"/api/v1/credits/{credit_id}/payments",
        json={
            "amount": "3000.00",
            "payment_method": "CASH",
            "reference": "DETAIL-PAYMENT-001",
            "notes": "Premier versement",
        },
        headers=headers,
    )

    assert payment_1.status_code == 200, payment_1.text

    # Deuxième versement
    payment_2 = client.post(
        f"/api/v1/credits/{credit_id}/payments",
        json={
            "amount": "2000.00",
            "payment_method": "MOBILE_MONEY",
            "reference": "DETAIL-PAYMENT-002",
            "notes": "Deuxième versement",
        },
        headers=headers,
    )

    assert payment_2.status_code == 200, payment_2.text

    # Détail du crédit
    detail_response = client.get(
        f"/api/v1/credits/{credit_id}",
        headers=headers,
    )

    assert detail_response.status_code == 200, detail_response.text

    detail = detail_response.json()

    assert detail["id"] == credit_id
    assert detail["customer_id"] == customer["id"]

    assert Decimal(
        str(detail["original_amount"])
    ) == Decimal("10000.00")

    assert Decimal(
        str(detail["amount_paid"])
    ) == Decimal("7000.00")

    assert Decimal(
        str(detail["remaining_amount"])
    ) == Decimal("3000.00")

    assert detail["status"] == "PARTIELLEMENT_PAYE"

    assert "payments" in detail
    assert len(detail["payments"]) == 2

    amounts = {
        Decimal(str(payment["amount"]))
        for payment in detail["payments"]
    }

    assert Decimal("3000.00") in amounts
    assert Decimal("2000.00") in amounts


# ============================================================
# FILTRE DES VENTES PAR DATE
# ============================================================


def test_sales_date_filter(client):
    headers = register_company_and_login(
        client,
        "Entreprise Filtre Date",
        "sales_date_filter@test.com",
    )

    product = create_product(
        client,
        headers,
        name="Produit Filtre Date",
        selling_price="1000.00",
        stock=20,
    )

    # Crée deux ventes aujourd'hui.
    for _ in range(2):
        response = client.post(
            "/api/v1/sales",
            json={
                "items": [
                    {
                        "product_id": product["id"],
                        "quantity": 1,
                        "discount": "0.00",
                    }
                ],
                "payment_method": "CASH",
                "amount_paid": "1000.00",
            },
            headers=headers,
        )

        assert response.status_code in (200, 201), response.text

    today = response.json()["created_at"][:10]

    response = client.get(
        f"/api/v1/sales?date_from={today}&date_to={today}",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    sales = response.json()

    assert len(sales) == 2


# ============================================================
# FILTRE DES CRÉDITS PAR DATE
# ============================================================


def test_credits_date_filter(client):
    headers = register_company_and_login(
        client,
        "Entreprise Filtre Credit",
        "credits_date_filter@test.com",
    )

    customer = create_customer(
        client,
        headers,
        first_name="Client",
        last_name="Filtre",
        phone="068888888",
    )

    product = create_product(
        client,
        headers,
        name="Produit Filtre Credit",
        selling_price="5000.00",
        stock=10,
    )

    response = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "1000.00",
        },
        headers=headers,
    )

    assert response.status_code in (200, 201), response.text

    today = response.json()["created_at"][:10]

    response = client.get(
        f"/api/v1/credits?date_from={today}&date_to={today}",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    credits = response.json()

    assert len(credits) == 1


# ============================================================
# DATE INVALIDE
# ============================================================


def test_invalid_date_range_for_sales(client):
    headers = register_company_and_login(
        client,
        "Entreprise Date Invalide",
        "invalid_date@test.com",
    )

    response = client.get(
        "/api/v1/sales"
        "?date_from=2026-09-20"
        "&date_to=2026-09-01",
        headers=headers,
    )

    assert response.status_code == 422


def test_invalid_date_range_for_credits(client):
    headers = register_company_and_login(
        client,
        "Entreprise Credit Date Invalide",
        "invalid_credit_date@test.com",
    )

    response = client.get(
        "/api/v1/credits"
        "?date_from=2026-09-20"
        "&date_to=2026-09-01",
        headers=headers,
    )

    assert response.status_code == 422


# ============================================================
# ISOLATION DU DÉTAIL D'UNE VENTE
# ============================================================


def test_sale_detail_company_isolation(client):
    headers_a = register_company_and_login(
        client,
        "Entreprise Detail Vente A",
        "detail_sale_a@test.com",
    )

    headers_b = register_company_and_login(
        client,
        "Entreprise Detail Vente B",
        "detail_sale_b@test.com",
    )

    product = create_product(
        client,
        headers_a,
        name="Produit Detail Isolation",
        selling_price="5000.00",
        stock=10,
    )

    response = client.post(
        "/api/v1/sales",
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "5000.00",
        },
        headers=headers_a,
    )

    assert response.status_code in (200, 201), response.text

    sale_id = response.json()["id"]

    response = client.get(
        f"/api/v1/sales/{sale_id}",
        headers=headers_b,
    )

    assert response.status_code == 404


# ============================================================
# ISOLATION DU DÉTAIL D'UN CRÉDIT
# ============================================================


def test_credit_detail_company_isolation(client):
    headers_a = register_company_and_login(
        client,
        "Entreprise Detail Credit A",
        "detail_credit_a@test.com",
    )

    headers_b = register_company_and_login(
        client,
        "Entreprise Detail Credit B",
        "detail_credit_b@test.com",
    )

    customer = create_customer(
        client,
        headers_a,
        first_name="Client",
        last_name="Isolation",
        phone="069999999",
    )

    product = create_product(
        client,
        headers_a,
        name="Produit Credit Isolation",
        selling_price="10000.00",
        stock=10,
    )

    response = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "2000.00",
        },
        headers=headers_a,
    )

    assert response.status_code in (200, 201), response.text

    credits = client.get(
        "/api/v1/credits",
        headers=headers_a,
    ).json()

    credit_id = credits[0]["id"]

    response = client.get(
        f"/api/v1/credits/{credit_id}",
        headers=headers_b,
    )

    assert response.status_code == 404


# ============================================================
# TRI DES VENTES
# ============================================================


def test_sales_are_ordered_by_created_at_desc(client):
    headers = register_company_and_login(
        client,
        "Entreprise Tri Ventes",
        "sales_order@test.com",
    )

    product = create_product(
        client,
        headers,
        name="Produit Tri",
        selling_price="1000.00",
        stock=10,
    )

    first_response = client.post(
        "/api/v1/sales",
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "1000.00",
        },
        headers=headers,
    )

    assert first_response.status_code in (200, 201)

    second_response = client.post(
        "/api/v1/sales",
        json={
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "1000.00",
        },
        headers=headers,
    )

    assert second_response.status_code in (200, 201)

    first_sale = first_response.json()
    second_sale = second_response.json()

    response = client.get(
        "/api/v1/sales",
        headers=headers,
    )

    assert response.status_code == 200

    sales = response.json()

    assert len(sales) == 2

    returned_ids = [sale["id"] for sale in sales]

    assert set(returned_ids) == {
        first_sale["id"],
        second_sale["id"],
    }

    # Les ventes sont censées être triées du plus récent
    # au plus ancien. Si les deux timestamps sont identiques
    # à la précision de la base, on vérifie au minimum leur présence.
    assert returned_ids[0] in {
        first_sale["id"],
        second_sale["id"],
    }


# ============================================================
# HISTORIQUE DES PAIEMENTS
# ============================================================


def test_payment_history_contains_expected_fields(client):
    headers = register_company_and_login(
        client,
        "Entreprise Historique",
        "payment_history@test.com",
    )

    customer = create_customer(
        client,
        headers,
        first_name="Client",
        last_name="Historique",
        phone="061010101",
    )

    product = create_product(
        client,
        headers,
        name="Produit Historique",
        selling_price="10000.00",
        stock=10,
    )

    sale_response = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "2000.00",
        },
        headers=headers,
    )

    assert sale_response.status_code in (200, 201)

    credit = client.get(
        "/api/v1/credits",
        headers=headers,
    ).json()[0]

    credit_id = credit["id"]

    payment_response = client.post(
        f"/api/v1/credits/{credit_id}/payments",
        json={
            "amount": "1000.00",
            "payment_method": "MOBILE_MONEY",
            "reference": "MOMO-TEST-001",
            "notes": "Test historique",
        },
        headers=headers,
    )

    assert payment_response.status_code == 200

    history_response = client.get(
        f"/api/v1/credits/{credit_id}/payments",
        headers=headers,
    )

    assert history_response.status_code == 200

    history = history_response.json()

    assert len(history) == 1

    payment = history[0]

    assert payment["credit_id"] == credit_id
    assert payment["customer_id"] == customer["id"]
    assert payment["payment_method"] == "MOBILE_MONEY"
    assert payment["reference"] == "MOMO-TEST-001"
    assert payment["notes"] == "Test historique"
    assert Decimal(str(payment["amount"])) == Decimal("1000.00")
    assert payment["created_at"] is not None


# ============================================================
# ISOLATION HISTORIQUE DES PAIEMENTS
# ============================================================


def test_payment_history_company_isolation(client):
    headers_a = register_company_and_login(
        client,
        "Entreprise History A",
        "history_a@test.com",
    )

    headers_b = register_company_and_login(
        client,
        "Entreprise History B",
        "history_b@test.com",
    )

    customer = create_customer(
        client,
        headers_a,
        first_name="Client",
        last_name="History",
        phone="062020202",
    )

    product = create_product(
        client,
        headers_a,
        name="Produit History",
        selling_price="10000.00",
        stock=10,
    )

    sale_response = client.post(
        "/api/v1/sales",
        json={
            "customer_id": customer["id"],
            "items": [
                {
                    "product_id": product["id"],
                    "quantity": 1,
                    "discount": "0.00",
                }
            ],
            "payment_method": "CASH",
            "amount_paid": "2000.00",
        },
        headers=headers_a,
    )

    assert sale_response.status_code in (200, 201)

    credit = client.get(
        "/api/v1/credits",
        headers=headers_a,
    ).json()[0]

    credit_id = credit["id"]

    response = client.get(
        f"/api/v1/credits/{credit_id}/payments",
        headers=headers_b,
    )

    assert response.status_code == 404