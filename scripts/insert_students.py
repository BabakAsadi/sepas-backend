import random

from app.database.session import SessionLocal
from app.features.students.model import Student


first_names = [
    "آراد", "پارسا", "امیرعلی", "محمد", "علی",
    "آرین", "سامیار", "کیان", "ماهان", "طاها",
    "نیما", "سینا", "یاسین", "بردیا", "اشکان",
    "هلیا", "نیکا", "باران", "آوا", "رها",
]

last_names = [
    "محمدی", "احمدی", "کریمی", "حسینی", "رضایی",
    "جعفری", "موسوی", "مرادی", "اکبری", "صادقی",
    "قاسمی", "رحیمی", "نجفی", "شریفی", "کاظمی",
]

father_names = [
    "حسین", "محمد", "علی", "رضا", "مهدی",
    "احمد", "امیر", "مجید", "حمید", "حسن",
]

grades = [
    "هفتم",
    "هشتم",
    "نهم",
    "دهم",
    "یازدهم",
    "دوازدهم",
]

fields = [
    "ریاضی فیزیک",
    "علوم تجربی",
    "علوم انسانی",
    "عمومی",
]


def generate_national_code(number: int) -> str:
    """
    Generate a 10-digit national code with a valid checksum.
    """
    digits = [int(digit) for digit in f"{number:09d}"]

    checksum_sum = sum(
        digit * (10 - index)
        for index, digit in enumerate(digits)
    )

    remainder = checksum_sum % 11

    check_digit = remainder if remainder < 2 else 11 - remainder

    return "".join(map(str, digits)) + str(check_digit)


def generate_students():
    rng = random.Random(42)
    students = []

    # Deterministic codes make the script safe to run repeatedly.
    for index in range(100):
        national_code = generate_national_code(900000000 + index)

        students.append({
            "first_name": rng.choice(first_names),
            "last_name": rng.choice(last_names),
            "national_code": national_code,
            "grade": rng.choice(grades),
            "field": rng.choice(fields),
            "father_name": rng.choice(father_names),
            "phone": f"0912{rng.randint(1000000, 9999999)}",
            "phone2": None,
        })

    return students


db = SessionLocal()

try:
    students = generate_students()

    existing_codes = {
        row[0]
        for row in db.query(Student.national_code).all()
    }

    added_count = 0

    for student_data in students:
        if student_data["national_code"] in existing_codes:
            continue

        db.add(Student(**student_data))
        added_count += 1

    db.commit()

    print(f"{added_count} دانش‌آموز جدید با موفقیت اضافه شدند.")

except Exception:
    db.rollback()
    raise

finally:
    db.close()