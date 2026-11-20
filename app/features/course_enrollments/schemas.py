from datetime import date

from pydantic import BaseModel, Field, model_validator


class CourseEnrollmentPayload(BaseModel):
    student_id: int = Field(gt=0)
    course_id: int = Field(gt=0)
    start_date: date
    end_date: date | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError("تاریخ پایان عضویت نمی‌تواند قبل از تاریخ شروع باشد.")
        return self
