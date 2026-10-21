from decimal import Decimal

from tests.test_commerce import register_company_and_login


def test_dashboard_empty(client):
    headers = register_company_and_login(
        client,
        "Dashboard Company",
        "dashboard@example.com",
    )

    response = client.get(
        "/api/v1/dashboard",
        headers=headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert Decimal(data["total_sales"]) == Decimal("0.00")
    assert Decimal(data["total_expenses"]) == Decimal("0.00")
    assert Decimal(data["net_result"]) == Decimal("0.00")
    assert data["sales_count"] == 0
    assert Decimal(data["average_sale"]) == Decimal("0.00")
    assert Decimal(data["total_paid"]) == Decimal("0.00")
    assert Decimal(data["total_receivables"]) == Decimal("0.00")
    assert Decimal(data["overdue_receivables"]) == Decimal("0.00")
    assert data["active_credits"] == 0
    assert Decimal(data["stock_value"]) == Decimal("0.00")
    assert data["low_stock_products"] == 0
    assert data["out_of_stock_products"] == 0


def test_dashboard_requires_authentication(client):
    response = client.get("/api/v1/dashboard")

    assert response.status_code == 401


def test_dashboard_rejects_invalid_date_range(client):
    headers = register_company_and_login(
        client,
        "Date Company",
        "date-dashboard@example.com",
    )

    response = client.get(
        "/api/v1/dashboard?date_from=2026-09-20&date_to=2026-09-01",
        headers=headers,
    )

    assert response.status_code == 400
    assert "date" in response.json()["detail"].lower()


def test_dashboard_company_isolation(client):
    headers_a = register_company_and_login(
        client,
        "Company A",
        "dashboard-a@example.com",
    )

    headers_b = register_company_and_login(
        client,
        "Company B",
        "dashboard-b@example.com",
    )

    response_a = client.get(
        "/api/v1/dashboard",
        headers=headers_a,
    )

    response_b = client.get(
        "/api/v1/dashboard",
        headers=headers_b,
    )

    assert response_a.status_code == 200
    assert response_b.status_code == 200

    assert response_a.json()["total_sales"] == "0.00"
    assert response_b.json()["total_sales"] == "0.00"
    assert response_a.json()["revenue_by_month"] == []
    assert response_b.json()["revenue_by_month"] == []


def test_dashboard_revenue_by_month_aggregation_and_isolation(client):
    headers_a = register_company_and_login(
        client,
        "Monthly Company A",
        "monthly-a@example.com",
    )
    headers_b = register_company_and_login(
        client,
        "Monthly Company B",
        "monthly-b@example.com",
    )

    # 1. Création d'un produit et stock pour l'entreprise A
    prod_resp = client.post(
        "/api/v1/products",
        headers=headers_a,
        json={
            "name": "Produit Mensuel",
            "selling_price": "1000.00",
            "purchase_price": "600.00",
            "current_stock": 50,
            "minimum_stock": 5,
        },
    )
    assert prod_resp.status_code == 201
    prod_id = prod_resp.json()["id"]

    # 2. Vente 1 pour l'entreprise A
    sale_resp1 = client.post(
        "/api/v1/sales",
        headers=headers_a,
        json={
            "items": [{"product_id": prod_id, "quantity": 2, "discount": "0.00"}],
            "discount": "0.00",
            "payment_method": "CASH",
            "amount_paid": "2000.00",
        },
    )
    assert sale_resp1.status_code == 201

    # 3. Vente 2 pour l'entreprise A
    sale_resp2 = client.post(
        "/api/v1/sales",
        headers=headers_a,
        json={
            "items": [{"product_id": prod_id, "quantity": 1, "discount": "0.00"}],
            "discount": "0.00",
            "payment_method": "CASH",
            "amount_paid": "1000.00",
        },
    )
    assert sale_resp2.status_code == 201

    # 4. Vérification dashboard entreprise A
    dash_a = client.get("/api/v1/dashboard", headers=headers_a)
    assert dash_a.status_code == 200
    data_a = dash_a.json()
    assert Decimal(data_a["total_sales"]) == Decimal("3000.00")
    assert len(data_a["revenue_by_month"]) == 1
    point = data_a["revenue_by_month"][0]
    assert "month" in point
    assert Decimal(point["revenue"]) == Decimal("3000.00")

    # 5. Vérification isolation entreprise B
    dash_b = client.get("/api/v1/dashboard", headers=headers_b)
    assert dash_b.status_code == 200
    data_b = dash_b.json()
    assert Decimal(data_b["total_sales"]) == Decimal("0.00")
    assert data_b["revenue_by_month"] == []