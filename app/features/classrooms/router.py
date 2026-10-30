
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.shared.dependencies import get_db
from app.core.security import verify_admin_password

from app.features.classrooms.schemas import ClassroomPayload
from app.features.classrooms import service


router = APIRouter(
    prefix="/api/classrooms",
    tags=["Classrooms"],
)


def classroom_to_dict(classroom):
    return {
        "id": classroom.id,
        "name": classroom.name,
        "address": classroom.address,
        "capacity": classroom.capacity,
        "latitude": classroom.latitude,
        "longitude": classroom.longitude,
    }


@router.get("")
def get_classrooms(db: Session = Depends(get_db)):
    items = service.get_classrooms(db)
    return [classroom_to_dict(item) for item in items]


@router.get("/{classroom_id}")
def get_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
):
    classroom = service.get_classroom(db, classroom_id)
    return classroom_to_dict(classroom)


@router.post("", status_code=201)
def create_classroom(
    data: ClassroomPayload,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    classroom = service.create_classroom(db, data)
    return classroom_to_dict(classroom)


@router.put("/{classroom_id}")
def update_classroom(
    classroom_id: int,
    data: ClassroomPayload,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    classroom = service.update_classroom(db, classroom_id, data)
    return classroom_to_dict(classroom)


@router.delete("/{classroom_id}")
def delete_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(verify_admin_password),
):
    service.delete_classroom(db, classroom_id)

    return {"message": "کلاس با موفقیت حذف شد."}
