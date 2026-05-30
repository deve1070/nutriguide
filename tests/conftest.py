import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base, get_db
from backend.main import app

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


@pytest.fixture(scope="function", autouse=True)
def reset_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def registered_user(client):
    """Register a user and return their token + data"""
    payload = {
        "email": "fixture@nutriguide.com",
        "full_name": "Fixture User",
        "password": "fixturepassword123",
    }
    response = client.post("/auth/register", json=payload)
    data = response.json()
    return {"token": data["access_token"], "user": data["user"], "payload": payload}


@pytest.fixture
def auth_headers(registered_user):
    """Return Authorization headers for authenticated requests"""
    return {"Authorization": f"Bearer {registered_user['token']}"}
