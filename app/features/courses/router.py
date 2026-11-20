from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.features.courses import service
from app.features.courses.schemas import CoursePayload
from app.shared.dependencies import get_db


router = APIRouter(
    prefix="/api/courses",
    tags=["Courses"],
)


def course_to_dict(course):
    return {
        "id": course.id,
        "title": course.title,
        "lesson_id": course.lesson_id,
        "lesson": {
            "id": course.lesson.id,
            "name": course.lesson.name,
            "grade": course.lesson.grade,
            "field": course.lesson.field,
        },
        "price_per_session": course.price_per_session,
        "currency": "toman",
        "start_date": course.start_date.isoformat(),
        "status": course.status,
        "created_at": course.created_at.isoformat() if course.created_at else None,
    }


@router.get("")
def get_courses(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    return [course_to_dict(item) for item in service.get_courses(db)]


@router.get("/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    course = service.get_course(db, course_id)
    return course_to_dict(course)


@router.post("", status_code=201)
def create_course(
    data: CoursePayload,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    course = service.create_course(db, data)
    return course_to_dict(course)


@router.put("/{course_id}")
def update_course(
    course_id: int,
    data: CoursePayload,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    course = service.update_course(db, course_id, data)
    return course_to_dict(course)


@router.delete("/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    service.delete_course(db, course_id)
    return {"message": "دوره با موفقیت حذف شد."}
