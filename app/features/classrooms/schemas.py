
from pydantic import BaseModel, Field


class ClassroomPayload(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    address: str = Field(min_length=1)
    capacity: int = Field(gt=0)
    latitude: float | None = None
    longitude: float | None = None
