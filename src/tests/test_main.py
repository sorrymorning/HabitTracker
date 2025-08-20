import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api import get_db
from database import Base
from main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_temp.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_and_teardown():
    # Создаем таблицы перед тестами
    Base.metadata.create_all(bind=engine)
    yield
    # Удаляем таблицы после тестов
    Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_create_user():
    response = client.post("/users", json={"name": "Test User"})
    assert response.status_code == 200
    assert response.json()["name"] == "Test User"
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_get_users():
    # Создаем тестового пользователя
    client.post("/users", json={"name": "User1"})
    response = client.get("/users")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert response.json()[0]["name"] == "User1"


@pytest.mark.asyncio
async def test_get_user_id():
    # Создаем тестового пользователя
    create_response = client.post("/users", json={"name": "User2"})
    user_id = create_response.json()["id"]
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "User2"
    assert response.json()["id"] == user_id


@pytest.mark.asyncio
async def test_get_user_id_not_found():
    response = client.get("/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_delete_user():
    # Создаем тестового пользователя
    create_response = client.post("/users", json={"name": "User3"})
    user_id = create_response.json()["id"]
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"
    # Проверяем, что пользователь удален
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_not_found():
    response = client.delete("/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
