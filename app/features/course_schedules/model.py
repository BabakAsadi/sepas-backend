from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database.base import Base


class CourseSchedule(Base):
    __tablename__ = "course_schedules"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False, index=True)
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False, index=True)

    weekday = Column(String(20), nullable=False)
    start_time = Column(String(5), nullable=False)
    end_time = Column(String(5), nullable=False)

    # A schedule applies from effective_from through effective_until (inclusive).
    # A NULL effective_until means that the schedule has no planned end date.
    effective_from = Column(Date, nullable=False)
    effective_until = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    course = relationship("Course", backref="schedules")
    teacher = relationship("Teacher")
    classroom = relationship("Classroom")
