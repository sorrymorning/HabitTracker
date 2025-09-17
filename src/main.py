from fastapi import APIRouter, FastAPI

from api import auth, habits, summary, users
from database import Base, engine

app = FastAPI()
router = APIRouter()

Base.metadata.create_all(bind=engine)

app.include_router(users.router)
app.include_router(habits.router)
app.include_router(auth.router)
app.include_router(summary.router)
