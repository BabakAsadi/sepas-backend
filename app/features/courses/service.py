from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.features.courses.model import Course
from app.features.lessons.model import Lesson


COURSE_NOT_FOUND = "دوره پیدا نشد."


def get_courses(db: Session):
    return (
        db.query(Course)
        .options(joinedload(Course.lesson))
        .order_by(Course.start_date.desc(), Course.id.desc())
        .all()
    )


def get_course(db: Session, course_id: int):
    course = (
        db.query(Course)
        .options(joinedload(Course.lesson))
        .filter(Course.id == course_id)
        .first()
    )

    if not course:
        raise HTTPException(status_code=404, detail=COURSE_NOT_FOUND)

    return course


def _validate_payload(db: Session, data):
    title = data.title.strip()
    if not title:
        raise HTTPException(status_code=422, detail="عنوان دوره الزامی است.")

    lesson = db.get(Lesson, data.lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="درس انتخاب‌شده پیدا نشد.")

    return title


def create_course(db: Session, data):
    title = _validate_payload(db, data)

    course = Course(
        title=title,
        lesson_id=data.lesson_id,
        price_per_session=data.price_per_session,
        start_date=data.start_date,
        status=data.status,
    )

    db.add(course)
    db.commit()
    db.refresh(course)

    return get_course(db, course.id)


def update_course(db: Session, course_id: int, data):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail=COURSE_NOT_FOUND)

    title = _validate_payload(db, data)

    if data.price_per_session != course.price_per_session:
        from app.features.course_enrollments.model import CourseEnrollment
        from app.features.course_occurrences.model import CourseOccurrence

        has_enrollments = db.query(CourseEnrollment.id).filter(
            CourseEnrollment.course_id == course_id
        ).first()
        has_occurrences = db.query(CourseOccurrence.id).filter(
            CourseOccurrence.course_id == course_id
        ).first()
        if has_enrollments or has_occurrences:
            raise HTTPException(
                status_code=409,
                detail="قیمت هر جلسه پس از ثبت عضویت یا ایجاد سابقه جلسه قابل تغییر نیست؛ برای قیمت جدید دوره جداگانه‌ای ایجاد کنید.",
            )

    course.title = title
    course.lesson_id = data.lesson_id
    course.price_per_session = data.price_per_session
    course.start_date = data.start_date
    course.status = data.status

    db.commit()
    db.refresh(course)

    return get_course(db, course.id)


def delete_course(db: Session, course_id: int):
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(status_code=404, detail=COURSE_NOT_FOUND)

    # Enrollment history must remain intact once students have joined a course.
    from app.features.course_enrollments.model import CourseEnrollment

    if db.query(CourseEnrollment.id).filter(
        CourseEnrollment.course_id == course_id
    ).first():
        raise HTTPException(
            status_code=409,
            detail="این دوره سابقه عضویت دانش‌آموز دارد و قابل حذف نیست.",
        )

    db.delete(course)
    db.commit()
