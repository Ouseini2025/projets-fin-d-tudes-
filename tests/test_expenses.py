from datetime import date, timedelta
from tests.test_commerce import register_company_and_login


def test_create_expense(client):
    headers = register_company_and_login(
        client,
        "Entreprise Depenses",
        "expense_create@test.com",
    )

    response = client.post(
        "/api/v1/expenses",
        json={
            "category": "ELECTRICITE",
            "amount": "25000.00",
            "description": "Facture d'électricité",
            "expense_date": date.today().isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text

    expense = response.json()

    assert expense["category"] == "ELECTRICITE"
    assert expense["amount"] == "25000.00"
    assert expense["description"] == "Facture d'électricité"


def test_list_expenses(client):
    headers = register_company_and_login(
        client,
        "Entreprise Liste Depenses",
        "expense_list@test.com",
    )

    for category, amount in [
        ("LOYER", "100000.00"),
        ("TRANSPORT", "15000.00"),
    ]:
        response = client.post(
            "/api/v1/expenses",
            json={
                "category": category,
                "amount": amount,
                "expense_date": date.today().isoformat(),
            },
            headers=headers,
        )

        assert response.status_code == 200, response.text

    response = client.get(
        "/api/v1/expenses",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    expenses = response.json()

    assert len(expenses) == 2


def test_get_expense(client):
    headers = register_company_and_login(
        client,
        "Entreprise Detail Depense",
        "expense_detail@test.com",
    )

    response = client.post(
        "/api/v1/expenses",
        json={
            "category": "INTERNET",
            "amount": "12000.00",
            "description": "Abonnement internet",
            "expense_date": date.today().isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text

    expense_id = response.json()["id"]

    response = client.get(
        f"/api/v1/expenses/{expense_id}",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    expense = response.json()

    assert expense["id"] == expense_id
    assert expense["category"] == "INTERNET"


def test_update_expense(client):
    headers = register_company_and_login(
        client,
        "Entreprise Update Depense",
        "expense_update@test.com",
    )

    response = client.post(
        "/api/v1/expenses",
        json={
            "category": "TRANSPORT",
            "amount": "10000.00",
            "expense_date": date.today().isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text

    expense_id = response.json()["id"]

    response = client.patch(
        f"/api/v1/expenses/{expense_id}",
        json={
            "category": "MAINTENANCE",
            "amount": "18000.00",
            "description": "Réparation équipement",
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text

    expense = response.json()

    assert expense["category"] == "MAINTENANCE"
    assert expense["amount"] == "18000.00"
    assert expense["description"] == "Réparation équipement"


def test_delete_expense(client):
    headers = register_company_and_login(
        client,
        "Entreprise Delete Depense",
        "expense_delete@test.com",
    )

    response = client.post(
        "/api/v1/expenses",
        json={
            "category": "AUTRE",
            "amount": "5000.00",
            "expense_date": date.today().isoformat(),
        },
        headers=headers,
    )

    assert response.status_code == 200, response.text

    expense_id = response.json()["id"]

    response = client.delete(
        f"/api/v1/expenses/{expense_id}",
        headers=headers,
    )

    assert response.status_code == 204, response.text

    response = client.get(
        f"/api/v1/expenses/{expense_id}",
        headers=headers,
    )

    assert response.status_code == 404


def test_expenses_category_filter(client):
    headers = register_company_and_login(
        client,
        "Entreprise Filtre Categorie",
        "expense_category_filter@test.com",
    )

    for category in ["LOYER", "LOYER", "TRANSPORT"]:
        response = client.post(
            "/api/v1/expenses",
            json={
                "category": category,
                "amount": "10000.00",
                "expense_date": date.today().isoformat(),
            },
            headers=headers,
        )

        assert response.status_code == 200, response.text

    response = client.get(
        "/api/v1/expenses?category=LOYER",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    expenses = response.json()

    assert len(expenses) == 2
    assert all(expense["category"] == "LOYER" for expense in expenses)


def test_expenses_date_filter(client):
    headers = register_company_and_login(
        client,
        "Entreprise Filtre Date Depense",
        "expense_date_filter@test.com",
    )

    yesterday = date.today() - timedelta(days=1)
    today = date.today()

    for expense_date, amount in [
        (yesterday, "10000.00"),
        (today, "20000.00"),
    ]:
        response = client.post(
            "/api/v1/expenses",
            json={
                "category": "AUTRE",
                "amount": amount,
                "expense_date": expense_date.isoformat(),
            },
            headers=headers,
        )

        assert response.status_code == 200, response.text

    response = client.get(
        f"/api/v1/expenses?date_from={today.isoformat()}&date_to={today.isoformat()}",
        headers=headers,
    )

    assert response.status_code == 200, response.text

    expenses = response.json()

    assert len(expenses) == 1
    assert expenses[0]["amount"] == "20000.00"


def test_expense_company_isolation(client):
    headers_a = register_company_and_login(
        client,
        "Entreprise Depense A",
        "expense_company_a@test.com",
    )

    headers_b = register_company_and_login(
        client,
        "Entreprise Depense B",
        "expense_company_b@test.com",
    )

    response = client.post(
        "/api/v1/expenses",
        json={
            "category": "MARKETING",
            "amount": "30000.00",
            "expense_date": date.today().isoformat(),
        },
        headers=headers_a,
    )

    assert response.status_code == 200, response.text

    expense_id = response.json()["id"]

    response = client.get(
        "/api/v1/expenses",
        headers=headers_b,
    )

    assert response.status_code == 200, response.text
    assert response.json() == []

    response = client.get(
        f"/api/v1/expenses/{expense_id}",
        headers=headers_b,
    )

    assert response.status_code == 404