
import re

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.features.sessions.model import CourseSession
from app.features.sessions.schemas import SessionPayload
from app.features.sessions.constants import WEEKDAYS
from app.features.lessons.model import Lesson
from app.features.teachers.model import Teacher
from app.features.classrooms.model import Classroom


def validate_session_data(data):
    if data.weekday not in WEEKDAYS:
        raise HTTPException(422, "روز هفته نامعتبر است.")

    time_pattern = r"^(?:[01]\d|2[0-3]):[0-5]\d$"

    if not re.match(time_pattern, data.start_time):
        raise HTTPException(422, "فرمت ساعت شروع نامعتبر است. فرمت صحیح HH:MM است.")

    if not re.match(time_pattern, data.end_time):
        raise HTTPException(422, "فرمت ساعت پایان نامعتبر است. فرمت صحیح HH:MM است.")

    if data.start_time >= data.end_time:
        raise HTTPException(422, "ساعت شروع باید قبل از ساعت پایان باشد.")


def validate_references(db: Session, data):
    if not db.get(Lesson, data.lesson_id):
        raise HTTPException(404, "درس انتخاب‌شده پیدا نشد.")

    if not db.get(Teacher, data.teacher_id):
        raise HTTPException(404, "دبیر انتخاب‌شده پیدا نشد.")

    if not db.get(Classroom, data.classroom_id):
        raise HTTPException(404, "کلاس انتخاب‌شده پیدا نشد.")


def check_conflicts(db: Session, data, exclude_session_id=None):
    query = db.query(CourseSession).filter(
        CourseSession.weekday == data.weekday,
        CourseSession.start_time < data.end_time,
        CourseSession.end_time > data.start_time,
    )

    if exclude_session_id is not None:
        query = query.filter(CourseSession.id != exclude_session_id)

    conflicts = query.all()

    for session in conflicts:
        if session.teacher_id == data.teacher_id:
            raise HTTPException(
                409,
                "این دبیر در این بازه زمانی جلسه دیگری دارد."
            )

        if session.classroom_id == data.classroom_id:
            raise HTTPException(
                409,
                "این کلاس در این بازه زمانی رزرو شده است."
            )


def get_sessions(db: Session):
    return db.query(CourseSession).order_by(
        CourseSession.weekday,
        CourseSession.start_time
    ).all()


def get_session(db: Session, session_id: int):
    session = db.get(CourseSession, session_id)

    if not session:
        raise HTTPException(404, "جلسه پیدا نشد.")

    return session


def create_session(db: Session, data: SessionPayload):
    validate_session_data(data)
    validate_references(db, data)
    check_conflicts(db, data)

    session = CourseSession(
        lesson_id=data.lesson_id,
        teacher_id=data.teacher_id,
        classroom_id=data.classroom_id,
        weekday=data.weekday,
        start_time=data.start_time,
        end_time=data.end_time,
        registered_count=data.registered_count,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def update_session(db: Session, session_id: int, data: SessionPayload):
    session = get_session(db, session_id)

    validate_session_data(data)
    validate_references(db, data)
    check_conflicts(db, data, exclude_session_id=session_id)

    session.lesson_id = data.lesson_id
    session.teacher_id = data.teacher_id
    session.classroom_id = data.classroom_id
    session.weekday = data.weekday
    session.start_time = data.start_time
    session.end_time = data.end_time
    session.registered_count = data.registered_count

    db.commit()
    db.refresh(session)

    return session


def delete_session(db: Session, session_id: int):
    session = get_session(db, session_id)

    db.delete(session)
    db.commit()
