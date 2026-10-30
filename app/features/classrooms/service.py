
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.features.classrooms.model import Classroom
from app.features.sessions.model import CourseSession


def get_classrooms(db: Session):
    return (
        db.query(Classroom)
        .order_by(Classroom.name)
        .all()
    )


def get_classroom(db: Session, classroom_id: int):
    classroom = db.get(Classroom, classroom_id)

    if not classroom:
        raise HTTPException(
            status_code=404,
            detail="کلاس پیدا نشد.",
        )

    return classroom


def create_classroom(db: Session, data):
    name = data.name.strip()
    address = data.address.strip()

    if not name or not address:
        raise HTTPException(
            status_code=422,
            detail="نام و آدرس کلاس الزامی هستند.",
        )

    classroom = Classroom(
        name=name,
        address=address,
        capacity=data.capacity,
        latitude=data.latitude,
        longitude=data.longitude,
    )

    db.add(classroom)
    db.commit()
    db.refresh(classroom)

    return classroom


def update_classroom(db: Session, classroom_id: int, data):
    classroom = get_classroom(db, classroom_id)

    name = data.name.strip()
    address = data.address.strip()

    if not name or not address:
        raise HTTPException(
            status_code=422,
            detail="نام و آدرس کلاس الزامی هستند.",
        )

    classroom.name = name
    classroom.address = address
    classroom.capacity = data.capacity
    classroom.latitude = data.latitude
    classroom.longitude = data.longitude

    db.commit()
    db.refresh(classroom)

    return classroom


def delete_classroom(db: Session, classroom_id: int):
    classroom = get_classroom(db, classroom_id)

    existing_sessions = (
        db.query(CourseSession)
        .filter(CourseSession.classroom_id == classroom_id)
        .first()
    )

    if existing_sessions:
        raise HTTPException(
            status_code=409,
            detail="این کلاس دارای جلسه ثبت‌شده است؛ ابتدا جلسات مربوط به آن را تعیین تکلیف کنید.",
        )

    db.delete(classroom)
    db.commit()
