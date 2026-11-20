from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.features.course_schedules import service
from app.features.course_schedules.schemas import CourseSchedulePayload
from app.shared.dependencies import get_db

router = APIRouter(prefix="/api/course-schedules", tags=["Course Schedules"])


def schedule_to_dict(item):
    return {
        "id": item.id,
        "course_id": item.course_id,
        "course_title": item.course.title,
        "teacher_id": item.teacher_id,
        "teacher_name": f"{item.teacher.first_name} {item.teacher.last_name}",
        "classroom_id": item.classroom_id,
        "classroom_name": item.classroom.name,
        "weekday": item.weekday,
        "start_time": item.start_time,
        "end_time": item.end_time,
        "effective_from": item.effective_from.isoformat(),
        "effective_until": item.effective_until.isoformat() if item.effective_until else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("")
def list_schedules(
    course_id: int | None = Query(default=None, gt=0),
    teacher_id: int | None = Query(default=None, gt=0),
    classroom_id: int | None = Query(default=None, gt=0),
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return [
        schedule_to_dict(item)
        for item in service.get_schedules(
            db,
            course_id=course_id,
            teacher_id=teacher_id,
            classroom_id=classroom_id,
        )
    ]

@router.get("/{schedule_id}")
def get_schedule(schedule_id: int, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    return schedule_to_dict(service.get_schedule(db, schedule_id))


@router.post("", status_code=201)
def create_schedule(data: CourseSchedulePayload, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    return schedule_to_dict(service.create_schedule(db, data))


@router.put("/{schedule_id}")
def update_schedule(schedule_id: int, data: CourseSchedulePayload, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    return schedule_to_dict(service.update_schedule(db, schedule_id, data))


@router.delete("/{schedule_id}")
def delete_schedule(schedule_id: int, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    service.delete_schedule(db, schedule_id)
    return {"message": "برنامه هفتگی با موفقیت حذف شد."}
