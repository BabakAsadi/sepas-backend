
# Import legacy Sepas timetable data into the new course models.
# Run from backend root: python scripts/seed_legacy_courses.py
# Idempotent and non-destructive: inserts missing records, preserves matching
# existing records, aborts on conflicting IDs, does not delete old sessions,
# and does not generate CourseOccurrence rows.

from __future__ import annotations
import json
import sys
from datetime import date
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import app.database.models  # noqa: F401
from app.database.session import SessionLocal
from app.features.teachers.model import Teacher
from app.features.classrooms.model import Classroom
from app.features.lessons.model import Lesson
from app.features.courses.model import Course
from app.features.course_schedules.model import CourseSchedule

START_DATE = date(2026, 10, 23)  # 1 Aban 1405
PRICE_PER_SESSION = 100_000  # toman
WEEKDAYS = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]

DATA = json.loads(r'''{
    "teachers": [
        {
            "id": 1,
            "first_name": "مهدی",
            "last_name": "اسدی",
            "phone": "09354007978",
            "photo": null
        },
        {
            "id": 2,
            "first_name": "رضا",
            "last_name": "دهقان پور",
            "phone": "09142380225",
            "photo": null
        },
        {
            "id": 3,
            "first_name": "پویا",
            "last_name": "حمامی",
            "phone": "09339505076",
            "photo": null
        }
    ],
    "classrooms": [
        {
            "id": 1,
            "name": "کلاس هنر",
            "address": "سهند فاز 1 محله سوم - بهارستان 25 - پاساژ شهریار - طبقه دوم - واحد 4 - آموزشگاه سپاس",
            "capacity": 10,
            "latitude": 37.947391,
            "longitude": 46.109787
        },
        {
            "id": 2,
            "name": "کلاس هوشمند",
            "address": "سهند فاز 1 محله سوم - بهارستان 25 - پاساژ شهریار - طبقه دوم - واحد 4 - آموزشگاه سپاس",
            "capacity": 10,
            "latitude": 37.947391,
            "longitude": 46.109787
        },
        {
            "id": 3,
            "name": "کلاس عمومی",
            "address": "سهند فاز 1 محله سوم - بهارستان 25 - پاساژ شهریار - طبقه دوم - واحد 4 - آموزشگاه سپاس",
            "capacity": 15,
            "latitude": 37.947391,
            "longitude": 46.109787
        }
    ],
    "lessons": [
        {
            "id": 1,
            "name": "ریاضی",
            "grade": "متوسطه اول - هفتم",
            "field": "بدون رشته"
        },
        {
            "id": 2,
            "name": "علوم",
            "grade": "متوسطه اول - هفتم",
            "field": "بدون رشته"
        },
        {
            "id": 3,
            "name": "عربی",
            "grade": "متوسطه اول - هفتم",
            "field": "بدون رشته"
        },
        {
            "id": 4,
            "name": "ادبیات فارسی",
            "grade": "متوسطه اول - هفتم",
            "field": "بدون رشته"
        },
        {
            "id": 5,
            "name": "ریاضی",
            "grade": "متوسطه اول - هشتم",
            "field": "بدون رشته"
        },
        {
            "id": 6,
            "name": "علوم",
            "grade": "متوسطه اول - هشتم",
            "field": "بدون رشته"
        },
        {
            "id": 7,
            "name": "عربی",
            "grade": "متوسطه اول - هشتم",
            "field": "بدون رشته"
        },
        {
            "id": 8,
            "name": "ادبیات فارسی",
            "grade": "متوسطه اول - هشتم",
            "field": "بدون رشته"
        },
        {
            "id": 9,
            "name": "ریاضی",
            "grade": "متوسطه اول - نهم",
            "field": "بدون رشته"
        },
        {
            "id": 10,
            "name": "علوم",
            "grade": "متوسطه اول - نهم",
            "field": "بدون رشته"
        },
        {
            "id": 11,
            "name": "عربی",
            "grade": "متوسطه اول - نهم",
            "field": "بدون رشته"
        },
        {
            "id": 12,
            "name": "ادبیات فارسی",
            "grade": "متوسطه اول - نهم",
            "field": "بدون رشته"
        },
        {
            "id": 13,
            "name": "ریاضی",
            "grade": "متوسطه دوم - دهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 14,
            "name": "هندسه",
            "grade": "متوسطه دوم - دهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 15,
            "name": "شیمی",
            "grade": "متوسطه دوم - دهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 16,
            "name": "فیزیک",
            "grade": "متوسطه دوم - دهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 17,
            "name": "عربی",
            "grade": "متوسطه دوم - دهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 18,
            "name": "ادبیات فارسی",
            "grade": "متوسطه دوم - دهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 19,
            "name": "دین و زندگی",
            "grade": "متوسطه دوم - دهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 20,
            "name": "زبان انگلیسی",
            "grade": "متوسطه دوم - دهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 21,
            "name": "حسابان",
            "grade": "متوسطه دوم - یازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 23,
            "name": "آمار و احتمال",
            "grade": "متوسطه دوم - یازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 24,
            "name": "فیزیک",
            "grade": "متوسطه دوم - یازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 25,
            "name": "شیمی",
            "grade": "متوسطه دوم - یازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 26,
            "name": "عربی",
            "grade": "متوسطه دوم - یازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 27,
            "name": "ادبیات فارسی",
            "grade": "متوسطه دوم - یازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 28,
            "name": "دین و زندگی",
            "grade": "متوسطه دوم - یازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 29,
            "name": "زبان انگلیسی",
            "grade": "متوسطه دوم - یازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 30,
            "name": "حسابان",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 31,
            "name": "هندسه",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 32,
            "name": "گسسته",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 33,
            "name": "فیزیک",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 34,
            "name": "شیمی",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 35,
            "name": "دین و زندگی",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 36,
            "name": "ادبیات فارسی",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 37,
            "name": "زبان انگلیسی",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "ریاضی فیزیک"
        },
        {
            "id": 38,
            "name": "ریاضی",
            "grade": "متوسطه دوم - دهم",
            "field": "تجربی"
        },
        {
            "id": 39,
            "name": "فیزیک",
            "grade": "متوسطه دوم - دهم",
            "field": "تجربی"
        },
        {
            "id": 40,
            "name": "شیمی",
            "grade": "متوسطه دوم - دهم",
            "field": "تجربی"
        },
        {
            "id": 41,
            "name": "زیست",
            "grade": "متوسطه دوم - دهم",
            "field": "تجربی"
        },
        {
            "id": 42,
            "name": "ادبیات فارسی",
            "grade": "متوسطه دوم - دهم",
            "field": "تجربی"
        },
        {
            "id": 43,
            "name": "عربی",
            "grade": "متوسطه دوم - دهم",
            "field": "تجربی"
        },
        {
            "id": 44,
            "name": "دین و زندگی",
            "grade": "متوسطه دوم - دهم",
            "field": "تجربی"
        },
        {
            "id": 45,
            "name": "زبان انگلیسی",
            "grade": "متوسطه دوم - دهم",
            "field": "تجربی"
        },
        {
            "id": 46,
            "name": "ریاضی",
            "grade": "متوسطه دوم - یازدهم",
            "field": "تجربی"
        },
        {
            "id": 47,
            "name": "فیزیک",
            "grade": "متوسطه دوم - یازدهم",
            "field": "تجربی"
        },
        {
            "id": 48,
            "name": "شیمی",
            "grade": "متوسطه دوم - یازدهم",
            "field": "تجربی"
        },
        {
            "id": 49,
            "name": "زیست",
            "grade": "متوسطه دوم - یازدهم",
            "field": "تجربی"
        },
        {
            "id": 50,
            "name": "ادبیات فارسی",
            "grade": "متوسطه دوم - یازدهم",
            "field": "تجربی"
        },
        {
            "id": 51,
            "name": "عربی",
            "grade": "متوسطه دوم - یازدهم",
            "field": "تجربی"
        },
        {
            "id": 52,
            "name": "دین و زندگی",
            "grade": "متوسطه دوم - یازدهم",
            "field": "تجربی"
        },
        {
            "id": 53,
            "name": "زبان انگلیسی",
            "grade": "متوسطه دوم - یازدهم",
            "field": "تجربی"
        },
        {
            "id": 54,
            "name": "ریاضی",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "تجربی"
        },
        {
            "id": 55,
            "name": "فیزیک",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "تجربی"
        },
        {
            "id": 56,
            "name": "شیمی",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "تجربی"
        },
        {
            "id": 57,
            "name": "زیست",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "تجربی"
        },
        {
            "id": 58,
            "name": "ادبیات فارسی",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "تجربی"
        },
        {
            "id": 59,
            "name": "عربی",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "تجربی"
        },
        {
            "id": 60,
            "name": "دین و زندگی",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "تجربی"
        },
        {
            "id": 61,
            "name": "زبان انگلیسی",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "تجربی"
        },
        {
            "id": 62,
            "name": "ریاضی",
            "grade": "متوسطه دوم - دهم",
            "field": "انسانی"
        },
        {
            "id": 63,
            "name": "عربی",
            "grade": "متوسطه دوم - دهم",
            "field": "انسانی"
        },
        {
            "id": 64,
            "name": "ادبیات فارسی",
            "grade": "متوسطه دوم - دهم",
            "field": "انسانی"
        },
        {
            "id": 65,
            "name": "زبان انگلیسی",
            "grade": "متوسطه دوم - دهم",
            "field": "انسانی"
        },
        {
            "id": 66,
            "name": "فلسفه",
            "grade": "متوسطه دوم - دهم",
            "field": "انسانی"
        },
        {
            "id": 67,
            "name": "ریاضی",
            "grade": "متوسطه دوم - یازدهم",
            "field": "انسانی"
        },
        {
            "id": 68,
            "name": "عربی",
            "grade": "متوسطه دوم - یازدهم",
            "field": "انسانی"
        },
        {
            "id": 69,
            "name": "ادبیات فارسی",
            "grade": "متوسطه دوم - یازدهم",
            "field": "انسانی"
        },
        {
            "id": 70,
            "name": "زبان انگلیسی",
            "grade": "متوسطه دوم - یازدهم",
            "field": "انسانی"
        },
        {
            "id": 71,
            "name": "فلسفه",
            "grade": "متوسطه دوم - یازدهم",
            "field": "انسانی"
        },
        {
            "id": 72,
            "name": "ریاضی",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "انسانی"
        },
        {
            "id": 73,
            "name": "عربی",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "انسانی"
        },
        {
            "id": 74,
            "name": "ادبیات فارسی",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "انسانی"
        },
        {
            "id": 75,
            "name": "زبان انگلیسی",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "انسانی"
        },
        {
            "id": 76,
            "name": "فلسفه",
            "grade": "متوسطه دوم - دوازدهم",
            "field": "انسانی"
        }
    ],
    "courses": [
        {
            "id": 23,
            "lesson_id": 46,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه دوم - یازدهم",
            "lesson_field": "تجربی",
            "teacher_id": 1,
            "classroom_id": 1,
            "weekday": "جمعه",
            "start_time": "08:00",
            "end_time": "10:30"
        },
        {
            "id": 24,
            "lesson_id": 47,
            "lesson_name": "فیزیک",
            "lesson_grade": "متوسطه دوم - یازدهم",
            "lesson_field": "تجربی",
            "teacher_id": 1,
            "classroom_id": 1,
            "weekday": "جمعه",
            "start_time": "11:30",
            "end_time": "13:30"
        },
        {
            "id": 31,
            "lesson_id": 62,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه دوم - دهم",
            "lesson_field": "انسانی",
            "teacher_id": 1,
            "classroom_id": 1,
            "weekday": "جمعه",
            "start_time": "18:00",
            "end_time": "19:30"
        },
        {
            "id": 7,
            "lesson_id": 9,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه اول - نهم",
            "lesson_field": "بدون رشته",
            "teacher_id": 1,
            "classroom_id": 3,
            "weekday": "دوشنبه",
            "start_time": "13:30",
            "end_time": "15:00"
        },
        {
            "id": 27,
            "lesson_id": 9,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه اول - نهم",
            "lesson_field": "بدون رشته",
            "teacher_id": 1,
            "classroom_id": 3,
            "weekday": "دوشنبه",
            "start_time": "15:30",
            "end_time": "17:00"
        },
        {
            "id": 39,
            "lesson_id": 5,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه اول - هشتم",
            "lesson_field": "بدون رشته",
            "teacher_id": 2,
            "classroom_id": 1,
            "weekday": "دوشنبه",
            "start_time": "15:30",
            "end_time": "17:00"
        },
        {
            "id": 28,
            "lesson_id": 9,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه اول - نهم",
            "lesson_field": "بدون رشته",
            "teacher_id": 1,
            "classroom_id": 1,
            "weekday": "دوشنبه",
            "start_time": "17:30",
            "end_time": "19:00"
        },
        {
            "id": 36,
            "lesson_id": 12,
            "lesson_name": "ادبیات فارسی",
            "lesson_grade": "متوسطه اول - نهم",
            "lesson_field": "بدون رشته",
            "teacher_id": 2,
            "classroom_id": 3,
            "weekday": "دوشنبه",
            "start_time": "17:30",
            "end_time": "19:00"
        },
        {
            "id": 9,
            "lesson_id": 9,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه اول - نهم",
            "lesson_field": "بدون رشته",
            "teacher_id": 1,
            "classroom_id": 3,
            "weekday": "دوشنبه",
            "start_time": "19:00",
            "end_time": "20:30"
        },
        {
            "id": 37,
            "lesson_id": 58,
            "lesson_name": "ادبیات فارسی",
            "lesson_grade": "متوسطه دوم - دوازدهم",
            "lesson_field": "تجربی",
            "teacher_id": 2,
            "classroom_id": 2,
            "weekday": "دوشنبه",
            "start_time": "19:00",
            "end_time": "20:30"
        },
        {
            "id": 33,
            "lesson_id": 57,
            "lesson_name": "زیست",
            "lesson_grade": "متوسطه دوم - دوازدهم",
            "lesson_field": "تجربی",
            "teacher_id": 3,
            "classroom_id": 2,
            "weekday": "سه‌شنبه",
            "start_time": "14:30",
            "end_time": "16:00"
        },
        {
            "id": 40,
            "lesson_id": 5,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه اول - هشتم",
            "lesson_field": "بدون رشته",
            "teacher_id": 2,
            "classroom_id": 3,
            "weekday": "سه‌شنبه",
            "start_time": "15:30",
            "end_time": "17:00"
        },
        {
            "id": 12,
            "lesson_id": 1,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه اول - هفتم",
            "lesson_field": "بدون رشته",
            "teacher_id": 1,
            "classroom_id": 2,
            "weekday": "سه‌شنبه",
            "start_time": "16:00",
            "end_time": "17:30"
        },
        {
            "id": 32,
            "lesson_id": 61,
            "lesson_name": "زبان انگلیسی",
            "lesson_grade": "متوسطه دوم - دوازدهم",
            "lesson_field": "تجربی",
            "teacher_id": 3,
            "classroom_id": 1,
            "weekday": "سه‌شنبه",
            "start_time": "16:15",
            "end_time": "17:45"
        },
        {
            "id": 38,
            "lesson_id": 11,
            "lesson_name": "عربی",
            "lesson_grade": "متوسطه اول - نهم",
            "lesson_field": "بدون رشته",
            "teacher_id": 2,
            "classroom_id": 3,
            "weekday": "سه‌شنبه",
            "start_time": "17:00",
            "end_time": "18:30"
        },
        {
            "id": 29,
            "lesson_id": 1,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه اول - هفتم",
            "lesson_field": "بدون رشته",
            "teacher_id": 1,
            "classroom_id": 1,
            "weekday": "سه‌شنبه",
            "start_time": "18:00",
            "end_time": "19:30"
        },
        {
            "id": 8,
            "lesson_id": 10,
            "lesson_name": "علوم",
            "lesson_grade": "متوسطه اول - نهم",
            "lesson_field": "بدون رشته",
            "teacher_id": 3,
            "classroom_id": 3,
            "weekday": "سه‌شنبه",
            "start_time": "18:30",
            "end_time": "20:00"
        },
        {
            "id": 41,
            "lesson_id": 73,
            "lesson_name": "عربی",
            "lesson_grade": "متوسطه دوم - دوازدهم",
            "lesson_field": "انسانی",
            "teacher_id": 2,
            "classroom_id": 2,
            "weekday": "سه‌شنبه",
            "start_time": "18:45",
            "end_time": "20:15"
        },
        {
            "id": 3,
            "lesson_id": 9,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه اول - نهم",
            "lesson_field": "بدون رشته",
            "teacher_id": 1,
            "classroom_id": 3,
            "weekday": "شنبه",
            "start_time": "13:30",
            "end_time": "15:00"
        },
        {
            "id": 4,
            "lesson_id": 9,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه اول - نهم",
            "lesson_field": "بدون رشته",
            "teacher_id": 1,
            "classroom_id": 3,
            "weekday": "شنبه",
            "start_time": "15:30",
            "end_time": "17:00"
        },
        {
            "id": 25,
            "lesson_id": 9,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه اول - نهم",
            "lesson_field": "بدون رشته",
            "teacher_id": 1,
            "classroom_id": 3,
            "weekday": "شنبه",
            "start_time": "17:00",
            "end_time": "18:30"
        },
        {
            "id": 20,
            "lesson_id": 49,
            "lesson_name": "زیست",
            "lesson_grade": "متوسطه دوم - یازدهم",
            "lesson_field": "تجربی",
            "teacher_id": 3,
            "classroom_id": 3,
            "weekday": "پنجشنبه",
            "start_time": "08:00",
            "end_time": "10:30"
        },
        {
            "id": 21,
            "lesson_id": 48,
            "lesson_name": "شیمی",
            "lesson_grade": "متوسطه دوم - یازدهم",
            "lesson_field": "تجربی",
            "teacher_id": 3,
            "classroom_id": 3,
            "weekday": "پنجشنبه",
            "start_time": "10:30",
            "end_time": "12:45"
        },
        {
            "id": 45,
            "lesson_id": 2,
            "lesson_name": "علوم",
            "lesson_grade": "متوسطه اول - هفتم",
            "lesson_field": "بدون رشته",
            "teacher_id": 2,
            "classroom_id": 1,
            "weekday": "پنجشنبه",
            "start_time": "11:00",
            "end_time": "12:30"
        },
        {
            "id": 46,
            "lesson_id": 2,
            "lesson_name": "علوم",
            "lesson_grade": "متوسطه اول - هفتم",
            "lesson_field": "بدون رشته",
            "teacher_id": 2,
            "classroom_id": 1,
            "weekday": "پنجشنبه",
            "start_time": "12:30",
            "end_time": "14:00"
        },
        {
            "id": 22,
            "lesson_id": 53,
            "lesson_name": "زبان انگلیسی",
            "lesson_grade": "متوسطه دوم - یازدهم",
            "lesson_field": "تجربی",
            "teacher_id": 3,
            "classroom_id": 3,
            "weekday": "پنجشنبه",
            "start_time": "13:30",
            "end_time": "16:30"
        },
        {
            "id": 42,
            "lesson_id": 73,
            "lesson_name": "عربی",
            "lesson_grade": "متوسطه دوم - دوازدهم",
            "lesson_field": "انسانی",
            "teacher_id": 2,
            "classroom_id": 1,
            "weekday": "پنجشنبه",
            "start_time": "14:00",
            "end_time": "15:45"
        },
        {
            "id": 43,
            "lesson_id": 72,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه دوم - دوازدهم",
            "lesson_field": "انسانی",
            "teacher_id": 2,
            "classroom_id": 1,
            "weekday": "پنجشنبه",
            "start_time": "16:00",
            "end_time": "17:45"
        },
        {
            "id": 49,
            "lesson_id": 61,
            "lesson_name": "زبان انگلیسی",
            "lesson_grade": "متوسطه دوم - دوازدهم",
            "lesson_field": "تجربی",
            "teacher_id": 3,
            "classroom_id": 2,
            "weekday": "پنجشنبه",
            "start_time": "16:45",
            "end_time": "18:15"
        },
        {
            "id": 15,
            "lesson_id": 9,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه اول - نهم",
            "lesson_field": "بدون رشته",
            "teacher_id": 1,
            "classroom_id": 3,
            "weekday": "چهارشنبه",
            "start_time": "13:30",
            "end_time": "15:30"
        },
        {
            "id": 30,
            "lesson_id": 62,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه دوم - دهم",
            "lesson_field": "انسانی",
            "teacher_id": 1,
            "classroom_id": 2,
            "weekday": "چهارشنبه",
            "start_time": "16:00",
            "end_time": "17:30"
        },
        {
            "id": 34,
            "lesson_id": 10,
            "lesson_name": "علوم",
            "lesson_grade": "متوسطه اول - نهم",
            "lesson_field": "بدون رشته",
            "teacher_id": 3,
            "classroom_id": 3,
            "weekday": "چهارشنبه",
            "start_time": "16:00",
            "end_time": "17:30"
        },
        {
            "id": 35,
            "lesson_id": 10,
            "lesson_name": "علوم",
            "lesson_grade": "متوسطه اول - نهم",
            "lesson_field": "بدون رشته",
            "teacher_id": 3,
            "classroom_id": 2,
            "weekday": "چهارشنبه",
            "start_time": "17:30",
            "end_time": "19:00"
        },
        {
            "id": 5,
            "lesson_id": 9,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه اول - نهم",
            "lesson_field": "بدون رشته",
            "teacher_id": 1,
            "classroom_id": 3,
            "weekday": "یکشنبه",
            "start_time": "13:30",
            "end_time": "15:30"
        },
        {
            "id": 44,
            "lesson_id": 2,
            "lesson_name": "علوم",
            "lesson_grade": "متوسطه اول - هفتم",
            "lesson_field": "بدون رشته",
            "teacher_id": 2,
            "classroom_id": 2,
            "weekday": "یکشنبه",
            "start_time": "15:30",
            "end_time": "17:00"
        },
        {
            "id": 26,
            "lesson_id": 1,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه اول - هفتم",
            "lesson_field": "بدون رشته",
            "teacher_id": 1,
            "classroom_id": 1,
            "weekday": "یکشنبه",
            "start_time": "16:00",
            "end_time": "17:30"
        },
        {
            "id": 47,
            "lesson_id": 50,
            "lesson_name": "ادبیات فارسی",
            "lesson_grade": "متوسطه دوم - یازدهم",
            "lesson_field": "تجربی",
            "teacher_id": 2,
            "classroom_id": 2,
            "weekday": "یکشنبه",
            "start_time": "17:00",
            "end_time": "19:15"
        },
        {
            "id": 6,
            "lesson_id": 1,
            "lesson_name": "ریاضی",
            "lesson_grade": "متوسطه اول - هفتم",
            "lesson_field": "بدون رشته",
            "teacher_id": 1,
            "classroom_id": 1,
            "weekday": "یکشنبه",
            "start_time": "18:00",
            "end_time": "19:30"
        },
        {
            "id": 48,
            "lesson_id": 51,
            "lesson_name": "عربی",
            "lesson_grade": "متوسطه دوم - یازدهم",
            "lesson_field": "تجربی",
            "teacher_id": 2,
            "classroom_id": 2,
            "weekday": "یکشنبه",
            "start_time": "19:15",
            "end_time": "21:30"
        }
    ]
}''')


def assert_same(existing, expected: dict, fields: tuple[str, ...], label: str):
    differences = {
        field: (getattr(existing, field), expected[field])
        for field in fields
        if getattr(existing, field) != expected[field]
    }
    if differences:
        details = ", ".join(
            f"{field}: database={old!r}, import={new!r}"
            for field, (old, new) in differences.items()
        )
        identity = expected.get("id", expected.get("course_id"))
        raise RuntimeError(
            f"تعارض در {label} با شناسه {identity}؛ "
            f"برای جلوگیری از بازنویسی، عملیات متوقف شد. {details}"
        )


def validate_source_data():
    courses = DATA["courses"]
    lessons_by_id = {item["id"]: item for item in DATA["lessons"]}
    teacher_ids = {item["id"] for item in DATA["teachers"]}
    classroom_ids = {item["id"] for item in DATA["classrooms"]}

    if len(courses) != 39:
        raise RuntimeError(f"تعداد رکوردهای برنامه باید ۳۹ باشد؛ مقدار فعلی: {len(courses)}")
    course_ids = [item["id"] for item in courses]
    if len(course_ids) != len(set(course_ids)):
        raise RuntimeError("شناسه تکراری در اطلاعات برنامه‌های قدیمی وجود دارد.")

    for item in courses:
        lesson = lessons_by_id.get(item["lesson_id"])
        if lesson is None:
            raise RuntimeError(f"درس با شناسه {item['lesson_id']} در فهرست درس‌ها نیست.")
        if (lesson["name"], lesson["grade"], lesson["field"]) != (
            item["lesson_name"], item["lesson_grade"], item["lesson_field"]
        ):
            raise RuntimeError(f"اطلاعات درس با شناسه {item['lesson_id']} بین فایل‌ها یکسان نیست.")
        if item["teacher_id"] not in teacher_ids:
            raise RuntimeError(f"دبیر با شناسه {item['teacher_id']} تعریف نشده است.")
        if item["classroom_id"] not in classroom_ids:
            raise RuntimeError(f"کلاس با شناسه {item['classroom_id']} تعریف نشده است.")
        if item["weekday"] not in WEEKDAYS:
            raise RuntimeError(f"روز هفته نامعتبر: {item['weekday']}")
        if item["start_time"] >= item["end_time"]:
            raise RuntimeError(f"بازه زمانی نامعتبر در رکورد قدیمی {item['id']}")

    # Check overlaps inside the imported timetable.
    for index, first in enumerate(courses):
        for second in courses[index + 1:]:
            if first["weekday"] != second["weekday"]:
                continue
            overlaps = (
                first["start_time"] < second["end_time"]
                and first["end_time"] > second["start_time"]
            )
            if overlaps and first["teacher_id"] == second["teacher_id"]:
                raise RuntimeError(f"تداخل برنامه دبیر در رکوردهای {first['id']} و {second['id']}")
            if overlaps and first["classroom_id"] == second["classroom_id"]:
                raise RuntimeError(f"تداخل برنامه کلاس در رکوردهای {first['id']} و {second['id']}")


def import_records(db):
    counts = {
        "teachers_created": 0, "teachers_existing": 0,
        "classrooms_created": 0, "classrooms_existing": 0,
        "lessons_created": 0, "lessons_existing": 0,
        "courses_created": 0, "courses_existing": 0,
        "schedules_created": 0, "schedules_existing": 0,
    }

    for item in DATA["teachers"]:
        existing = db.get(Teacher, item["id"])
        if existing:
            assert_same(existing, item, ("first_name", "last_name", "phone"), "دبیر")
            counts["teachers_existing"] += 1
        else:
            db.add(Teacher(**item))
            db.flush()
            counts["teachers_created"] += 1

    for item in DATA["classrooms"]:
        existing = db.get(Classroom, item["id"])
        if existing:
            assert_same(
                existing, item,
                ("name", "address", "capacity", "latitude", "longitude"),
                "کلاس",
            )
            counts["classrooms_existing"] += 1
        else:
            db.add(Classroom(**item))
            db.flush()
            counts["classrooms_created"] += 1

    for item in DATA["lessons"]:
        existing = db.get(Lesson, item["id"])
        if existing:
            assert_same(existing, item, ("name", "grade", "field"), "درس")
            counts["lessons_existing"] += 1
        else:
            db.add(Lesson(**item))
            db.flush()
            counts["lessons_created"] += 1

    lessons_by_id = {item["id"]: item for item in DATA["lessons"]}
    for item in DATA["courses"]:
        course_id = item["id"]
        lesson = lessons_by_id[item["lesson_id"]]
        title = f"{lesson['name']} - {lesson['grade']} - {lesson['field']}"
        expected_course = {
            "id": course_id,
            "title": title,
            "lesson_id": item["lesson_id"],
            "price_per_session": PRICE_PER_SESSION,
            "start_date": START_DATE,
        }

        existing_course = db.get(Course, course_id)
        if existing_course:
            assert_same(
                existing_course, expected_course,
                ("title", "lesson_id", "price_per_session", "start_date"),
                "دوره",
            )
            # Do not reset status on an already-existing course.
            counts["courses_existing"] += 1
        else:
            db.add(Course(**expected_course, status="active"))
            db.flush()
            counts["courses_created"] += 1

        expected_schedule = {
            "course_id": course_id,
            "teacher_id": item["teacher_id"],
            "classroom_id": item["classroom_id"],
            "weekday": item["weekday"],
            "start_time": item["start_time"],
            "end_time": item["end_time"],
            "effective_from": START_DATE,
            "effective_until": None,
        }
        existing_schedules = (
            db.query(CourseSchedule)
            .filter(CourseSchedule.course_id == course_id)
            .all()
        )
        if existing_schedules:
            if len(existing_schedules) != 1:
                raise RuntimeError(
                    f"دوره {course_id} بیش از یک برنامه هفتگی دارد؛ عملیات متوقف شد."
                )
            assert_same(
                existing_schedules[0], expected_schedule,
                (
                    "teacher_id", "classroom_id", "weekday",
                    "start_time", "end_time", "effective_from", "effective_until",
                ),
                "برنامه هفتگی",
            )
            counts["schedules_existing"] += 1
        else:
            db.add(CourseSchedule(**expected_schedule))
            db.flush()
            counts["schedules_created"] += 1

    return counts


def main():
    validate_source_data()
    db = SessionLocal()
    try:
        counts = import_records(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print("\nورود اطلاعات با موفقیت انجام شد.\n")
    labels = {
        "teachers_created": "دبیر جدید",
        "teachers_existing": "دبیر از قبل موجود",
        "classrooms_created": "کلاس جدید",
        "classrooms_existing": "کلاس از قبل موجود",
        "lessons_created": "درس جدید",
        "lessons_existing": "درس از قبل موجود",
        "courses_created": "دوره جدید",
        "courses_existing": "دوره از قبل موجود",
        "schedules_created": "برنامه هفتگی جدید",
        "schedules_existing": "برنامه هفتگی از قبل موجود",
    }
    for key, label in labels.items():
        print(f"{label}: {counts[key]}")
    print("\nتاریخ شروع: ۱ آبان ۱۴۰۵")
    print("قیمت هر جلسه: ۱۰۰٬۰۰۰ تومان")
    print("وضعیت اولیه دوره‌ها: active (در حال برگزاری)")
    print("تعداد دانش‌آموزان وارد نشده است.")
    print("جلسات CourseOccurrence تولید نشده‌اند؛ فقط دوره و برنامه هفتگی ثبت شده‌اند.")


if __name__ == "__main__":
    main()
