from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator


OccurrenceStatus = Literal["held", "cancelled", "moved"]


class GenerateOccurrencesPayload(BaseModel):
    through_date: date


class OccurrenceStatusPayload(BaseModel):
    status: OccurrenceStatus
    session_date: date | None = None

    @model_validator(mode="after")
    def validate_moved_date(self):
        if self.status == "moved" and self.session_date is None:
            raise ValueError("برای جلسه جابه‌جاشده، تاریخ جدید الزامی است.")
        return self
