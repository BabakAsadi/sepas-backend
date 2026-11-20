from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.features.course_schedules.model import CourseSchedule
from app.features.course_schedules.schemas import CourseSchedulePayload
from app.features.courses.model import Course
from app.features.sessions.constants import WEEKDAYS
from app.features.sessions.model import CourseSession
from app.features.course_occurrences.model import CourseOccurrence
from app.features.teachers.model import Teacher
from app.features.classrooms.model import Classroom


NOT_FOUND = "برنامه هفتگی پیدا نشد."


def _validate(db: Session, data: CourseSchedulePayload, exclude_id: int | None = None):
    course = db.get(Course, data.course_id)
    if not course:
        raise HTTPException(404, "دوره انتخاب‌شده پیدا نشد.")
    if course.status == "completed":
        raise HTTPException(409, "برای دوره اتمام‌یافته نمی‌توان برنامه جدید تعریف کرد.")

    if not db.get(Teacher, data.teacher_id):
        raise HTTPException(404, "مدرس انتخاب‌شده پیدا نشد.")
    if not db.get(Classroom, data.classroom_id):
        raise HTTPException(404, "کلاس انتخاب‌شده پیدا نشد.")

    if data.weekday not in WEEKDAYS:
        raise HTTPException(422, "روز هفته نامعتبر است.")
    if data.start_time >= data.end_time:
        raise HTTPException(422, "ساعت شروع باید قبل از ساعت پایان باشد.")
    if data.effective_from < course.start_date:
        raise HTTPException(422, "تاریخ شروع برنامه نمی‌تواند قبل از شروع دوره باشد.")
    if data.effective_until and data.effective_until < data.effective_from:
        raise HTTPException(422, "تاریخ پایان برنامه نمی‌تواند قبل از تاریخ شروع آن باشد.")

    _check_conflicts(db, data, exclude_id)


def _date_ranges_overlap(a_start, a_end, b_start, b_end):
    return (a_end is None or b_start <= a_end) and (b_end is None or a_start <= b_end)


def _check_conflicts(db: Session, data: CourseSchedulePayload, exclude_id: int | None = None):
    query = db.query(CourseSchedule).filter(
        CourseSchedule.weekday == data.weekday,
        CourseSchedule.start_time < data.end_time,
        CourseSchedule.end_time > data.start_time,
    )
    if exclude_id is not None:
        query = query.filter(CourseSchedule.id != exclude_id)

    for existing in query.all():
        if not _date_ranges_overlap(
            data.effective_from, data.effective_until,
            existing.effective_from, existing.effective_until,
        ):
            continue
        if existing.teacher_id == data.teacher_id:
            raise HTTPException(409, "این مدرس در این روز و بازه زمانی برنامه دیگری دارد.")
        if existing.classroom_id == data.classroom_id:
            raise HTTPException(409, "این کلاس در این روز و بازه زمانی رزرو شده است.")

    # Existing course_sessions are the legacy weekly schedules. Keep their
    # resource-conflict protection while the old feature remains in use.
    legacy = db.query(CourseSession).filter(
        CourseSession.weekday == data.weekday,
        CourseSession.start_time < data.end_time,
        CourseSession.end_time > data.start_time,
    ).all()
    for existing in legacy:
        if existing.teacher_id == data.teacher_id:
            raise HTTPException(409, "این مدرس در این بازه زمانی در برنامه‌های فعلی نیز مشغول است.")
        if existing.classroom_id == data.classroom_id:
            raise HTTPException(409, "این کلاس در این بازه زمانی در برنامه‌های فعلی رزرو شده است.")


def _with_relations(db: Session, schedule_id: int):
    return (
        db.query(CourseSchedule)
        .options(
            joinedload(CourseSchedule.course),
            joinedload(CourseSchedule.teacher),
            joinedload(CourseSchedule.classroom),
        )
        .filter(CourseSchedule.id == schedule_id)
        .first()
    )


def get_schedules(
    db: Session,
    course_id: int | None = None,
    teacher_id: int | None = None,
    classroom_id: int | None = None,
):
    query = db.query(CourseSchedule).options(
        joinedload(CourseSchedule.course),
        joinedload(CourseSchedule.teacher),
        joinedload(CourseSchedule.classroom),
    )

    if course_id is not None:
        query = query.filter(CourseSchedule.course_id == course_id)

    if teacher_id is not None:
        query = query.filter(CourseSchedule.teacher_id == teacher_id)

    if classroom_id is not None:
        query = query.filter(CourseSchedule.classroom_id == classroom_id)

    return query.order_by(
        CourseSchedule.weekday,
        CourseSchedule.start_time,
    ).all()


def get_schedule(db: Session, schedule_id: int):
    schedule = _with_relations(db, schedule_id)
    if not schedule:
        raise HTTPException(404, NOT_FOUND)
    return schedule


def create_schedule(db: Session, data: CourseSchedulePayload):
    _validate(db, data)
    schedule = CourseSchedule(**data.model_dump())
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return get_schedule(db, schedule.id)


def update_schedule(db: Session, schedule_id: int, data: CourseSchedulePayload):
    schedule = db.get(CourseSchedule, schedule_id)
    if not schedule:
        raise HTTPException(404, NOT_FOUND)
    _validate(db, data, exclude_id=schedule_id)
    for key, value in data.model_dump().items():
        setattr(schedule, key, value)
    db.commit()
    return get_schedule(db, schedule_id)


def delete_schedule(db: Session, schedule_id: int):
    schedule = db.get(CourseSchedule, schedule_id)
    if not schedule:
        raise HTTPException(404, NOT_FOUND)
    has_occurrences = db.query(CourseOccurrence.id).filter(
        CourseOccurrence.course_schedule_id == schedule_id
    ).first()
    if has_occurrences:
        raise HTTPException(409, "این برنامه دارای سوابق جلسه است و قابل حذف نیست.")
    db.delete(schedule)
    db.commit()
