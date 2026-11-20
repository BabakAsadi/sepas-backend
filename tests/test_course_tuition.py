from datetime import date, timedelta

from app.features.auth.service import create_access_token

ADMIN_HEADERS = {"Authorization": f"Bearer {create_access_token()}"}


def last_saturday():
    today = date.today()
    return today - timedelta(days=(today.weekday() - 5) % 7)


def setup_enrollment_and_occurrence(client, enrollment_start=None):
    lesson = client.post("/api/lessons", headers=ADMIN_HEADERS, json={
        "name": "ریاضی", "grade": "دهم", "field": "ریاضی"
    }).json()
    course = client.post("/api/courses", headers=ADMIN_HEADERS, json={
        "title": "ریاضی دهم",
        "lesson_id": lesson["id"],
        "price_per_session": 500000,
        "start_date": last_saturday().isoformat(),
        "status": "active",
    }).json()
    student = client.post("/api/students", headers=ADMIN_HEADERS, json={
        "first_name": "علی",
        "last_name": "رضایی",
        "national_code": "1000000001",
        "grade": "دهم",
        "field": "ریاضی",
        "father_name": "محمد",
        "phone": "09120000000",
        "phone2": None,
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
        "effective_from": last_saturday().isoformat(),
        "effective_until": None,
    })
    assert schedule.status_code == 201, schedule.text

    enrollment = client.post("/api/course-enrollments", headers=ADMIN_HEADERS, json={
        "student_id": student["id"],
        "course_id": course["id"],
        "start_date": (enrollment_start or last_saturday()).isoformat(),
        "end_date": None,
    })
    assert enrollment.status_code == 201, enrollment.text

    generated = client.post("/api/course-occurrences/generate", headers=ADMIN_HEADERS, json={
        "through_date": date.today().isoformat()
    })
    assert generated.status_code == 201, generated.text
    assert generated.json()["created_count"] == 1
    return course, student, enrollment.json(), generated.json()["items"][0]


def test_tuition_counts_held_occurrence(client):
    course, student, enrollment, occurrence = setup_enrollment_and_occurrence(client)

    response = client.get(
        f"/api/course-enrollments/{enrollment['id']}/tuition",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["student_id"] == student["id"]
    assert data["course_id"] == course["id"]
    assert data["billable_session_count"] == 1
    assert data["total_tuition"] == 500000
    assert data["sessions"][0]["occurrence_id"] == occurrence["id"]


def test_cancelled_occurrence_is_not_billable(client):
    _, _, enrollment, occurrence = setup_enrollment_and_occurrence(client)
    cancelled = client.patch(
        f"/api/course-occurrences/{occurrence['id']}/status",
        headers=ADMIN_HEADERS,
        json={"status": "cancelled"},
    )
    assert cancelled.status_code == 200

    response = client.get(
        f"/api/course-enrollments/{enrollment['id']}/tuition",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["billable_session_count"] == 0
    assert response.json()["total_tuition"] == 0


def test_moved_occurrence_uses_actual_session_date_for_enrollment(client):
    moved_date = last_saturday() + timedelta(days=2)
    _, _, enrollment, occurrence = setup_enrollment_and_occurrence(
        client, enrollment_start=moved_date
    )
    moved = client.patch(
        f"/api/course-occurrences/{occurrence['id']}/status",
        headers=ADMIN_HEADERS,
        json={"status": "moved", "session_date": moved_date.isoformat()},
    )
    assert moved.status_code == 200

    response = client.get(
        f"/api/course-enrollments/{enrollment['id']}/tuition",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["billable_session_count"] == 1
    assert data["sessions"][0]["scheduled_date"] == last_saturday().isoformat()
    assert data["sessions"][0]["session_date"] == moved_date.isoformat()


def test_future_moved_occurrence_is_not_charged_yet(client):
    _, _, enrollment, occurrence = setup_enrollment_and_occurrence(client)
    future_date = date.today() + timedelta(days=7)
    moved = client.patch(
        f"/api/course-occurrences/{occurrence['id']}/status",
        headers=ADMIN_HEADERS,
        json={"status": "moved", "session_date": future_date.isoformat()},
    )
    assert moved.status_code == 200

    response = client.get(
        f"/api/course-enrollments/{enrollment['id']}/tuition",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["billable_session_count"] == 0


def test_tuition_can_be_calculated_as_of_a_past_date(client):
    _, _, enrollment, _ = setup_enrollment_and_occurrence(client)
    response = client.get(
        f"/api/course-enrollments/{enrollment['id']}/tuition"
        f"?as_of_date={(last_saturday() - timedelta(days=1)).isoformat()}",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["billable_session_count"] == 0


def test_tuition_requires_admin_password(client):
    response = client.get("/api/course-enrollments/1/tuition")
    assert response.status_code == 401

def test_course_price_cannot_change_after_enrollment(client):
    course, _, _, _ = setup_enrollment_and_occurrence(client)
    response = client.put(f"/api/courses/{course['id']}", headers=ADMIN_HEADERS, json={
        "title": course["title"],
        "lesson_id": course["lesson_id"],
        "price_per_session": 600000,
        "start_date": course["start_date"],
        "status": course["status"],
    })
    assert response.status_code == 409
