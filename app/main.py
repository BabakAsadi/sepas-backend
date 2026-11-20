
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.features.teachers.router import router as teachers_router
from app.features.lessons.router import router as lessons_router
from app.features.classrooms.router import router as classrooms_router
from app.features.sessions.router import router as sessions_router
from app.features.students.router import router as students_router
from app.features.courses.router import router as courses_router
from app.features.course_schedules.router import router as course_schedules_router
from app.features.course_occurrences.router import router as course_occurrences_router
from app.features.course_enrollments.router import router as course_enrollments_router
from app.features.wallets.router import router as wallets_router
from app.features.reports.router import router as reports_router
from app.features.auth.router import router as auth_router

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
app.include_router(auth_router)
app.include_router(teachers_router)
app.include_router(lessons_router)
app.include_router(classrooms_router)
app.include_router(sessions_router)
app.include_router(students_router)
app.include_router(courses_router)
app.include_router(course_schedules_router)
app.include_router(course_occurrences_router)
app.include_router(course_enrollments_router)
app.include_router(wallets_router)
app.include_router(reports_router)


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

