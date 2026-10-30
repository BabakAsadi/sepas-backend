
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.features.lessons.model import Lesson
from app.features.sessions.model import CourseSession


def get_lessons(db: Session):
    return (
        db.query(Lesson)
        .order_by(Lesson.grade, Lesson.name)
        .all()
    )


def get_lesson(db: Session, lesson_id: int):
    lesson = db.get(Lesson, lesson_id)

    if not lesson:
        raise HTTPException(
            status_code=404,
            detail="درس پیدا نشد.",
        )

    return lesson


def create_lesson(db: Session, data):
    name = data.name.strip()
    grade = data.grade.strip()
    field = data.field.strip()

    if not name or not grade or not field:
        raise HTTPException(
            status_code=422,
            detail="نام درس، پایه و رشته الزامی هستند.",
        )

    lesson = Lesson(
        name=name,
        grade=grade,
        field=field,
    )

    db.add(lesson)
    db.commit()
    db.refresh(lesson)

    return lesson


def update_lesson(db: Session, lesson_id: int, data):
    lesson = get_lesson(db, lesson_id)

    name = data.name.strip()
    grade = data.grade.strip()
    field = data.field.strip()

    if not name or not grade or not field:
        raise HTTPException(
            status_code=422,
            detail="نام درس، پایه و رشته الزامی هستند.",
        )

    lesson.name = name
    lesson.grade = grade
    lesson.field = field

    db.commit()
    db.refresh(lesson)

    return lesson


def delete_lesson(db: Session, lesson_id: int):
    lesson = get_lesson(db, lesson_id)

    existing_sessions = (
        db.query(CourseSession)
        .filter(CourseSession.lesson_id == lesson_id)
        .first()
    )

    if existing_sessions:
        raise HTTPException(
            status_code=409,
            detail="این درس دارای جلسه ثبت‌شده است؛ ابتدا جلسات مربوط به آن را تعیین تکلیف کنید.",
        )

    db.delete(lesson)
    db.commit()
