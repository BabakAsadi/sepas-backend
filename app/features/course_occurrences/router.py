
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_admin
from app.features.course_occurrences import service
from app.features.course_occurrences.schemas import OccurrenceStatusPayload
from app.shared.dependencies import get_db


router = APIRouter(prefix="/api/course-occurrences", tags=["Course Occurrences"])


def occurrence_to_dict(item):
    return {
        "id": item.id,
        "course_id": item.course_id,
        "course_title": item.course.title,
        "course_schedule_id": item.course_schedule_id,
        "teacher_id": item.teacher_id,
        "teacher_name": f"{item.teacher.first_name} {item.teacher.last_name}",
        "classroom_id": item.classroom_id,
        "classroom_name": item.classroom.name,
        "scheduled_date": item.scheduled_date.isoformat(),
        "session_date": item.session_date.isoformat(),
        "start_time": item.start_time.strftime("%H:%M"),
        "end_time": item.end_time.strftime("%H:%M"),
        "status": item.status,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("")
def list_occurrences(
    course_id: int | None = Query(default=None, gt=0),
    from_date: date | None = None,
    to_date: date | None = None,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    if from_date and to_date and from_date > to_date:
        raise HTTPException(
            422,
            "تاریخ شروع بازه نباید بعد از تاریخ پایان باشد."
        )

    return [
        occurrence_to_dict(item)
        for item in service.get_occurrences(db, course_id, from_date, to_date)
    ]


@router.get("/{occurrence_id}")
def get_occurrence(
    occurrence_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return occurrence_to_dict(service.get_occurrence(db, occurrence_id))


@router.post("/generate", status_code=201)
def generate_all_occurrences(
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    items = service.generate_occurrences(db)

    return {
        "created_count": len(items),
        "items": [occurrence_to_dict(item) for item in items],
    }


@router.post("/generate/{course_id}", status_code=201)
def generate_course_occurrences(
    course_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    items = service.generate_occurrences(db, course_id=course_id)

    return {
        "created_count": len(items),
        "items": [occurrence_to_dict(item) for item in items],
    }


@router.patch("/{occurrence_id}/status")
def update_occurrence_status(
    occurrence_id: int,
    payload: OccurrenceStatusPayload,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    return occurrence_to_dict(
        service.update_occurrence_status(db, occurrence_id, payload)
    )
