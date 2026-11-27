
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.shared.dependencies import get_db
from app.core.security import get_current_admin, get_current_student

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
    _admin=Depends(get_current_admin),
):
    items = service.get_students(db)
    return [student_to_dict(item) for item in items]


@router.get("/me")
def get_my_student_profile(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_student),
):
    student = service.get_student(db, int(current_user["student_id"]))
    return student_to_dict(student)


@router.get("/{student_id}")
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    student = service.get_student(db, student_id)
    return student_to_dict(student)


@router.post("", status_code=201)
def create_student(
    data: StudentPayload,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    student = service.create_student(db, data)
    return student_to_dict(student)


@router.put("/{student_id}")
def update_student(
    student_id: int,
    data: StudentPayload,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    student = service.update_student(db, student_id, data)
    return student_to_dict(student)


@router.get("/{student_id}/deletion-preview")
def get_student_deletion_preview(
    student_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return service.get_student_deletion_preview(db, student_id)


@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    confirm: bool = False,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    if not confirm:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="برای حذف دانش‌آموز باید حذف را تأیید کنید.",
        )
    service.delete_student(db, student_id)

    return {
        "message": "دانش‌آموز و تمام اطلاعات وابسته به او با موفقیت حذف شدند."
    }
