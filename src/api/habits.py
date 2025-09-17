from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Habit, HabitCreate, HabitLog, User

from .auth import get_current_user

router = APIRouter(prefix="/habits", tags=["habits"])


@router.post("/")
def create_habit(
    habit: HabitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_habit = Habit(
        title=habit.title, description=habit.description, user_id=current_user.id
    )
    db.add(new_habit)
    db.commit()
    db.refresh(new_habit)
    return new_habit


@router.get("/")
def get_habits(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    habits = db.query(Habit).filter(Habit.user_id == current_user.id).all()
    return habits


@router.get("/{habit_id}")
def get_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == current_user.id)
        .first()
    )
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    return habit


@router.delete("/{habit_id}")
def delete_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == current_user.id)
        .first()
    )
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")
    db.delete(habit)
    db.commit()
    return {"message": "Habit deleted successfully"}


@router.post("/{habit_id}/log")
def create_log_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == current_user.id)
        .first()
    )
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    log = HabitLog(habit_id=habit.id)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/{habit_id}/log")
def get_log_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == current_user.id)
        .first()
    )
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    logs = db.query(HabitLog).filter(HabitLog.habit_id == habit.id).all()
    return logs
