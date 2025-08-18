from fastapi import FastAPI
from database import Base, engine
from api import router

app = FastAPI()


Base.metadata.create_all(bind=engine)

app.include_router(router)
