
import models
from database import SessionLocal, Base, engine

Base.metadata.create_all(bind=engine)

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
        exists = db.query(models.Teacher).filter_by(
            phone=teacher_data["phone"]
        ).first()

        if not exists:
            db.add(models.Teacher(**teacher_data))

    db.commit()
    print("اطلاعات مدرس‌ها با موفقیت ذخیره شد.")
except Exception:
    db.rollback()
    raise
finally:
    db.close()
