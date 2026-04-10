"""Integration tests for authentication endpoints."""


def test_register_success(client):
    resp = client.post("/auth/register", json={
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "token" in data
    assert data["user"]["email"] == "jane@example.com"
    assert data["user"]["name"] == "Jane Doe"
    assert "id" in data["user"]


def test_register_duplicate_email(client, seed_user):
    resp = client.post("/auth/register", json={
        "name": "Duplicate",
        "email": "test@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"] == "validation failed"
    assert "email" in data["fields"]


def test_register_missing_fields(client):
    resp = client.post("/auth/register", json={"email": "x@example.com"})
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"] == "validation failed"


def test_login_success(client, seed_user):
    resp = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "password123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["user"]["email"] == "test@example.com"


def test_login_wrong_password(client, seed_user):
    resp = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "wrongpassword",
    })
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    resp = client.post("/auth/login", json={
        "email": "nobody@example.com",
        "password": "secret123",
    })
    assert resp.status_code == 401


def test_protected_endpoint_without_token(client):
    resp = client.get("/projects")
    assert resp.status_code == 403  # HTTPBearer returns 403 when no credentials
