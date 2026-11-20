from app.features.auth.service import create_access_token

ADMIN_HEADERS = {"Authorization": f"Bearer {create_access_token()}"}


def create_student(client, national_code="1000000001"):
    response = client.post("/api/students", headers=ADMIN_HEADERS, json={
        "first_name": "علی",
        "last_name": "رضایی",
        "national_code": national_code,
        "grade": "دهم",
        "field": "ریاضی",
        "father_name": "محمد",
        "phone": "09120000000",
        "phone2": None,
    })
    assert response.status_code == 201, response.text
    return response.json()


def create_course_and_enrollment(client, student_id):
    lesson = client.post("/api/lessons", headers=ADMIN_HEADERS, json={
        "name": "ریاضی", "grade": "دهم", "field": "ریاضی"
    })
    assert lesson.status_code == 201, lesson.text
    course = client.post("/api/courses", headers=ADMIN_HEADERS, json={
        "title": "ریاضی دهم",
        "lesson_id": lesson.json()["id"],
        "price_per_session": 500000,
        "start_date": "2026-09-23",
        "status": "active",
    })
    assert course.status_code == 201, course.text
    enrollment = client.post("/api/course-enrollments", headers=ADMIN_HEADERS, json={
        "student_id": student_id,
        "course_id": course.json()["id"],
        "start_date": "2026-10-01",
        "end_date": None,
    })
    assert enrollment.status_code == 201, enrollment.text
    return course.json(), enrollment.json()


def test_wallet_is_empty_before_first_top_up(client):
    student = create_student(client)
    response = client.get(f"/api/wallets/{student['id']}", headers=ADMIN_HEADERS)

    assert response.status_code == 200, response.text
    assert response.json()["balance"] == 0
    assert response.json()["transactions"] == []
    assert response.json()["currency"] == "toman"


def test_top_up_increases_wallet_balance_and_creates_transaction(client):
    student = create_student(client)
    response = client.post(
        f"/api/wallets/{student['id']}/top-ups",
        headers=ADMIN_HEADERS,
        json={"amount": 2000000, "description": "شارژ اولیه"},
    )

    assert response.status_code == 201, response.text
    assert response.json()["type"] == "top_up"
    assert response.json()["amount"] == 2000000
    assert response.json()["wallet_balance"] == 2000000

    wallet = client.get(f"/api/wallets/{student['id']}", headers=ADMIN_HEADERS)
    assert wallet.json()["balance"] == 2000000
    assert len(wallet.json()["transactions"]) == 1
    assert wallet.json()["transactions"][0]["description"] == "شارژ اولیه"


def test_top_up_does_not_create_course_allocation(client):
    student = create_student(client)
    _, enrollment = create_course_and_enrollment(client, student["id"])

    top_up = client.post(
        f"/api/wallets/{student['id']}/top-ups",
        headers=ADMIN_HEADERS,
        json={"amount": 1000000},
    )
    assert top_up.status_code == 201

    wallet = client.get(f"/api/wallets/{student['id']}", headers=ADMIN_HEADERS)
    transactions = wallet.json()["transactions"]
    assert wallet.json()["balance"] == 1000000
    assert len(transactions) == 1
    assert transactions[0]["type"] == "top_up"
    assert transactions[0]["enrollment_id"] is None
    assert enrollment["id"] > 0


def test_allocation_reduces_wallet_balance_and_is_linked_to_enrollment(client):
    student = create_student(client)
    course, enrollment = create_course_and_enrollment(client, student["id"])
    client.post(
        f"/api/wallets/{student['id']}/top-ups",
        headers=ADMIN_HEADERS,
        json={"amount": 1500000},
    )

    allocation = client.post(
        f"/api/wallets/{student['id']}/allocations",
        headers=ADMIN_HEADERS,
        json={"enrollment_id": enrollment["id"], "amount": 700000},
    )

    assert allocation.status_code == 201, allocation.text
    data = allocation.json()
    assert data["type"] == "course_allocation"
    assert data["amount"] == 700000
    assert data["enrollment_id"] == enrollment["id"]
    assert data["course_id"] == course["id"]
    assert data["course_title"] == course["title"]
    assert data["wallet_balance"] == 800000

    wallet = client.get(f"/api/wallets/{student['id']}", headers=ADMIN_HEADERS)
    assert wallet.json()["balance"] == 800000
    assert [item["type"] for item in wallet.json()["transactions"]] == [
        "course_allocation", "top_up"
    ]


def test_allocation_cannot_make_wallet_negative(client):
    student = create_student(client)
    _, enrollment = create_course_and_enrollment(client, student["id"])
    client.post(
        f"/api/wallets/{student['id']}/top-ups",
        headers=ADMIN_HEADERS,
        json={"amount": 300000},
    )

    response = client.post(
        f"/api/wallets/{student['id']}/allocations",
        headers=ADMIN_HEADERS,
        json={"enrollment_id": enrollment["id"], "amount": 400000},
    )

    assert response.status_code == 409
    wallet = client.get(f"/api/wallets/{student['id']}", headers=ADMIN_HEADERS)
    assert wallet.json()["balance"] == 300000
    assert len(wallet.json()["transactions"]) == 1


def test_allocation_requires_enrollment_belonging_to_same_student(client):
    first_student = create_student(client, "1000000001")
    second_student = create_student(client, "1000000011")
    _, enrollment = create_course_and_enrollment(client, second_student["id"])
    client.post(
        f"/api/wallets/{first_student['id']}/top-ups",
        headers=ADMIN_HEADERS,
        json={"amount": 1000000},
    )

    response = client.post(
        f"/api/wallets/{first_student['id']}/allocations",
        headers=ADMIN_HEADERS,
        json={"enrollment_id": enrollment["id"], "amount": 100000},
    )
    assert response.status_code == 404


def test_wallet_endpoints_require_admin_password(client):
    response = client.get("/api/wallets/1")
    assert response.status_code == 401

def test_student_with_wallet_history_cannot_be_deleted(client):
    student = create_student(client)
    top_up = client.post(
        f"/api/wallets/{student['id']}/top-ups",
        headers=ADMIN_HEADERS,
        json={"amount": 100000},
    )
    assert top_up.status_code == 201

    response = client.delete(f"/api/students/{student['id']}", headers=ADMIN_HEADERS)
    assert response.status_code == 409


def test_top_up_amount_must_be_positive(client):
    student = create_student(client)
    response = client.post(
        f"/api/wallets/{student['id']}/top-ups",
        headers=ADMIN_HEADERS,
        json={"amount": 0},
    )
    assert response.status_code == 422


def test_wallet_top_up_does_not_reduce_course_debt_until_allocated(client):
    from datetime import date, timedelta

    student = create_student(client)
    course, enrollment = create_course_and_enrollment(client, student["id"])

    # Build one billable occurrence in the past/current period.
    # Create a recurring schedule and generate its due occurrence for this course.
    today = date.today()
    weekday_names = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
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
        "weekday": weekday_names[today.weekday()],
        "start_time": "16:00",
        "end_time": "17:30",
        "effective_from": (today - timedelta(days=7)).isoformat(),
        "effective_until": None,
    })
    assert schedule.status_code == 201, schedule.text
    generated = client.post("/api/course-occurrences/generate", headers=ADMIN_HEADERS, json={
        "through_date": today.isoformat()
    })
    assert generated.status_code == 201, generated.text

    tuition_url = f"/api/course-enrollments/{enrollment['id']}/tuition"
    before = client.get(tuition_url, headers=ADMIN_HEADERS)
    assert before.status_code == 200, before.text
    assert before.json()["total_tuition"] >= 0

    top_up = client.post(
        f"/api/wallets/{student['id']}/top-ups",
        headers=ADMIN_HEADERS,
        json={"amount": 1000000},
    )
    assert top_up.status_code == 201
    after_top_up = client.get(tuition_url, headers=ADMIN_HEADERS).json()
    assert after_top_up["allocated_amount"] == 0
    assert after_top_up["remaining_debt"] == after_top_up["total_tuition"]

    allocation = client.post(
        f"/api/wallets/{student['id']}/allocations",
        headers=ADMIN_HEADERS,
        json={"enrollment_id": enrollment["id"], "amount": 500000},
    )
    assert allocation.status_code == 201, allocation.text
    after_allocation = client.get(tuition_url, headers=ADMIN_HEADERS).json()
    assert after_allocation["allocated_amount"] == 500000
    assert after_allocation["remaining_debt"] == max(
        after_allocation["total_tuition"] - 500000, 0
    )
