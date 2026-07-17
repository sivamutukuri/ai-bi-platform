"""Integration tests for authentication endpoints."""


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_and_login(client):
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": "a@b.com", "password": "password123", "full_name": "A"},
    )
    assert reg.status_code == 201
    assert reg.json()["email"] == "a@b.com"

    login = client.post(
        "/api/v1/auth/login",
        data={"username": "a@b.com", "password": "password123"},
    )
    assert login.status_code == 200
    body = login.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_duplicate_registration_rejected(client):
    payload = {"email": "dup@b.com", "password": "password123"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_login_wrong_password(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "c@b.com", "password": "password123"},
    )
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "c@b.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401


def test_me_requires_auth(client):
    assert client.get("/api/v1/auth/me").status_code == 401


def test_me_returns_current_user(client, auth_headers):
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "tester@example.com"


def test_refresh_token_flow(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "r@b.com", "password": "password123"},
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "r@b.com", "password": "password123"},
    )
    refresh = login.json()["refresh_token"]
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
