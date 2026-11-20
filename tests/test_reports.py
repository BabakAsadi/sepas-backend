from datetime import date, timedelta

from app.features.auth.service import create_access_token

ADMIN_HEADERS = {"Authorization": f"Bearer {create_access_token()}"}


def setup_report_data(client):
    lesson = client.post("/api/lessons", headers=ADMIN_HEADERS, json={
        "name": "ریاضی", "grade": "دهم", "field": "ریاضی"
    }).json()
    today = date.today()
    session_date = today - timedelta(days=(today.weekday() - 5) % 7)
    course = client.post("/api/courses", headers=ADMIN_HEADERS, json={
        "title": "ریاضی دهم",
        "lesson_id": lesson["id"],
        "price_per_session": 800000,
        "start_date": session_date.isoformat(),
        "status": "active",
    }).json()
    teacher = client.post("/api/teachers", headers=ADMIN_HEADERS, json={
        "first_name": "علی", "last_name": "احمدی", "phone": "09123456789"
    }).json()
    classroom = client.post("/api/classrooms", headers=ADMIN_HEADERS, json={
        "name": "کلاس ۱", "address": "تهران", "capacity": 20
    }).json()
    schedule = client.post("/api/course-schedules", headers=ADMIN_HEADERS, json={
        "course_id": course["id"],
        "teacher_id": teacher["id"],
        "classroom_id": classroom["id"],
        "weekday": "شنبه",
        "start_time": "16:00",
        "end_time": "17:30",
        "effective_from": session_date.isoformat(),
        "effective_until": None,
    })
    assert schedule.status_code == 201, schedule.text

    students = []
    enrollments = []
    for index, (name, national_code) in enumerate(zip(("اول", "دوم", "سوم"), ("1234000008", "2345000007", "3456000006")), start=1):
        student = client.post("/api/students", headers=ADMIN_HEADERS, json={
            "first_name": name,
            "last_name": "آزمایشی",
            "national_code": national_code,
            "grade": "دهم",
            "field": "ریاضی",
            "father_name": "پدر",
            "phone": f"0912000000{index}",
            "phone2": None,
        })
        assert student.status_code == 201, student.text
        student_data = student.json()
        students.append(student_data)

        enrollment = client.post("/api/course-enrollments", headers=ADMIN_HEADERS, json={
            "student_id": student_data["id"],
            "course_id": course["id"],
            "start_date": session_date.isoformat(),
            "end_date": None,
        })
        assert enrollment.status_code == 201, enrollment.text
        enrollments.append(enrollment.json())

    generated = client.post("/api/course-occurrences/generate", headers=ADMIN_HEADERS, json={
        "through_date": today.isoformat()
    })
    assert generated.status_code == 201, generated.text
    assert generated.json()["created_count"] == 1
    return students, enrollments, session_date


def test_student_debt_report_groups_and_sorts_students(client):
    students, enrollments, session_date = setup_report_data(client)

    # Top-ups alone must not reduce debt.
    for student in students:
        response = client.post(
            f"/api/wallets/{student['id']}/top-ups",
            headers=ADMIN_HEADERS,
            json={"amount": 800000, "description": "شارژ"},
        )
        assert response.status_code == 201, response.text

    # The second student allocates part of the wallet; the third pays in full.
    partial = client.post(
        f"/api/wallets/{students[1]['id']}/allocations",
        headers=ADMIN_HEADERS,
        json={"enrollment_id": enrollments[1]["id"], "amount": 500000},
    )
    assert partial.status_code == 201, partial.text
    full = client.post(
        f"/api/wallets/{students[2]['id']}/allocations",
        headers=ADMIN_HEADERS,
        json={"enrollment_id": enrollments[2]["id"], "amount": 800000},
    )
    assert full.status_code == 201, full.text

    response = client.get("/api/reports/student-debts", headers=ADMIN_HEADERS)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["currency"] == "toman"
    assert data["indebted_student_count"] == 2
    assert data["total_debt"] == 1100000
    assert [item["student_id"] for item in data["students"]] == [
        students[0]["id"], students[1]["id"]
    ]
    assert [item["total_debt"] for item in data["students"]] == [800000, 300000]
    assert data["students"][0]["courses"][0]["remaining_debt"] == 800000
    assert data["students"][1]["courses"][0]["allocated_amount"] == 500000
    assert data["as_of_date"] == date.today().isoformat()

    # A report for the previous day must not include today's allocations.
    previous_day = date.today() - timedelta(days=1)
    historical = client.get(
        f"/api/reports/student-debts?as_of_date={previous_day.isoformat()}",
        headers=ADMIN_HEADERS,
    )
    assert historical.status_code == 200, historical.text
    historical_data = historical.json()
    assert historical_data["total_debt"] == 2400000
    assert historical_data["indebted_student_count"] == 3


def test_student_debt_report_supports_historical_cutoff(client):
    _, _, session_date = setup_report_data(client)
    cutoff = session_date - timedelta(days=1)

    response = client.get(
        f"/api/reports/student-debts?as_of_date={cutoff.isoformat()}",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["indebted_student_count"] == 0
    assert data["total_debt"] == 0
    assert data["students"] == []


def test_student_debt_report_rejects_future_date(client):
    future = date.today() + timedelta(days=1)
    response = client.get(
        f"/api/reports/student-debts?as_of_date={future.isoformat()}",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 422


def test_student_debt_report_requires_admin_password(client):
    response = client.get("/api/reports/student-debts")
    assert response.status_code == 401
