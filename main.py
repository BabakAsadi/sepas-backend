
from datetime import datetime

from fastapi import Header, FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

import models
from database import Base, engine, get_db
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

if not ADMIN_PASSWORD:
    raise RuntimeError("ADMIN_PASSWORD is missing from backend .env")

Base.metadata.create_all(bind=engine)

def verify_admin_password(
    x_admin_password: str = Header(...)
):
    if not secrets.compare_digest(
        x_admin_password,
        ADMIN_PASSWORD,
    ):
        raise HTTPException(
            status_code=401,
            detail="رمز مدیریت نادرست است",
        )

    return True


app = FastAPI(
    title="Sepas Academy API",
    description="API مدیریت آموزشگاه سپاس",
    version="1.0.0",
)

# اجازه ارتباط React با FastAPI
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

WEEKDAYS = [
    "شنبه",
    "یکشنبه",
    "دوشنبه",
    "سه‌شنبه",
    "چهارشنبه",
    "پنجشنبه",
    "جمعه",
]


class SessionPayload(BaseModel):
    lesson_id: int = Field(gt=0)
    teacher_id: int = Field(gt=0)
    classroom_id: int = Field(gt=0)
    weekday: str
    start_time: str
    end_time: str
    registered_count: int = Field(default=0, ge=0)


class TeacherPayload(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=30)
    photo: str | None = None



def validate_payload(data: SessionPayload):
    if data.weekday not in WEEKDAYS:
        raise HTTPException(
            status_code=422,
            detail="روز هفته معتبر نیست.",
        )

    try:
        start = datetime.strptime(data.start_time, "%H:%M")
        end = datetime.strptime(data.end_time, "%H:%M")
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="ساعت باید با قالب HH:MM باشد؛ مانند 16:30.",
        )

    if start.strftime("%H:%M") != data.start_time:
        raise HTTPException(
            status_code=422,
            detail="فرمت ساعت شروع معتبر نیست.",
        )

    if end.strftime("%H:%M") != data.end_time:
        raise HTTPException(
            status_code=422,
            detail="فرمت ساعت پایان معتبر نیست.",
        )

    if data.start_time >= data.end_time:
        raise HTTPException(
            status_code=422,
            detail="ساعت پایان باید بعد از ساعت شروع باشد.",
        )


def validate_references(data: SessionPayload, db: Session):
    if not db.get(models.Lesson, data.lesson_id):
        raise HTTPException(status_code=404, detail="درس پیدا نشد.")

    if not db.get(models.Teacher, data.teacher_id):
        raise HTTPException(status_code=404, detail="مدرس پیدا نشد.")

    if not db.get(models.Classroom, data.classroom_id):
        raise HTTPException(status_code=404, detail="کلاس پیدا نشد.")


def check_conflicts(
    data: SessionPayload,
    db: Session,
    exclude_id: int | None = None,
):
    sessions = (
        db.query(models.CourseSession)
        .filter(models.CourseSession.weekday == data.weekday)
        .all()
    )

    for existing in sessions:
        if existing.id == exclude_id:
            continue

        # اگر بازه‌های زمانی هم‌پوشانی نداشته باشند، مشکلی نیست.
        overlaps = (
            data.start_time < existing.end_time
            and data.end_time > existing.start_time
        )

        if not overlaps:
            continue

        if existing.teacher_id == data.teacher_id:
            raise HTTPException(
                status_code=409,
                detail="این مدرس در این ساعت جلسه دیگری دارد.",
            )

        if existing.classroom_id == data.classroom_id:
            raise HTTPException(
                status_code=409,
                detail="این کلاس در این ساعت رزرو شده است.",
            )


def session_to_dict(item: models.CourseSession, db: Session):
    lesson = db.get(models.Lesson, item.lesson_id)
    teacher = db.get(models.Teacher, item.teacher_id)
    classroom = db.get(models.Classroom, item.classroom_id)

    return {
        "id": item.id,
        "lesson_id": item.lesson_id,
        "lesson_name": lesson.name,
        "grade": lesson.grade,
        "field": lesson.field,
        "teacher_id": item.teacher_id,
        "teacher_name": f"{teacher.first_name} {teacher.last_name}",
        "classroom_id": item.classroom_id,
        "classroom_name": classroom.name,
        "weekday": item.weekday,
        "start_time": item.start_time,
        "end_time": item.end_time,
        "registered_count": item.registered_count,
    }


@app.get("/")
def home():
    return {"message": "Academy API is running!"}


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


# دریافت اطلاعات موردنیاز فرم React

@app.get("/api/lessons")
def get_lessons(db: Session = Depends(get_db)):
    items = db.query(models.Lesson).order_by(
        models.Lesson.grade,
        models.Lesson.name,
    ).all()

    return [
        {
            "id": x.id,
            "name": x.name,
            "grade": x.grade,
            "field": x.field,
        }
        for x in items
    ]


@app.get("/api/teachers")
def get_teachers(db: Session = Depends(get_db)):
    items = db.query(models.Teacher).order_by(
        models.Teacher.first_name,
        models.Teacher.last_name,
    ).all()

    return [
        {
            "id": x.id,
            "first_name": x.first_name,
            "last_name": x.last_name,
            "phone": x.phone,
            "photo": x.photo,
        }
        for x in items
    ]




# مشاهده جزئیات یک دبیر

@app.get("/api/teachers/{teacher_id}")
def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
):
    teacher = db.get(models.Teacher, teacher_id)

    if not teacher:
        raise HTTPException(
            status_code=404,
            detail="دبیر پیدا نشد.",
        )

    return {
        "id": teacher.id,
        "first_name": teacher.first_name,
        "last_name": teacher.last_name,
        "phone": teacher.phone,
        "photo": teacher.photo,
    }


# افزودن دبیر جدید

@app.post("/api/teachers", status_code=201)
def create_teacher(
    data: TeacherPayload,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    teacher = models.Teacher(
        first_name=data.first_name.strip(),
        last_name=data.last_name.strip(),
        phone=data.phone.strip(),
        photo=data.photo,
    )

    if not teacher.first_name or not teacher.last_name or not teacher.phone:
        raise HTTPException(
            status_code=422,
            detail="نام، نام خانوادگی و شماره تماس الزامی هستند.",
        )

    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return {
        "id": teacher.id,
        "first_name": teacher.first_name,
        "last_name": teacher.last_name,
        "phone": teacher.phone,
        "photo": teacher.photo,
    }


# ویرایش اطلاعات دبیر

@app.put("/api/teachers/{teacher_id}")
def update_teacher(
    teacher_id: int,
    data: TeacherPayload,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    teacher = db.get(models.Teacher, teacher_id)

    if not teacher:
        raise HTTPException(
            status_code=404,
            detail="دبیر پیدا نشد.",
        )

    first_name = data.first_name.strip()
    last_name = data.last_name.strip()
    phone = data.phone.strip()

    if not first_name or not last_name or not phone:
        raise HTTPException(
            status_code=422,
            detail="نام، نام خانوادگی و شماره تماس الزامی هستند.",
        )

    teacher.first_name = first_name
    teacher.last_name = last_name
    teacher.phone = phone
    teacher.photo = data.photo

    db.commit()
    db.refresh(teacher)

    return {
        "id": teacher.id,
        "first_name": teacher.first_name,
        "last_name": teacher.last_name,
        "phone": teacher.phone,
        "photo": teacher.photo,
    }


# حذف دبیر

@app.delete("/api/teachers/{teacher_id}")
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    teacher = db.get(models.Teacher, teacher_id)

    if not teacher:
        raise HTTPException(
            status_code=404,
            detail="دبیر پیدا نشد.",
        )

    existing_sessions = (
        db.query(models.CourseSession)
        .filter(models.CourseSession.teacher_id == teacher_id)
        .first()
    )

    if existing_sessions:
        raise HTTPException(
            status_code=409,
            detail="این دبیر دارای جلسه ثبت‌شده است؛ ابتدا جلسات او را تعیین تکلیف کنید.",
        )

    db.delete(teacher)
    db.commit()

    return {"message": "دبیر با موفقیت حذف شد."}




@app.get("/api/classrooms")
def get_classrooms(db: Session = Depends(get_db)):
    items = db.query(models.Classroom).order_by(
        models.Classroom.name
    ).all()

    return [
        {
            "id": x.id,
            "name": x.name,
            "address": x.address,
            "capacity": x.capacity,
        }
        for x in items
    ]


@app.get("/api/weekdays")
def get_weekdays():
    return WEEKDAYS


# مشاهده برنامه هفتگی

@app.get("/api/sessions")
def get_sessions(db: Session = Depends(get_db)):
    items = db.query(models.CourseSession).all()

    weekday_order = {day: i for i, day in enumerate(WEEKDAYS)}

    items.sort(
        key=lambda x: (
            weekday_order.get(x.weekday, 99),
            x.start_time,
        )
    )

    return [session_to_dict(x, db) for x in items]


@app.get("/api/sessions/{session_id}")
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    item = db.get(models.CourseSession, session_id)

    if not item:
        raise HTTPException(status_code=404, detail="جلسه پیدا نشد.")

    return session_to_dict(item, db)


# ثبت جلسه جدید

@app.post("/api/sessions", status_code=201)
def create_session(
    data: SessionPayload,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    validate_payload(data)
    validate_references(data, db)
    check_conflicts(data, db)

    item = models.CourseSession(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)

    return session_to_dict(item, db)


# ویرایش کامل اطلاعات جلسه

@app.put("/api/sessions/{session_id}")
def update_session(
    session_id: int,
    data: SessionPayload,
    db: Session = Depends(get_db),
     _admin=Depends(verify_admin_password),
):
    item = db.get(models.CourseSession, session_id)

    if not item:
        raise HTTPException(status_code=404, detail="جلسه پیدا نشد.")

    validate_payload(data)
    validate_references(data, db)
    check_conflicts(data, db, exclude_id=session_id)

    for key, value in data.model_dump().items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)

    return session_to_dict(item, db)


# حذف جلسه

@app.delete("/api/sessions/{session_id}")
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
     _admin=Depends(verify_admin_password),
):
    item = db.get(models.CourseSession, session_id)

    if not item:
        raise HTTPException(status_code=404, detail="جلسه پیدا نشد.")

    db.delete(item)
    db.commit()

    return {"message": "جلسه با موفقیت حذف شد."}


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