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