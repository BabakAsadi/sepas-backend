from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Index,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class CourseEnrollment(Base):
    __tablename__ = "course_enrollments"
    __table_args__ = (
        CheckConstraint(
            "end_date IS NULL OR end_date >= start_date",
            name="ck_course_enrollment_dates",
        ),
        Index(
            "ix_course_enrollment_student_course",
            "student_id",
            "course_id",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False,
        index=True,
    )
    course_id = Column(
        Integer,
        ForeignKey("courses.id"),
        nullable=False,
        index=True,
    )
    start_date = Column(Date, nullable=False)
    # Inclusive last date of enrollment. NULL means the enrollment is ongoing.
    end_date = Column(Date, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    student = relationship("Student")
    course = relationship("Course")
