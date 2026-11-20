from datetime import date, datetime, time, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.features.course_occurrences.model import CourseOccurrence
from app.features.course_occurrences.schemas import OccurrenceStatusPayload
from app.features.course_schedules.model import CourseSchedule
from app.features.courses.model import Course
from app.features.sessions.constants import WEEKDAYS


NOT_FOUND = "جلسه دوره پیدا نشد."
PYTHON_WEEKDAY_BY_PERSIAN_INDEX = [5, 6, 0, 1, 2, 3, 4]


def _schedule_dates(schedule: CourseSchedule, course: Course, through_date: date):
    start = max(schedule.effective_from, course.start_date)
    end = min(schedule.effective_until, through_date) if schedule.effective_until else through_date
    if end < start:
        return

    weekday_index = WEEKDAYS.index(schedule.weekday)
    target_weekday = PYTHON_WEEKDAY_BY_PERSIAN_INDEX[weekday_index]
    first_date = start + timedelta(days=(target_weekday - start.weekday()) % 7)

    current = first_date
    while current <= end:
        yield current
        current += timedelta(days=7)




def generate_occurrences(
    db: Session,
    through_date: date | None = None,
    course_id: int | None = None,
):
    """Idempotently generate occurrences for eligible courses up to through_date."""

    if course_id is not None:
        course = db.get(Course, course_id)

        if not course:
            raise HTTPException(404, "دوره پیدا نشد.")

        if course.status == "completed":
            raise HTTPException(
                409,
                "برای دوره اتمام‌یافته امکان تولید جلسه وجود ندارد."
            )

        if course.status not in ("pending", "active"):
            raise HTTPException(409, "وضعیت دوره برای تولید جلسه معتبر نیست.")

        courses = [course]
    else:
        courses = (
            db.query(Course)
            .filter(Course.status.in_(("pending", "active")))
            .order_by(Course.id)
            .all()
        )

    through_date = through_date or date.today()
    created = []

    for course in courses:
        schedules = (
            db.query(CourseSchedule)
            .filter(CourseSchedule.course_id == course.id)
            .order_by(CourseSchedule.id)
            .all()
        )

        for schedule in schedules:
            for scheduled_date in _schedule_dates(schedule, course, through_date):
                exists = (
                    db.query(CourseOccurrence.id)
                    .filter(
                        CourseOccurrence.course_schedule_id == schedule.id,
                        CourseOccurrence.scheduled_date == scheduled_date,
                    )
                    .first()
                )

                if exists:
                    continue

                occurrence = CourseOccurrence(
                    course_id=course.id,
                    course_schedule_id=schedule.id,
                    teacher_id=schedule.teacher_id,
                    classroom_id=schedule.classroom_id,
                    scheduled_date=scheduled_date,
                    session_date=scheduled_date,
                    start_time=time.fromisoformat(schedule.start_time),
                    end_time=time.fromisoformat(schedule.end_time),
                    status="held",
                )

                db.add(occurrence)
                created.append(occurrence)

    db.commit()

    for item in created:
        db.refresh(item)

    return created


def _occurrence_query(db: Session):
    return db.query(CourseOccurrence).options(
        joinedload(CourseOccurrence.course),
        joinedload(CourseOccurrence.teacher),
        joinedload(CourseOccurrence.classroom),
    )


def get_occurrences(
    db: Session,
    course_id: int | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
):
    query = _occurrence_query(db)
    if course_id is not None:
        query = query.filter(CourseOccurrence.course_id == course_id)
    if from_date is not None:
        query = query.filter(CourseOccurrence.session_date >= from_date)
    if to_date is not None:
        query = query.filter(CourseOccurrence.session_date <= to_date)
    return query.order_by(CourseOccurrence.session_date, CourseOccurrence.start_time).all()


def get_occurrence(db: Session, occurrence_id: int):
    item = _occurrence_query(db).filter(CourseOccurrence.id == occurrence_id).first()
    if not item:
        raise HTTPException(404, NOT_FOUND)
    return item


def update_occurrence_status(db: Session, occurrence_id: int, data: OccurrenceStatusPayload):
    item = db.get(CourseOccurrence, occurrence_id)
    if not item:
        raise HTTPException(404, NOT_FOUND)

   
    if data.status == "moved":
        if data.session_date is None or data.session_date == item.scheduled_date:
            raise HTTPException(422, "تاریخ جدید جلسه باید با تاریخ اصلی متفاوت باشد.")
        conflicts = db.query(CourseOccurrence).filter(
            CourseOccurrence.id != item.id,
            CourseOccurrence.status != "cancelled",
            CourseOccurrence.session_date == data.session_date,
            CourseOccurrence.start_time < item.end_time,
            CourseOccurrence.end_time > item.start_time,
        ).all()
        for existing in conflicts:
            if existing.teacher_id == item.teacher_id:
                raise HTTPException(409, "مدرس در تاریخ و ساعت انتخاب‌شده جلسه دیگری دارد.")
            if existing.classroom_id == item.classroom_id:
                raise HTTPException(409, "کلاس در تاریخ و ساعت انتخاب‌شده رزرو شده است.")
        item.session_date = data.session_date
    elif data.status == "held":
        if data.session_date is not None and data.session_date != item.scheduled_date:
            raise HTTPException(422, "برای تغییر تاریخ، وضعیت جلسه باید جابه‌جاشده باشد.")
        item.session_date = item.scheduled_date
    else:  # cancelled: retain the moved date if it had already been rescheduled.
        if data.session_date is not None and data.session_date != item.session_date:
            raise HTTPException(422, "برای تغییر تاریخ، وضعیت جلسه باید جابه‌جاشده باشد.")

    item.status = data.status
    db.commit()
    return get_occurrence(db, occurrence_id)
