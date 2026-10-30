
from app.database.session import SessionLocal
from app.features.classrooms.model import Classroom


address = (
    "سهند فاز 1 محله سوم - بهارستان 25 - "
    "پاساژ شهریار - طبقه دوم - واحد 4 - آموزشگاه سپاس"
)

classrooms = [
    {
        "name": "کلاس هنر",
        "address": address,
        "latitude": 37.947391,
        "longitude": 46.109787,
        "capacity": 10,
    },
    {
        "name": "کلاس هوشمند",
        "address": address,
        "latitude": 37.947391,
        "longitude": 46.109787,
        "capacity": 10,
    },
    {
        "name": "کلاس عمومی",
        "address": address,
        "latitude": 37.947391,
        "longitude": 46.109787,
        "capacity": 15,
    },
]

db = SessionLocal()

try:
    for classroom_data in classrooms:
        exists = db.query(Classroom).filter_by(
            name=classroom_data["name"]
        ).first()

        if not exists:
            db.add(Classroom(**classroom_data))

    db.commit()
    print("اطلاعات کلاس‌ها با موفقیت ذخیره شد.")

except Exception:
    db.rollback()
    raise

finally:
    db.close()
