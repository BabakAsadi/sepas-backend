
from pydantic import BaseModel, Field


class SessionPayload(BaseModel):
    lesson_id: int = Field(gt=0)
    teacher_id: int = Field(gt=0)
    classroom_id: int = Field(gt=0)

    weekday: str = Field(min_length=1)
    start_time: str
    end_time: str

    registered_count: int = Field(default=0, ge=0)
