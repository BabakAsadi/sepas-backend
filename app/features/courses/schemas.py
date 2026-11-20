from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


CourseStatus = Literal["pending", "active", "completed"]


class CoursePayload(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    lesson_id: int = Field(gt=0)
    # All monetary values in this feature are stored as integer toman.
    price_per_session: int = Field(gt=0)
    start_date: date
    status: CourseStatus = "pending"
