
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.shared.dependencies import get_db
from app.core.security import verify_admin_password

from app.features.teachers.schemas import TeacherPayload
from app.features.teachers import service


router = APIRouter(
    prefix="/api/teachers",
    tags=["Teachers"],
)


def teacher_to_dict(teacher):
    return {
        "id": teacher.id,
        "first_name": teacher.first_name,
        "last_name": teacher.last_name,
        "phone": teacher.phone,
        "photo": teacher.photo,
    }


@router.get("")
def get_teachers(db: Session = Depends(get_db)):
    items = service.get_teachers(db)
    return [teacher_to_dict(item) for item in items]


@router.get("/{teacher_id}")
def get_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
):
    teacher = service.get_teacher(db, teacher_id)
    return teacher_to_dict(teacher)


@router.post("", status_code=201)
def create_teacher(
    data: TeacherPayload,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    teacher = service.create_teacher(db, data)
    return teacher_to_dict(teacher)


@router.put("/{teacher_id}")
def update_teacher(
    teacher_id: int,
    data: TeacherPayload,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    teacher = service.update_teacher(db, teacher_id, data)
    return teacher_to_dict(teacher)


@router.delete("/{teacher_id}")
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    service.delete_teacher(db, teacher_id)
    return {"message": "دبیر با موفقیت حذف شد."}
