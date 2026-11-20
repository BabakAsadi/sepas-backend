from datetime import date

from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.features.course_enrollments.model import CourseEnrollment
from app.features.course_enrollments.service import get_enrollment_tuition
from app.features.courses.model import Course


def get_student_debt_report(db: Session, as_of_date: date | None = None):
    """Return indebted students and their course-level balances at a cutoff date."""
    cutoff = as_of_date or date.today()

    enrollments = (
        db.query(CourseEnrollment)
        .options(
            joinedload(CourseEnrollment.student),
            joinedload(CourseEnrollment.course),
        )
        .order_by(CourseEnrollment.student_id, CourseEnrollment.id)
        .all()
    )

    students_by_id: dict[int, dict] = {}

    for enrollment in enrollments:
        tuition = get_enrollment_tuition(db, enrollment.id, cutoff)
        debt = tuition["remaining_debt"]
        if debt <= 0:
            continue

        student = enrollment.student
        row = students_by_id.setdefault(
            student.id,
            {
                "student_id": student.id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "full_name": f"{student.first_name} {student.last_name}",
                "national_code": student.national_code,
                "total_debt": 0,
                "courses": [],
            },
        )

        row["total_debt"] += debt
        row["courses"].append(
            {
                "enrollment_id": enrollment.id,
                "course_id": enrollment.course_id,
                "course_title": enrollment.course.title,
                "price_per_session": tuition["price_per_session"],
                "billable_session_count": tuition["billable_session_count"],
                "total_tuition": tuition["total_tuition"],
                "allocated_amount": tuition["allocated_amount"],
                "remaining_debt": debt,
                "course_credit": tuition["course_credit"],
            }
        )

    students = sorted(
        students_by_id.values(),
        key=lambda item: (-item["total_debt"], item["last_name"], item["first_name"], item["student_id"]),
    )

    for student in students:
        student["courses"].sort(
            key=lambda item: (-item["remaining_debt"], item["course_title"], item["enrollment_id"])
        )

    return {
        "as_of_date": cutoff.isoformat(),
        "currency": "toman",
        "indebted_student_count": len(students),
        "total_debt": sum(item["total_debt"] for item in students),
        "students": students,
    }


def get_course_financial_report(
    db: Session,
    course_id: int,
    as_of_date: date | None = None,
):
    """Aggregate financial information for one course, grouped by student."""
    cutoff = as_of_date or date.today()
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="دوره پیدا نشد.")

    enrollments = (
        db.query(CourseEnrollment)
        .options(joinedload(CourseEnrollment.student), joinedload(CourseEnrollment.course))
        .filter(CourseEnrollment.course_id == course_id)
        .order_by(CourseEnrollment.student_id, CourseEnrollment.start_date, CourseEnrollment.id)
        .all()
    )

    students_by_id: dict[int, dict] = {}
    totals = {
        "billable_session_count": 0,
        "total_tuition": 0,
        "allocated_amount": 0,
        "remaining_debt": 0,
        "course_credit": 0,
    }

    for enrollment in enrollments:
        tuition = get_enrollment_tuition(db, enrollment.id, cutoff)
        student = enrollment.student
        row = students_by_id.setdefault(
            student.id,
            {
                "student_id": student.id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "full_name": f"{student.first_name} {student.last_name}",
                "national_code": student.national_code,
                "billable_session_count": 0,
                "total_tuition": 0,
                "allocated_amount": 0,
                "remaining_debt": 0,
                "course_credit": 0,
                "enrollments": [],
            },
        )

        for key in totals:
            value = tuition[key]
            totals[key] += value
            row[key] += value

        row["enrollments"].append(
            {
                "enrollment_id": enrollment.id,
                "start_date": enrollment.start_date.isoformat(),
                "end_date": enrollment.end_date.isoformat() if enrollment.end_date else None,
                "billable_session_count": tuition["billable_session_count"],
                "price_per_session": tuition["price_per_session"],
                "total_tuition": tuition["total_tuition"],
                "allocated_amount": tuition["allocated_amount"],
                "remaining_debt": tuition["remaining_debt"],
                "course_credit": tuition["course_credit"],
            }
        )

    students = sorted(
        students_by_id.values(),
        key=lambda item: (-item["remaining_debt"], item["last_name"], item["first_name"], item["student_id"]),
    )

    return {
        "course_id": course.id,
        "course_title": course.title,
        "as_of_date": cutoff.isoformat(),
        "currency": "toman",
        "student_count": len(students),
        "enrollment_count": len(enrollments),
        **totals,
        "students": students,
    }
