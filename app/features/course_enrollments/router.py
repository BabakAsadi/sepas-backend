from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.features.course_enrollments import service
from app.features.course_enrollments.schemas import CourseEnrollmentPayload
from app.shared.dependencies import get_db


router = APIRouter(
    prefix="/api/course-enrollments",
    tags=["Course Enrollments"],
)


def enrollment_to_dict(enrollment):
    student = enrollment.student
    course = enrollment.course
    return {
        "id": enrollment.id,
        "student_id": enrollment.student_id,
        "student": {
            "id": student.id,
            "first_name": student.first_name,
            "last_name": student.last_name,
            "national_code": student.national_code,
        },
        "course_id": enrollment.course_id,
        "course": {
            "id": course.id,
            "title": course.title,
            "price_per_session": course.price_per_session,
            "currency": "toman",
        },
        "start_date": enrollment.start_date.isoformat(),
        "end_date": enrollment.end_date.isoformat() if enrollment.end_date else None,
        "created_at": enrollment.created_at.isoformat() if enrollment.created_at else None,
    }


@router.get("")
def get_enrollments(
    student_id: int | None = Query(default=None, gt=0),
    course_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    items = service.get_enrollments(db, student_id=student_id, course_id=course_id)
    return [enrollment_to_dict(item) for item in items]


@router.get("/{enrollment_id}")
def get_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return enrollment_to_dict(service.get_enrollment(db, enrollment_id))




@router.get("/{enrollment_id}/tuition")
def get_enrollment_tuition(
    enrollment_id: int,
    as_of_date: date | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    from datetime import date as date_type
    from fastapi import HTTPException

    if as_of_date is not None and as_of_date > date_type.today():
        raise HTTPException(status_code=422, detail="تاریخ محاسبه نمی‌تواند در آینده باشد.")
    return service.get_enrollment_tuition(db, enrollment_id, as_of_date)


@router.post("", status_code=201)
def create_enrollment(
    data: CourseEnrollmentPayload,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return enrollment_to_dict(service.create_enrollment(db, data))


@router.put("/{enrollment_id}")
def update_enrollment(
    enrollment_id: int,
    data: CourseEnrollmentPayload,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return enrollment_to_dict(service.update_enrollment(db, enrollment_id, data))



@router.delete("/{enrollment_id}")
def delete_enrollment(
    enrollment_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.delete_enrollment(db, enrollment_id)
