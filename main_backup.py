
from fastapi import FastAPI

import models
from database import Base, engine

# ایجاد جدول‌ها در صورت نبودن
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sepas Academy API",
    description="API مدیریت آموزشگاه",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Academy API is running!"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "ok"
    }
