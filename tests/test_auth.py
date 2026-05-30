import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.main import app
from backend.database import Base, get_db

# ── In-memory SQLite for tests (no Postgres needed) ───
TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)

REGISTER_PAYLOAD = {
    "email": "test@nutriguide.com",
    "full_name": "Test User",
    "password": "securepassword123",
}


def test_register_success():
    response = client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == REGISTER_PAYLOAD["email"]
    assert data["user"]["role"] == "patient"


def test_register_duplicate_email():
    client.post("/auth/register", json=REGISTER_PAYLOAD)
    response = client.post("/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 409


def test_register_weak_password():
    response = client.post(
        "/auth/register", json={**REGISTER_PAYLOAD, "password": "short"}
    )
    assert response.status_code == 422


def test_login_success():
    client.post("/auth/register", json=REGISTER_PAYLOAD)
    response = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": REGISTER_PAYLOAD["password"],
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_wrong_password():
    client.post("/auth/register", json=REGISTER_PAYLOAD)
    response = client.post(
        "/auth/login",
        json={
            "email": REGISTER_PAYLOAD["email"],
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401


def test_get_me_authenticated():
    reg = client.post("/auth/register", json=REGISTER_PAYLOAD)
    token = reg.json()["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == REGISTER_PAYLOAD["email"]


def test_get_me_unauthenticated():
    response = client.get("/auth/me")
    assert response.status_code == 403
