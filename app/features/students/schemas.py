
from pydantic import BaseModel, Field


class StudentPayload(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)

    national_code: str = Field(
        min_length=10,
        max_length=10,
        pattern=r"^\d{10}$",
    )

    grade: str = Field(min_length=1, max_length=50)
    field: str = Field(min_length=1, max_length=100)

    father_name: str = Field(min_length=1, max_length=100)

    phone: str = Field(min_length=1, max_length=30)
    phone2: str | None = Field(default=None, max_length=30)


class StudentDeletionPreview(BaseModel):
    student_id: int
    student_name: str
    enrollment_count: int
    transaction_count: int
    wallet_balance: int
    has_user_account: bool