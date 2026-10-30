
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.features.teachers.model import Teacher
from app.features.sessions.model import CourseSession


def get_teachers(db: Session):
    return (
        db.query(Teacher)
        .order_by(Teacher.first_name, Teacher.last_name)
        .all()
    )


def get_teacher(db: Session, teacher_id: int):
    teacher = db.get(Teacher, teacher_id)

    if not teacher:
        raise HTTPException(
            status_code=404,
            detail="دبیر پیدا نشد.",
        )

    return teacher


def create_teacher(db: Session, data):
    first_name = data.first_name.strip()
    last_name = data.last_name.strip()
    phone = data.phone.strip()

    if not first_name or not last_name or not phone:
        raise HTTPException(
            status_code=422,
            detail="نام، نام خانوادگی و شماره تماس الزامی هستند.",
        )

    teacher = Teacher(
        first_name=first_name,
        last_name=last_name,
        phone=phone,
        photo=data.photo,
    )

    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return teacher


def update_teacher(db: Session, teacher_id: int, data):
    teacher = get_teacher(db, teacher_id)

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

    return teacher


def delete_teacher(db: Session, teacher_id: int):
    teacher = get_teacher(db, teacher_id)

    existing_sessions = (
        db.query(CourseSession)
        .filter(CourseSession.teacher_id == teacher_id)
        .first()
    )

    if existing_sessions:
        raise HTTPException(
            status_code=409,
            detail="این دبیر دارای جلسه ثبت‌شده است؛ ابتدا جلسات او را تعیین تکلیف کنید.",
        )

    db.delete(teacher)
    db.commit()
