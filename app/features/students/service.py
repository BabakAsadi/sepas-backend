
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.features.students.model import Student
from app.features.students.schemas import StudentPayload


def normalize_text(value: str) -> str:
    return value.strip()


def is_valid_iranian_national_code(code: str) -> bool:
    """
    اعتبارسنجی ساختار و رقم کنترل کد ملی ایران.
    """

    if not code or len(code) != 10 or not code.isdigit():
        return False

    # کدهایی که تمام ارقامشان یکسان است معتبر نیستند.
    if len(set(code)) == 1:
        return False

    digits = [int(digit) for digit in code]

    checksum = sum(
        digits[index] * (10 - index)
        for index in range(9)
    )

    remainder = checksum % 11
    control_digit = digits[9]

    expected_digit = (
        remainder if remainder < 2 else 11 - remainder
    )

    return control_digit == expected_digit


def normalize_payload(data: StudentPayload) -> dict:
    values = {
        "first_name": normalize_text(data.first_name),
        "last_name": normalize_text(data.last_name),
        "national_code": data.national_code.strip(),
        "grade": normalize_text(data.grade),
        "field": normalize_text(data.field),
        "father_name": normalize_text(data.father_name),
        "phone": data.phone.strip(),
        "phone2": data.phone2.strip() if data.phone2 else None,
    }

    required_fields = (
        "first_name",
        "last_name",
        "national_code",
        "grade",
        "field",
        "father_name",
        "phone",
    )

    if any(not values[field] for field in required_fields):
        raise HTTPException(
            status_code=422,
            detail="تمام فیلدهای الزامی باید مقدار داشته باشند.",
        )

    if not is_valid_iranian_national_code(values["national_code"]):
        raise HTTPException(
            status_code=422,
            detail="کد ملی واردشده معتبر نیست.",
        )

    return values


def validate_national_code(
    db: Session,
    national_code: str,
    exclude_student_id: int | None = None,
):
    query = db.query(Student).filter(
        Student.national_code == national_code
    )

    if exclude_student_id is not None:
        query = query.filter(
            Student.id != exclude_student_id
        )

    if query.first():
        raise HTTPException(
            status_code=409,
            detail="این کد ملی قبلاً برای دانش‌آموز دیگری ثبت شده است.",
        )


def commit_student_changes(db: Session):
    """
    مدیریت خطای Unique Constraint کد ملی،
    مخصوصاً در درخواست‌های هم‌زمان.
    """

    try:
        db.commit()

    except IntegrityError as exc:
        db.rollback()

        error_message = str(exc.orig)

        if (
            "uq_students_national_code" in error_message
            or "students.national_code" in error_message
        ):
            raise HTTPException(
                status_code=409,
                detail="این کد ملی قبلاً برای دانش‌آموز دیگری ثبت شده است.",
            ) from exc

        # خطاهای دیگر دیتابیس نباید به‌اشتباه
        # خطای کد ملی تکراری گزارش شوند.
        raise


def get_students(db: Session):
    return (
        db.query(Student)
        .order_by(Student.first_name, Student.last_name)
        .all()
    )


def get_student(db: Session, student_id: int):
    student = db.get(Student, student_id)

    if not student:
        raise HTTPException(
            status_code=404,
            detail="دانش‌آموز پیدا نشد.",
        )

    return student


def create_student(db: Session, data: StudentPayload):
    values = normalize_payload(data)

    validate_national_code(
        db,
        values["national_code"],
    )

    student = Student(**values)

    db.add(student)
    commit_student_changes(db)
    db.refresh(student)

    return student


def update_student(
    db: Session,
    student_id: int,
    data: StudentPayload,
):
    student = get_student(db, student_id)

    values = normalize_payload(data)

    validate_national_code(
        db,
        values["national_code"],
        exclude_student_id=student_id,
    )

    for field, value in values.items():
        setattr(student, field, value)

    commit_student_changes(db)
    db.refresh(student)

    return student


def delete_student(db: Session, student_id: int):
    student = get_student(db, student_id)

    try:
        db.delete(student)
        db.commit()

    except Exception:
        db.rollback()
        raise
