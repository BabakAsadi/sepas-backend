
import models
from database import SessionLocal, Base, engine

Base.metadata.create_all(bind=engine)

lessons = []


def add_lessons(grade, field, names):
    for name in names:
        lessons.append({
            "grade": grade,
            "field": field,
            "name": name,
        })


# متوسطه اول
middle_school_lessons = [
    "ریاضی",
    "علوم",
    "عربی",
    "ادبیات فارسی",
]

for grade in ["هفتم", "هشتم", "نهم"]:
    add_lessons(
        f"متوسطه اول - {grade}",
        "بدون رشته",
        middle_school_lessons,
    )


# متوسطه دوم - رشته ریاضی فیزیک
add_lessons(
    "متوسطه دوم - دهم",
    "ریاضی فیزیک",
    [
        "ریاضی", "هندسه", "شیمی", "فیزیک",
        "عربی", "ادبیات فارسی", "دین و زندگی",
        "زبان انگلیسی",
    ],
)

add_lessons(
    "متوسطه دوم - یازدهم",
    "ریاضی فیزیک",
    [
        "حسابان", "هندسه", "آمار و احتمال",
        "فیزیک", "شیمی", "عربی", "ادبیات فارسی",
        "دین و زندگی", "زبان انگلیسی",
    ],
)

add_lessons(
    "متوسطه دوم - دوازدهم",
    "ریاضی فیزیک",
    [
        "حسابان", "هندسه", "گسسته", "فیزیک",
        "شیمی", "دین و زندگی", "ادبیات فارسی",
        "زبان انگلیسی",
    ],
)


# متوسطه دوم - رشته تجربی
experimental_lessons = [
    "ریاضی", "فیزیک", "شیمی", "زیست",
    "ادبیات فارسی", "عربی", "دین و زندگی",
    "زبان انگلیسی",
]

for grade in ["دهم", "یازدهم", "دوازدهم"]:
    add_lessons(
        f"متوسطه دوم - {grade}",
        "تجربی",
        experimental_lessons,
    )


# متوسطه دوم - رشته انسانی
humanities_lessons = [
    "ریاضی",
    "عربی",
    "ادبیات فارسی",
    "زبان انگلیسی",
    "فلسفه",
]

for grade in ["دهم", "یازدهم", "دوازدهم"]:
    add_lessons(
        f"متوسطه دوم - {grade}",
        "انسانی",
        humanities_lessons,
    )


# ذخیره در دیتابیس، بدون ثبت رکورد تکراری
db = SessionLocal()

try:
    inserted_count = 0
    skipped_count = 0

    for lesson_data in lessons:
        exists = db.query(models.Lesson).filter_by(
            grade=lesson_data["grade"],
            field=lesson_data["field"],
            name=lesson_data["name"],
        ).first()

        if exists:
            skipped_count += 1
            continue

        db.add(models.Lesson(**lesson_data))
        inserted_count += 1

    db.commit()

    print(f"تعداد درس‌های جدید ثبت‌شده: {inserted_count}")
    print(f"تعداد درس‌های تکراری ردشده: {skipped_count}")
    print(f"تعداد کل درس‌های تعریف‌شده: {len(lessons)}")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
