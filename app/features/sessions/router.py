
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.shared.dependencies import get_db
from app.core.security import get_current_admin
from app.features.sessions.schemas import SessionPayload
from app.features.sessions import service


router = APIRouter(
    prefix="/api/sessions",
    tags=["Sessions"],
)


def session_to_dict(session):
    return {
        "id": session.id,
        "lesson_id": session.lesson_id,
        "lesson_name": session.lesson.name,
        "lesson_grade": session.lesson.grade,
        "lesson_field": session.lesson.field,
        "teacher_id": session.teacher_id,
        "teacher_name": (
            f"{session.teacher.first_name} {session.teacher.last_name}"
        ),
        "classroom_id": session.classroom_id,
        "classroom_name": session.classroom.name,
        "weekday": session.weekday,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "registered_count": session.registered_count,
    }


@router.get("")
def list_sessions(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    sessions = service.get_sessions(db)
    return [session_to_dict(session) for session in sessions]


@router.get("/{session_id}")
def get_session(session_id: int, db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    session = service.get_session(db, session_id)
    return session_to_dict(session)


@router.post("")
def create_session(
    data: SessionPayload,
    db: Session = Depends(get_db),
    _: bool = Depends(get_current_admin),
):
    session = service.create_session(db, data)
    return session_to_dict(session)


@router.put("/{session_id}")
def update_session(
    session_id: int,
    data: SessionPayload,
    db: Session = Depends(get_db),
    _: bool = Depends(get_current_admin),
):
    session = service.update_session(db, session_id, data)
    return session_to_dict(session)


@router.delete("/{session_id}")
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(get_current_admin),
):
    service.delete_session(db, session_id)
    return {"success": True}
