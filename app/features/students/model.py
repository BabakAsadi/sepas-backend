
from sqlalchemy import Column, Integer, String, UniqueConstraint

from app.database.base import Base


class Student(Base):
    __tablename__ = "students"

    __table_args__ = (
        UniqueConstraint(
            "national_code",
            name="uq_students_national_code",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)

    national_code = Column(String(10), nullable=False)

    grade = Column(String(50), nullable=False)
    field = Column(String(100), nullable=False)

    father_name = Column(String(100), nullable=False)

    phone = Column(String(30), nullable=False)
    phone2 = Column(String(30), nullable=True)
