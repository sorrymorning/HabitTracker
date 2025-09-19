import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from models import User
from utils import get_password_hash

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


@pytest.fixture
def token():
    db = TestingSessionLocal()
    user = User(name="amir", hashed_password=get_password_hash("1234"))
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    response = client.post("/auth/login", data={"username": "amir", "password": "1234"})

    return response.json()["access_token"]


def test_register_user_success():
    response = client.post("/auth/register", json={"name": "amir", "password": "1234"})
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["name"] == "amir"


def test_register_user_duplicate():
    # первый раз ок
    client.post("/auth/register", json={"name": "amir", "password": "1234"})
    # второй раз должно вернуть ошибку
    response = client.post("/auth/register", json={"name": "amir", "password": "1234"})
    assert response.status_code == 400
    assert response.json()["detail"] == "User already exists"


@pytest.mark.asyncio
async def test_get_users():
    # Создаем тестового пользователя
    client.post("/auth/register", json={"name": "amir", "password": "1234"})
    response = client.get("/users")
    assert response.status_code == 200
    assert len(response.json()) >= 1
    assert response.json()[0]["name"] == "amir"


@pytest.mark.asyncio
async def test_get_user_id():
    # Создаем тестового пользователя
    create_response = client.post(
        "/auth/register", json={"name": "amir", "password": "1234"}
    )
    user_id = create_response.json()["id"]
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "amir"
    assert response.json()["id"] == user_id


@pytest.mark.asyncio
async def test_get_user_id_not_found():
    response = client.get("/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


@pytest.mark.asyncio
async def test_delete_user():
    # Создаем тестового пользователя
    create_response = client.post(
        "/auth/register", json={"name": "amir", "password": "1234"}
    )
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


def test_create_habit(token):
    response = client.post(
        "/habits",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Test Habit", "description": "Test Desc"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Habit"
    assert "id" in data
    assert data["id"] == 1


def test_get_habits(token):
    # создаём привычку сначала
    client.post(
        "/habits",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Test Habit", "description": "Test Desc"},
    )

    response = client.get("/habits", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Test Habit"


def test_delete_habit(token):
    # создаём привычку
    res = client.post(
        "/habits",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "To Delete", "description": "Desc"},
    )
    habit_id = res.json()["id"]

    # удаляем привычку
    response = client.delete(
        f"/habits/{habit_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Habit deleted successfully"


def test_habit_access_denied_for_other_user(token):
    # создаём вторую учётку
    db = TestingSessionLocal()
    user2 = User(name="other", hashed_password=get_password_hash("4321"))
    db.add(user2)
    db.commit()
    db.refresh(user2)
    db.close()

    # создаём привычку для второго пользователя
    db = TestingSessionLocal()
    from models import Habit

    habit2 = Habit(title="Other Habit", description="Other Desc", user_id=user2.id)
    db.add(habit2)
    db.commit()
    db.refresh(habit2)
    habit2_id = habit2.id
    db.close()

    # пробуем получить чужую привычку
    response = client.get(
        f"/habits/{habit2_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_create_log_habit(token):
    # сначала создаём привычку
    response = client.post(
        "/habits",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Morning Run", "description": "Run 5km"},
    )
    assert response.status_code == 200
    habit = response.json()
    habit_id = habit["id"]

    # теперь создаём лог
    response = client.post(
        f"/habits/{habit_id}/log", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    log = response.json()
    assert log["habit_id"] == habit_id
    assert log["id"] == 1


def test_get_log_habit(token):
    # создаём привычку
    response = client.post(
        "/habits",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Read Book", "description": "Read 10 pages"},
    )
    assert response.status_code == 200
    habit = response.json()
    habit_id = habit["id"]

    # создаём лог
    client.post(f"/habits/{habit_id}/log", headers={"Authorization": f"Bearer {token}"})

    # получаем логи
    response = client.get(
        f"/habits/{habit_id}/log", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    logs = response.json()

    # проверяем, что лог существует
    assert len(logs) == 1
    assert logs[0]["habit_id"] == habit_id


def test_get_daily_summary(token):
    # создаём привычку
    client.post(
        "/habits",
        headers={"Authorization": f"Bearer {token}"},
        json={"title": "Test Habit", "description": "Test Desc"},
    )

    # отмечаем её выполненной (создаём лог)
    client.post("/habits/1/log", headers={"Authorization": f"Bearer {token}"})

    # получаем дневной отчёт
    response = client.get(
        "/summary/daily-summary", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # проверяем ключи
    assert "date" in data
    assert "total_habits" in data
    assert "completed" in data
    assert "not_completed" in data
    assert "percent" in data
    assert "habits" in data
    assert "done_habits" in data

    # проверяем корректность
    assert data["total_habits"] == 1
    assert data["completed"] == 1
    assert data["not_completed"] == 0
    assert data["percent"] == 100
    assert "Test Habit" in data["habits"]
    assert "Test Habit" in data["done_habits"]
