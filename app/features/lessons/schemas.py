from pydantic import BaseModel, Field


class LessonPayload(BaseModel):
    name: str = Field(min_length=1)
    grade: str = Field(min_length=1)
    field: str = Field(min_length=1)