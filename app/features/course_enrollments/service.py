from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.features.course_enrollments.model import CourseEnrollment
from app.features.courses.model import Course
from app.features.students.model import Student


ENROLLMENT_NOT_FOUND = "عضویت دانش‌آموز در دوره پیدا نشد."


def _get_enrollment_or_404(db: Session, enrollment_id: int):
    enrollment = (
        db.query(CourseEnrollment)
        .options(
            joinedload(CourseEnrollment.student),
            joinedload(CourseEnrollment.course),
        )
        .filter(CourseEnrollment.id == enrollment_id)
        .first()
    )
    if not enrollment:
        raise HTTPException(status_code=404, detail=ENROLLMENT_NOT_FOUND)
    return enrollment


def _validate_references_and_dates(db: Session, data, exclude_id: int | None = None):
    student = db.get(Student, data.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="دانش‌آموز انتخاب‌شده پیدا نشد.")

    course = db.get(Course, data.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="دوره انتخاب‌شده پیدا نشد.")

    if data.start_date < course.start_date:
        raise HTTPException(
            status_code=422,
            detail="تاریخ شروع عضویت نمی‌تواند قبل از تاریخ شروع دوره باشد.",
        )

    if course.status == "completed":
        raise HTTPException(
            status_code=409,
            detail="برای دوره‌ای که به اتمام رسیده امکان ثبت عضویت جدید وجود ندارد.",
        )

    # Date ranges are inclusive. A NULL end date means the enrollment is ongoing.
    # This allows a student to rejoin the same course after a previous enrollment
    # has ended, but prevents two simultaneous enrollments in that course.
    query = db.query(CourseEnrollment).filter(
        CourseEnrollment.student_id == data.student_id,
        CourseEnrollment.course_id == data.course_id,
    )
    if exclude_id is not None:
        query = query.filter(CourseEnrollment.id != exclude_id)

    existing = query.all()
    new_end = data.end_date
    for item in existing:
        existing_end = item.end_date
        starts_before_new_ends = new_end is None or item.start_date <= new_end
        new_starts_before_existing_ends = (
            existing_end is None or existing_end >= data.start_date
        )
        if starts_before_new_ends and new_starts_before_existing_ends:
            raise HTTPException(
                status_code=409,
                detail="بازه عضویت با ثبت‌نام قبلی این دانش‌آموز در همین دوره هم‌پوشانی دارد.",
            )


def get_enrollments(
    db: Session,
    student_id: int | None = None,
    course_id: int | None = None,
):
    query = db.query(CourseEnrollment).options(
        joinedload(CourseEnrollment.student),
        joinedload(CourseEnrollment.course),
    )
    if student_id is not None:
        query = query.filter(CourseEnrollment.student_id == student_id)
    if course_id is not None:
        query = query.filter(CourseEnrollment.course_id == course_id)
    return query.order_by(CourseEnrollment.start_date.desc(), CourseEnrollment.id.desc()).all()


def get_enrollment(db: Session, enrollment_id: int):
    return _get_enrollment_or_404(db, enrollment_id)


def create_enrollment(db: Session, data):
    _validate_references_and_dates(db, data)
    enrollment = CourseEnrollment(
        student_id=data.student_id,
        course_id=data.course_id,
        start_date=data.start_date,
        end_date=data.end_date,
    )
    db.add(enrollment)
    db.commit()
    return _get_enrollment_or_404(db, enrollment.id)


def update_enrollment(db: Session, enrollment_id: int, data):
    enrollment = db.get(CourseEnrollment, enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail=ENROLLMENT_NOT_FOUND)

    if data.student_id != enrollment.student_id or data.course_id != enrollment.course_id:
        from app.features.wallets.model import WalletTransaction

        has_allocations = db.query(WalletTransaction.id).filter(
            WalletTransaction.enrollment_id == enrollment_id,
            WalletTransaction.transaction_type == "course_allocation",
        ).first()
        if has_allocations:
            raise HTTPException(
                status_code=409,
                detail="عضویتی که پرداخت به آن تخصیص داده شده، قابل انتقال به دانش‌آموز یا دوره دیگری نیست.",
            )

    _validate_references_and_dates(db, data, exclude_id=enrollment_id)

    enrollment.student_id = data.student_id
    enrollment.course_id = data.course_id
    enrollment.start_date = data.start_date
    enrollment.end_date = data.end_date
    db.commit()
    return _get_enrollment_or_404(db, enrollment_id)


def get_enrollment_tuition(db: Session, enrollment_id: int, as_of_date=None):
    from datetime import date
    from app.features.course_occurrences.model import CourseOccurrence

    enrollment = _get_enrollment_or_404(db, enrollment_id)
    cutoff = as_of_date or date.today()

    query = db.query(CourseOccurrence).filter(
        CourseOccurrence.course_id == enrollment.course_id,
        CourseOccurrence.status.in_(("held", "moved")),
        # The actual date is authoritative for moved sessions.
        CourseOccurrence.session_date >= enrollment.start_date,
        CourseOccurrence.session_date <= cutoff,
    )
    if enrollment.end_date is not None:
        query = query.filter(CourseOccurrence.session_date <= enrollment.end_date)

    occurrences = query.order_by(
        CourseOccurrence.session_date,
        CourseOccurrence.start_time,
        CourseOccurrence.id,
    ).all()

    from sqlalchemy import func
    from app.features.wallets.model import StudentWallet, WalletTransaction

    price = enrollment.course.price_per_session
    total_tuition = len(occurrences) * price
    allocated_amount = (
        db.query(func.coalesce(func.sum(WalletTransaction.amount), 0))
        .join(StudentWallet, WalletTransaction.wallet_id == StudentWallet.id)
        .filter(
            StudentWallet.student_id == enrollment.student_id,
            WalletTransaction.enrollment_id == enrollment.id,
            WalletTransaction.transaction_type == "course_allocation",
            func.date(WalletTransaction.created_at) <= cutoff.isoformat(),
        )
        .scalar()
    ) or 0
    remaining_debt = max(total_tuition - allocated_amount, 0)
    course_credit = max(allocated_amount - total_tuition, 0)

    return {
        "enrollment_id": enrollment.id,
        "student_id": enrollment.student_id,
        "student_name": f"{enrollment.student.first_name} {enrollment.student.last_name}",
        "course_id": enrollment.course_id,
        "course_title": enrollment.course.title,
        "currency": "toman",
        "price_per_session": price,
        "as_of_date": cutoff.isoformat(),
        "billable_session_count": len(occurrences),
        "total_tuition": total_tuition,
        "allocated_amount": allocated_amount,
        "remaining_debt": remaining_debt,
        "course_credit": course_credit,
        "sessions": [
            {
                "occurrence_id": item.id,
                "scheduled_date": item.scheduled_date.isoformat(),
                "session_date": item.session_date.isoformat(),
                "status": item.status,
                "amount": price,
            }
            for item in occurrences
        ],
    }



def delete_enrollment(db: Session, enrollment_id: int):
    from app.features.course_occurrences.model import CourseOccurrence
    from app.features.wallets.model import WalletTransaction

    enrollment = db.get(CourseEnrollment, enrollment_id)
    if not enrollment:
        raise HTTPException(status_code=404, detail=ENROLLMENT_NOT_FOUND)

    has_allocations = db.query(WalletTransaction.id).filter(
        WalletTransaction.enrollment_id == enrollment_id,
        WalletTransaction.transaction_type == "course_allocation",
    ).first()
    if has_allocations:
        raise HTTPException(
            status_code=409,
            detail="برای این عضویت پرداختی تخصیص داده شده است و امکان حذف آن وجود ندارد. در صورت نیاز تاریخ پایان عضویت را ثبت کنید.",
        )

    occurrence_query = db.query(CourseOccurrence.id).filter(
        CourseOccurrence.course_id == enrollment.course_id,
        CourseOccurrence.session_date >= enrollment.start_date,
    )
    if enrollment.end_date is not None:
        occurrence_query = occurrence_query.filter(
            CourseOccurrence.session_date <= enrollment.end_date
        )

    if occurrence_query.first():
        raise HTTPException(
            status_code=409,
            detail="برای بازه این عضویت سابقه جلسه ثبت شده است و امکان حذف آن وجود ندارد. برای خاتمه عضویت، تاریخ پایان ثبت کنید.",
        )

    db.delete(enrollment)
    db.commit()
    return {"message": "عضویت با موفقیت حذف شد."}
