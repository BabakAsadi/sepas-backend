from datetime import date, datetime, time, timedelta, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.database.models  # noqa: F401
from app.database.base import Base
from app.features.classrooms.model import Classroom
from app.features.course_enrollments.model import CourseEnrollment
from app.features.course_enrollments.schemas import CourseEnrollmentPayload
from app.features.course_enrollments.service import create_enrollment, get_enrollment_tuition, update_enrollment
from app.features.course_occurrences.model import CourseOccurrence
from app.features.course_occurrences.schemas import OccurrenceStatusPayload
from app.features.course_occurrences.service import generate_occurrences, update_occurrence_status
from app.features.course_schedules.model import CourseSchedule
from app.features.courses.model import Course
from app.features.lessons.model import Lesson
from app.features.reports.service import get_student_debt_report
from app.features.students.model import Student
from app.features.teachers.model import Teacher
from app.features.wallets.model import StudentWallet, WalletTransaction
from app.features.wallets.schemas import WalletAllocationPayload, WalletTopUpPayload
from app.features.wallets.service import allocate_to_enrollment, top_up_wallet
from app.features.sessions.constants import WEEKDAYS


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def make_academy(db, *, course_status="active", price=100_000, start_date=None):
    today = date.today()
    lesson = Lesson(grade="دهم", name="ریاضی", field="ریاضی")
    teacher = Teacher(first_name="تست", last_name="مدرس", phone="09000000001")
    classroom = Classroom(name="کلاس تست", address="آدرس تست", capacity=10)
    student = Student(
        first_name="آرمان", last_name="تست", national_code="9900000001",
        grade="دهم", field="ریاضی", father_name="پدر تست", phone="09000000002",
    )
    db.add_all([lesson, teacher, classroom, student])
    db.flush()
    course = Course(
        title="دوره تست", lesson_id=lesson.id, price_per_session=price,
        start_date=start_date or today - timedelta(days=30), status=course_status,
    )
    db.add(course)
    db.flush()
    return student, course, teacher, classroom


def add_enrollment(db, student, course, start=None, end=None):
    enrollment = CourseEnrollment(
        student_id=student.id, course_id=course.id,
        start_date=start or course.start_date, end_date=end,
    )
    db.add(enrollment)
    db.flush()
    return enrollment


def add_occurrence(db, course, teacher, classroom, scheduled, *, actual=None, status="held"):
    item = CourseOccurrence(
        course_id=course.id, course_schedule_id=None,
        teacher_id=teacher.id, classroom_id=classroom.id,
        scheduled_date=scheduled, session_date=actual or scheduled,
        start_time=time(10, 0), end_time=time(11, 0), status=status,
    )
    db.add(item)
    db.flush()
    return item


def test_occurrence_generation_is_idempotent_for_pending_and_active_courses(db):
    student, active, teacher, classroom = make_academy(db)
    _, pending, _, _ = make_academy_for_pending(db, teacher, classroom)
    today = date.today()
    schedule = CourseSchedule(
        course_id=active.id, teacher_id=teacher.id, classroom_id=classroom.id,
        weekday=WEEKDAYS[(today.weekday() - 5) % 7],
        start_time="10:00", end_time="11:00",
        effective_from=today - timedelta(days=21), effective_until=None,
    )
    pending_schedule = CourseSchedule(
        course_id=pending.id, teacher_id=teacher.id, classroom_id=classroom.id,
        weekday=WEEKDAYS[(today.weekday() - 5) % 7],
        start_time="12:00", end_time="13:00",
        effective_from=today - timedelta(days=21), effective_until=None,
    )
    db.add_all([schedule, pending_schedule])
    db.commit()

    first = generate_occurrences(db, today)
    second = generate_occurrences(db, today)

    assert len(first) > 0
    assert second == []
    active_count = db.query(CourseOccurrence).filter_by(course_id=active.id).count()
    pending_count = db.query(CourseOccurrence).filter_by(course_id=pending.id).count()
    assert active_count > 0
    assert pending_count > 0
    assert len(first) == active_count + pending_count


def make_academy_for_pending(db, teacher, classroom):
    lesson = Lesson(grade="یازدهم", name="فیزیک", field="ریاضی")
    db.add(lesson)
    db.flush()
    course = Course(
        title="دوره در انتظار", lesson_id=lesson.id, price_per_session=100_000,
        start_date=date.today() - timedelta(days=30), status="pending",
    )
    db.add(course)
    db.flush()
    return None, course, teacher, classroom


def test_tuition_counts_held_and_moved_by_actual_date_and_excludes_cancelled(db):
    student, course, teacher, classroom = make_academy(db)
    start = date.today() - timedelta(days=10)
    enrollment = add_enrollment(db, student, course, start=start)
    add_occurrence(db, course, teacher, classroom, start + timedelta(days=1))
    moved = add_occurrence(
        db, course, teacher, classroom, start + timedelta(days=2),
        actual=start + timedelta(days=5), status="moved",
    )
    add_occurrence(
        db, course, teacher, classroom, start + timedelta(days=3), status="cancelled",
    )
    add_occurrence(
        db, course, teacher, classroom, start - timedelta(days=1),
    )

    result = get_enrollment_tuition(db, enrollment.id, date.today())
    assert result["billable_session_count"] == 2
    assert result["total_tuition"] == 200_000
    assert {row["occurrence_id"] for row in result["sessions"]} == {
        db.query(CourseOccurrence.id).filter(CourseOccurrence.session_date == start + timedelta(days=1)).scalar(),
        moved.id,
    }


def test_enrollment_end_date_is_inclusive(db):
    student, course, teacher, classroom = make_academy(db)
    start = date.today() - timedelta(days=5)
    end = start + timedelta(days=2)
    enrollment = add_enrollment(db, student, course, start=start, end=end)
    add_occurrence(db, course, teacher, classroom, start)
    add_occurrence(db, course, teacher, classroom, end)
    add_occurrence(db, course, teacher, classroom, end + timedelta(days=1))

    result = get_enrollment_tuition(db, enrollment.id, date.today())
    assert result["billable_session_count"] == 2
    assert result["total_tuition"] == 200_000


def test_wallet_topup_and_partial_allocation_keep_balance_consistent(db):
    student, course, _, _ = make_academy(db)
    enrollment = add_enrollment(db, student, course)

    wallet, topup = top_up_wallet(db, student.id, WalletTopUpPayload(amount=500_000))
    wallet, allocation = allocate_to_enrollment(
        db, student.id,
        WalletAllocationPayload(enrollment_id=enrollment.id, amount=200_000),
    )

    assert topup.amount == 500_000
    assert allocation.amount == 200_000
    assert allocation.enrollment_id == enrollment.id
    assert wallet.balance == 300_000
    assert db.query(WalletTransaction).count() == 2


def test_wallet_rejects_allocation_above_available_balance(db):
    student, course, _, _ = make_academy(db)
    enrollment = add_enrollment(db, student, course)
    top_up_wallet(db, student.id, WalletTopUpPayload(amount=100_000))

    with pytest.raises(HTTPException) as error:
        allocate_to_enrollment(
            db, student.id,
            WalletAllocationPayload(enrollment_id=enrollment.id, amount=100_001),
        )

    assert error.value.status_code == 409
    wallet = db.query(StudentWallet).filter_by(student_id=student.id).one()
    assert wallet.balance == 100_000
    assert db.query(WalletTransaction).count() == 1


def test_wallet_cannot_allocate_to_another_students_enrollment(db):
    student, course, _, _ = make_academy(db)
    other = Student(
        first_name="نگار", last_name="تست", national_code="9900000002",
        grade="دهم", field="ریاضی", father_name="پدر", phone="09000000003",
    )
    db.add(other)
    db.flush()
    other_enrollment = add_enrollment(db, other, course)
    top_up_wallet(db, student.id, WalletTopUpPayload(amount=500_000))

    with pytest.raises(HTTPException) as error:
        allocate_to_enrollment(
            db, student.id,
            WalletAllocationPayload(enrollment_id=other_enrollment.id, amount=100_000),
        )

    assert error.value.status_code == 404
    wallet = db.query(StudentWallet).filter_by(student_id=student.id).one()
    assert wallet.balance == 500_000


def test_enrollment_allows_rejoin_after_previous_enrollment_ends(db):
    student, course, _, _ = make_academy(db)
    first_start = course.start_date
    first_end = first_start + timedelta(days=5)
    first = create_enrollment(
        db,
        CourseEnrollmentPayload(
            student_id=student.id, course_id=course.id,
            start_date=first_start, end_date=first_end,
        ),
    )
    second = create_enrollment(
        db,
        CourseEnrollmentPayload(
            student_id=student.id, course_id=course.id,
            start_date=first_end + timedelta(days=1), end_date=None,
        ),
    )
    assert first.id != second.id


def test_enrollment_rejects_overlapping_ranges(db):
    student, course, _, _ = make_academy(db)
    start = course.start_date
    add_enrollment(db, student, course, start=start, end=start + timedelta(days=10))

    with pytest.raises(HTTPException) as error:
        create_enrollment(
            db,
            CourseEnrollmentPayload(
                student_id=student.id, course_id=course.id,
                start_date=start + timedelta(days=10), end_date=None,
            ),
        )
    assert error.value.status_code == 409


def test_debt_report_aggregates_by_student_and_sorts_descending(db):
    student, course, teacher, classroom = make_academy(db, price=100_000)
    enrollment = add_enrollment(db, student, course)
    add_occurrence(db, course, teacher, classroom, date.today() - timedelta(days=2))
    add_occurrence(db, course, teacher, classroom, date.today() - timedelta(days=1))

    report = get_student_debt_report(db, date.today())
    assert report["indebted_student_count"] == 1
    assert report["total_debt"] == 200_000
    assert report["students"][0]["national_code"] == student.national_code
    assert report["students"][0]["courses"][0]["remaining_debt"] == 200_000


def test_report_cutoff_excludes_allocations_after_cutoff(db):
    student, course, teacher, classroom = make_academy(db, price=100_000)
    enrollment = add_enrollment(db, student, course)
    add_occurrence(db, course, teacher, classroom, date.today() - timedelta(days=3))
    wallet = StudentWallet(student_id=student.id, balance=0)
    db.add(wallet)
    db.flush()
    db.add(
        WalletTransaction(
            wallet_id=wallet.id, transaction_type="course_allocation", amount=100_000,
            enrollment_id=enrollment.id, description="پرداخت بعد از تاریخ گزارش",
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    cutoff = date.today() - timedelta(days=1)
    report = get_student_debt_report(db, cutoff)
    assert report["total_debt"] == 100_000


def test_cancelled_occurrence_cannot_be_changed_again(db):
    student, course, teacher, classroom = make_academy(db)
    occurrence = add_occurrence(
        db, course, teacher, classroom, date.today() - timedelta(days=1), status="cancelled",
    )

    with pytest.raises(HTTPException) as error:
        update_occurrence_status(
            db, occurrence.id, OccurrenceStatusPayload(status="held"),
        )
    assert error.value.status_code == 409


def test_moving_occurrence_can_use_slot_of_cancelled_occurrence(db):
    student, course, teacher, classroom = make_academy(db)
    target_date = date.today() - timedelta(days=1)
    cancelled = add_occurrence(
        db, course, teacher, classroom, target_date, status="cancelled",
    )
    to_move = add_occurrence(
        db, course, teacher, classroom, date.today() - timedelta(days=3),
    )

    updated = update_occurrence_status(
        db,
        to_move.id,
        OccurrenceStatusPayload(status="moved", session_date=target_date),
    )

    assert updated.session_date == target_date
    assert updated.status == "moved"
    assert cancelled.status == "cancelled"


def test_moving_occurrence_rejects_slot_used_by_active_occurrence(db):
    student, course, teacher, classroom = make_academy(db)
    target_date = date.today() - timedelta(days=1)
    add_occurrence(db, course, teacher, classroom, target_date, status="held")
    to_move = add_occurrence(
        db, course, teacher, classroom, date.today() - timedelta(days=3),
    )

    with pytest.raises(HTTPException) as error:
        update_occurrence_status(
            db,
            to_move.id,
            OccurrenceStatusPayload(status="moved", session_date=target_date),
        )

    assert error.value.status_code == 409


def test_enrollment_with_allocated_payment_cannot_be_reassigned(db):
    student, course, _, _ = make_academy(db)
    enrollment = add_enrollment(db, student, course)
    other_student = Student(
        first_name="نگار", last_name="تست", national_code="9900000002",
        grade="دهم", field="ریاضی", father_name="پدر", phone="09000000003",
    )
    db.add(other_student)
    db.flush()

    top_up_wallet(db, student.id, WalletTopUpPayload(amount=300_000))
    allocate_to_enrollment(
        db, student.id,
        WalletAllocationPayload(enrollment_id=enrollment.id, amount=100_000),
    )

    with pytest.raises(HTTPException) as error:
        update_enrollment(
            db,
            enrollment.id,
            CourseEnrollmentPayload(
                student_id=other_student.id,
                course_id=course.id,
                start_date=enrollment.start_date,
                end_date=enrollment.end_date,
            ),
        )

    assert error.value.status_code == 409
    db.refresh(enrollment)
    assert enrollment.student_id == student.id
