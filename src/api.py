from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Habit, HabitLog
from pydantic import BaseModel


router = APIRouter()

class UserCreate(BaseModel):
    name: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/users")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    user = User(name=user.name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.get("/users/{id}")
def get_user_id(id:int ,db: Session = Depends(get_db)):
    user = db.get(User, id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/users/{id}")
def delete_user(id:int ,db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}




@router.post("/users/{user_id}/habits")
def create_habit_for_user(user_id: int, title: str, description: str, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    habit = Habit(user_id=user_id, title=title, description=description)
    db.add(habit)
    db.commit()
    db.refresh(habit)

    return habit


@router.get("/users/{user_id}/habits")
def get_user_habit(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    habits = db.query(Habit).filter(Habit.user_id == user_id).all()
    if not habits:
        raise HTTPException(status_code=404, detail="Привычки не найдены")

    return habits


@router.get("/habits/{habit_id}")
def get_habits_id(habit_id: int,db: Session = Depends(get_db)):
    habit = db.get(Habit, habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="User not found")
    return habit

@router.delete("/habits/{habit_id}")
def delete_habit(habit_id:int ,db: Session = Depends(get_db)):
    habit = db.query(Habit).filter(Habit.id == habit_id).first()
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    db.delete(habit)
    db.commit()
    return {"message": "Habit deleted successfully"}




@router.post("/habits/{habit_id}/log")
def create_log_habit(habit_id:int,db: Session = Depends(get_db)):
    habit = db.get(Habit, habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="User not found")

    log = HabitLog(habit_id = habit_id)
    db.add(log)
    db.commit()
    db.refresh(log)

    return log


@router.get("/habits/{habit_id}/log")
def get_log_habit(habit_id:int,db: Session = Depends(get_db)):
    habit = db.get(Habit, habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    logs = db.query(HabitLog).filter(HabitLog.habit_id == habit_id).all()
    if not logs:
        raise HTTPException(status_code=404, detail="Logs not found")

    return logs