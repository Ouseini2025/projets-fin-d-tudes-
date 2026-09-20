from decimal import Decimal

from sqlalchemy import select

from app.models.catalog import Product
from app.models.commerce import Credit, Customer, Payment, Sale, SaleItem


def register(client, email="admin@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "company_name": "PME Commerce",
            "full_name": "Admin Commerce",
            "email": email,
            "password": "MotDePasseSolide123!",
        },
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(client, email="admin@example.com"):
    data = register(client, email)
    return {"Authorization": f"Bearer {data['access_token']}"}


def test_create_customer(client):
    headers = auth_headers(client)

    response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={
            "first_name": "Jean",
            "last_name": "Koumba",
            "phone": "060000001",
            "email": "jean@example.com",
            "address": "Pointe-Noire",
        },
    )

    assert response.status_code == 201

    body = response.json()
    assert body["first_name"] == "Jean"
    assert body["last_name"] == "Koumba"
    assert body["phone"] == "060000001"
    assert body["is_active"] is True


def test_list_customers(client):
    headers = auth_headers(client)

    client.post(
        "/api/v1/customers",
        headers=headers,
        json={
            "first_name": "Alice",
            "last_name": "Mabiala",
            "phone": "060000002",
        },
    )

    response = client.get(
        "/api/v1/customers",
        headers=headers,
    )

    assert response.status_code == 200

    customers = response.json()
    assert len(customers) == 1
    assert customers[0]["first_name"] == "Alice"


def test_customer_search(client):
    headers = auth_headers(client)

    client.post(
        "/api/v1/customers",
        headers=headers,
        json={
            "first_name": "Patrick",
            "last_name": "Ngoma",
            "phone": "060000003",
        },
    )

    response = client.get(
        "/api/v1/customers?search=Ngoma",
        headers=headers,
    )

    assert response.status_code == 200
    customers = response.json()

    assert len(customers) == 1
    assert customers[0]["last_name"] == "Ngoma"


def test_customer_can_be_deactivated(client):
    headers = auth_headers(client)

    create_response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={
            "first_name": "Client",
            "last_name": "Test",
            "phone": "060000004",
        },
    )

    customer_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/customers/{customer_id}",
        headers=headers,
    )

    assert response.status_code == 204

    detail = client.get(
        f"/api/v1/customers/{customer_id}",
        headers=headers,
    )

    assert detail.status_code == 200
    assert detail.json()["is_active"] is False