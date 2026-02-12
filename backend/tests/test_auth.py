from tests.conftest import make_token


def test_valid_token_returns_user(client, auth_headers):
    """Authenticated request to a protected endpoint should succeed."""
    response = client.get("/api/v1/screener/passive_income", headers=auth_headers)
    # Should not be 401/403 — may be 200 or 500 depending on DB, but auth passed
    assert response.status_code not in (401, 403)


def test_missing_token_returns_403(client):
    """Request without token should be rejected by HTTPBearer (403)."""
    response = client.get("/api/v1/screener/passive_income")
    assert response.status_code == 403


def test_expired_token_returns_401(client, expired_headers):
    """Expired token should return 401."""
    response = client.get("/api/v1/screener/passive_income", headers=expired_headers)
    assert response.status_code == 401


def test_malformed_token_returns_401(client):
    """Malformed token should return 401."""
    response = client.get("/api/v1/screener/passive_income", headers={"Authorization": "Bearer not.a.valid.token"})
    assert response.status_code == 401


def test_invalid_signature_returns_401(client):
    """Token signed with wrong secret should return 401."""
    import jwt as pyjwt
    from datetime import datetime, timezone, timedelta
    token = pyjwt.encode(
        {"sub": "user-1", "email": "a@b.com", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "wrong-secret",
        algorithm="HS256",
    )
    response = client.get("/api/v1/screener/passive_income", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
