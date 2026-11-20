from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class CourseOccurrence(Base):
    __tablename__ = "course_occurrences"
    __table_args__ = (
        UniqueConstraint(
            "course_schedule_id",
            "scheduled_date",
            name="uq_course_occurrence_schedule_date",
        ),
        CheckConstraint(
            "status IN ('held', 'cancelled', 'moved')",
            name="ck_course_occurrence_status",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    # Keep the schedule reference nullable so historical occurrences can survive
    # if a schedule is eventually archived/deleted. The snapshot fields below
    # preserve the original teacher, classroom and time.
    course_schedule_id = Column(
        Integer,
        ForeignKey("course_schedules.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False)

    scheduled_date = Column(Date, nullable=False, index=True)
    session_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(String(20), nullable=False, default="held")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    course = relationship("Course")
    teacher = relationship("Teacher")
    classroom = relationship("Classroom")
    schedule = relationship("CourseSchedule")
