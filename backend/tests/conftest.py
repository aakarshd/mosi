import jwt
import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


TEST_USER = {"user_id": "test-user-001", "email": "test@mosi.dev"}


def make_token(user: dict = TEST_USER, expired: bool = False) -> str:
    payload = {
        "sub": user["user_id"],
        "email": user["email"],
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + (timedelta(seconds=-1) if expired else timedelta(hours=1)),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth_headers():
    token = make_token()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def expired_headers():
    token = make_token(expired=True)
    return {"Authorization": f"Bearer {token}"}
