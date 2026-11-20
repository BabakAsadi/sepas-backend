from datetime import date
from pydantic import BaseModel, Field


class CourseSchedulePayload(BaseModel):
    course_id: int = Field(gt=0)
    teacher_id: int = Field(gt=0)
    classroom_id: int = Field(gt=0)
    weekday: str = Field(min_length=1, max_length=20)
    start_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    effective_from: date
    effective_until: date | None = None
