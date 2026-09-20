from app.core.security import decode_access_token, hash_password, verify_password


def register(client, email="admin@example.com", password="MotDePasseSolide123!"):
    return client.post("/api/v1/auth/register", json={
        "company_name": "PME Démo", "full_name": "Admin Démo", "email": email, "password": password,
    })


def test_creates_user_with_admin_role(client):
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["role"] == "ADMIN"
    assert body["access_token"]


def test_password_hash_is_secure():
    hashed = hash_password("MotDePasseSolide123!")
    assert hashed != "MotDePasseSolide123!"
    assert verify_password("MotDePasseSolide123!", hashed)
    assert not verify_password("incorrect", hashed)


def test_login_generates_valid_jwt(client):
    register(client)
    response = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "MotDePasseSolide123!"})
    assert response.status_code == 200
    payload = decode_access_token(response.json()["access_token"])
    assert payload["role"] == "ADMIN"
    assert payload["company_id"] == response.json()["user"]["company_id"]


def test_current_user_requires_and_accepts_valid_token(client):
    assert client.get("/api/v1/users/me").status_code == 401
    token = register(client).json()["access_token"]
    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "admin@example.com"


def test_invalid_token_is_refused(client):
    response = client.get("/api/v1/users/me", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_admin_creates_user_in_own_company(client):
    token = register(client).json()["access_token"]
    response = client.post("/api/v1/users", headers={"Authorization": f"Bearer {token}"}, json={
        "full_name": "Employé Démo", "email": "employe@example.com", "password": "MotDePasseSolide123!", "role": "EMPLOYE",
    })
    assert response.status_code == 201
    assert response.json()["role"] == "EMPLOYE"


def test_role_control_refuses_unauthorised_role():
    from types import SimpleNamespace
    from fastapi import HTTPException
    from app.api.deps import require_roles

    employee = SimpleNamespace(role=SimpleNamespace(name="EMPLOYE"))
    try:
        require_roles("ADMIN", "GERANT")(employee)
        assert False, "Un employé ne doit pas passer le contrôle ADMIN/GERANT"
    except HTTPException as error:
        assert error.status_code == 403
