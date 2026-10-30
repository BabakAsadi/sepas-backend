
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
import app.database.models

from app.features.teachers.router import router as teachers_router
from app.features.lessons.router import router as lessons_router
from app.features.classrooms.router import router as classrooms_router
from app.features.sessions.router import router as sessions_router
from pydantic import BaseModel
from app.core.config import ADMIN_PASSWORD
import secrets

app = FastAPI(
    title="Sepas Academy API",
    description="API مدیریت آموزشگاه سپاس",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register feature routers
app.include_router(teachers_router)
app.include_router(lessons_router)
app.include_router(classrooms_router)
app.include_router(sessions_router)


@app.get("/")
def root():
    return {"message": "Sepas Academy API is running"}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/weekdays")
def get_weekdays():
    from app.features.sessions.constants import WEEKDAYS
    return WEEKDAYS

class AdminLoginPayload(BaseModel):
    password: str

@app.post("/api/admin/login")
def admin_login(payload: AdminLoginPayload):
    if not secrets.compare_digest(
        payload.password,
        ADMIN_PASSWORD,
    ):
        raise HTTPException(
            status_code=401,
            detail="رمز مدیریت نادرست است",
        )

    return {"success": True}

# Create database tables if they do not exist
Base.metadata.create_all(bind=engine)
