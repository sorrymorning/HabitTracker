from datetime import date, datetime

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from database import get_db
from image import generate_end_of_day_image
from models import Habit, HabitLog, User

from .auth import get_current_user

router = APIRouter(prefix="/summary", tags=["summary"])


def get_daily_summary(db: Session, user_id: int, summary_date: date = None):
    if summary_date is None:
        summary_date = date.today()

    # все привычки пользователя
    habits = db.query(Habit).filter(Habit.user_id == user_id).all()
    total = len(habits)

    # все логи за конкретный день
    logs = (
        db.query(HabitLog)
        .join(Habit)
        .filter(
            Habit.user_id == user_id,
            HabitLog.date >= datetime.combine(summary_date, datetime.min.time()),
            HabitLog.date <= datetime.combine(summary_date, datetime.max.time()),
        )
        .all()
    )
    done = len(logs)

    return {
        "date": summary_date.isoformat(),
        "total_habits": total,
        "completed": done,
        "not_completed": total - done,
        "percent": round((done / total * 100), 2) if total > 0 else 0,
        "habits": [h.title for h in habits],
        "done_habits": [l.habit.title for l in logs],
    }


@router.get("/daily-summary/image")
def get_daily_summary_image(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    summary = get_daily_summary(db, current_user.id)
    path = generate_end_of_day_image(summary, f"summary_{current_user.id}.png")
    return FileResponse(path, media_type="image/png")
