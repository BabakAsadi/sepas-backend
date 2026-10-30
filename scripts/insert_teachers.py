
from app.database.session import SessionLocal
from app.features.teachers.model import Teacher

teachers = [
    {
        "first_name": "مهدی",
        "last_name": "اسدی",
        "phone": "09354007978",
        "photo": None,
    },
    {
        "first_name": "رضا",
        "last_name": "دهقان پور",
        "phone": "09142380225",
        "photo": None,
    },
    {
        "first_name": "پویا",
        "last_name": "حمامی",
        "phone": "09339505076",
        "photo": None,
    },
]

db = SessionLocal()

try:
    for teacher_data in teachers:
        exists = db.query(Teacher).filter_by(
            phone=teacher_data["phone"]
        ).first()

        if not exists:
            db.add(Teacher(**teacher_data))

    db.commit()
    print("اطلاعات مدرس‌ها با موفقیت ذخیره شد.")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
