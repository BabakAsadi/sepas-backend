
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.shared.dependencies import get_db
from app.core.security import verify_admin_password

from app.features.lessons.schemas import LessonPayload
from app.features.lessons import service


router = APIRouter(
    prefix="/api/lessons",
    tags=["Lessons"],
)


def lesson_to_dict(lesson):
    return {
        "id": lesson.id,
        "name": lesson.name,
        "grade": lesson.grade,
        "field": lesson.field,
    }


@router.get("")
def get_lessons(db: Session = Depends(get_db)):
    items = service.get_lessons(db)
    return [lesson_to_dict(item) for item in items]


@router.get("/{lesson_id}")
def get_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
):
    lesson = service.get_lesson(db, lesson_id)
    return lesson_to_dict(lesson)


@router.post("", status_code=201)
def create_lesson(
    data: LessonPayload,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    lesson = service.create_lesson(db, data)
    return lesson_to_dict(lesson)


@router.put("/{lesson_id}")
def update_lesson(
    lesson_id: int,
    data: LessonPayload,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    lesson = service.update_lesson(db, lesson_id, data)
    return lesson_to_dict(lesson)


@router.delete("/{lesson_id}")
def delete_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    service.delete_lesson(db, lesson_id)

    return {"message": "درس با موفقیت حذف شد."}
