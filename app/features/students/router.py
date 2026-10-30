
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.shared.dependencies import get_db
from app.core.security import verify_admin_password

from app.features.students.schemas import StudentPayload
from app.features.students import service


router = APIRouter(
    prefix="/api/students",
    tags=["Students"],
)


def student_to_dict(student):
    return {
        "id": student.id,
        "first_name": student.first_name,
        "last_name": student.last_name,
        "national_code": student.national_code,
        "grade": student.grade,
        "field": student.field,
        "father_name": student.father_name,
        "phone": student.phone,
        "phone2": student.phone2,
    }


@router.get("")
def get_students(
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    items = service.get_students(db)
    return [student_to_dict(item) for item in items]


@router.get("/{student_id}")
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    student = service.get_student(db, student_id)
    return student_to_dict(student)


@router.post("", status_code=201)
def create_student(
    data: StudentPayload,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    student = service.create_student(db, data)
    return student_to_dict(student)


@router.put("/{student_id}")
def update_student(
    student_id: int,
    data: StudentPayload,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    student = service.update_student(db, student_id, data)
    return student_to_dict(student)


@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    service.delete_student(db, student_id)

    return {
        "message": "دانش‌آموز با موفقیت حذف شد."
    }
