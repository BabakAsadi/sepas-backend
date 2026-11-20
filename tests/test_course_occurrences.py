
from datetime import date, timedelta

from app.features.auth.service import create_access_token


ADMIN_HEADERS = {
    "Authorization": f"Bearer {create_access_token()}"
}


def last_saturday():
    today = date.today()
    return today - timedelta(days=(today.weekday() - 5) % 7)


def setup_active_schedule(client, weekday="شنبه", status="active"):
    lesson = client.post(
        "/api/lessons",
        headers=ADMIN_HEADERS,
        json={
            "name": "ریاضی",
            "grade": "دهم",
            "field": "ریاضی",
        },
    ).json()

    course = client.post(
        "/api/courses",
        headers=ADMIN_HEADERS,
        json={
            "title": "ریاضی دهم",
            "lesson_id": lesson["id"],
            "price_per_session": 500000,
            "start_date": last_saturday().isoformat(),
            "status": status,
        },
    ).json()

    teacher = client.post(
        "/api/teachers",
        headers=ADMIN_HEADERS,
        json={
            "first_name": "علی",
            "last_name": "احمدی",
            "phone": "09123456789",
        },
    ).json()

    classroom = client.post(
        "/api/classrooms",
        headers=ADMIN_HEADERS,
        json={
            "name": "کلاس ۱",
            "address": "تهران",
            "capacity": 20,
        },
    ).json()

    schedule = client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json={
            "course_id": course["id"],
            "teacher_id": teacher["id"],
            "classroom_id": classroom["id"],
            "weekday": weekday,
            "start_time": "16:00",
            "end_time": "17:30",
            "effective_from": last_saturday().isoformat(),
            "effective_until": None,
        },
    )

    assert schedule.status_code == 201
    return course, schedule.json()


def generate_all(client):
    return client.post(
        "/api/course-occurrences/generate",
        headers=ADMIN_HEADERS,
    )


def generate_course(client, course_id):
    return client.post(
        f"/api/course-occurrences/generate/{course_id}",
        headers=ADMIN_HEADERS,
    )


def test_generate_all_occurrences_creates_due_sessions(client):
    course, schedule = setup_active_schedule(client)

    response = generate_all(client)

    assert response.status_code == 201
    data = response.json()
    assert data["created_count"] == 1

    item = data["items"][0]
    assert item["course_id"] == course["id"]
    assert item["course_schedule_id"] == schedule["id"]
    assert item["scheduled_date"] == last_saturday().isoformat()
    assert item["session_date"] == last_saturday().isoformat()
    assert item["status"] == "held"
    assert item["start_time"] == "16:00"


def test_generate_single_course_occurrences(client):
    course, schedule = setup_active_schedule(client)

    response = generate_course(client, course["id"])

    assert response.status_code == 201
    data = response.json()
    assert data["created_count"] == 1
    assert data["items"][0]["course_id"] == course["id"]
    assert data["items"][0]["course_schedule_id"] == schedule["id"]


def test_generate_all_is_idempotent(client):
    setup_active_schedule(client)

    first = generate_all(client)
    second = generate_all(client)

    assert first.status_code == 201
    assert first.json()["created_count"] == 1

    assert second.status_code == 201
    assert second.json()["created_count"] == 0

    occurrences = client.get(
        "/api/course-occurrences",
        headers=ADMIN_HEADERS,
    ).json()

    assert len(occurrences) == 1


def test_generate_single_course_is_idempotent(client):
    course, _ = setup_active_schedule(client)

    first = generate_course(client, course["id"])
    second = generate_course(client, course["id"])

    assert first.status_code == 201
    assert first.json()["created_count"] == 1

    assert second.status_code == 201
    assert second.json()["created_count"] == 0


def test_generate_all_includes_pending_and_active_courses(client):
    active_course, _ = setup_active_schedule(client, status="active")
    pending_course, _ = setup_active_schedule(
        client,
        weekday="یکشنبه",
        status="pending",
    )

    response = generate_all(client)

    assert response.status_code == 201
    items = response.json()["items"]

    course_ids = {item["course_id"] for item in items}
    assert active_course["id"] in course_ids
    assert pending_course["id"] in course_ids


def test_completed_course_does_not_generate_occurrences(client):
    course, _ = setup_active_schedule(client)

    update = client.put(
        f"/api/courses/{course['id']}",
        headers=ADMIN_HEADERS,
        json={
            "title": course["title"],
            "lesson_id": course["lesson_id"],
            "price_per_session": course["price_per_session"],
            "start_date": course["start_date"],
            "status": "completed",
        },
    )
    assert update.status_code == 200

    response = generate_all(client)

    assert response.status_code == 201
    assert response.json()["created_count"] == 0


def test_generator_does_not_create_future_sessions(client):
    course, _ = setup_active_schedule(
        client,
        weekday="یکشنبه",
    )

    response = generate_course(client, course["id"])

    assert response.status_code == 201
    items = response.json()["items"]

    assert all(
        date.fromisoformat(item["scheduled_date"]) <= date.today()
        for item in items
    )


def test_generate_nonexistent_course_returns_404(client):
    response = generate_course(client, 999999)

    assert response.status_code == 404


def test_cancel_occurrence(client):
    setup_active_schedule(client)
    generated = generate_all(client).json()["items"][0]

    response = client.patch(
        f"/api/course-occurrences/{generated['id']}/status",
        headers=ADMIN_HEADERS,
        json={"status": "cancelled"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"
    assert response.json()["session_date"] == generated["scheduled_date"]


def test_move_occurrence_preserves_original_date(client):
    setup_active_schedule(client)
    generated = generate_all(client).json()["items"][0]
    moved_date = last_saturday() + timedelta(days=2)

    response = client.patch(
        f"/api/course-occurrences/{generated['id']}/status",
        headers=ADMIN_HEADERS,
        json={
            "status": "moved",
            "session_date": moved_date.isoformat(),
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "moved"
    assert response.json()["scheduled_date"] == generated["scheduled_date"]
    assert response.json()["session_date"] == moved_date.isoformat()


def test_moved_occurrence_requires_new_date(client):
    setup_active_schedule(client)
    generated = generate_all(client).json()["items"][0]

    response = client.patch(
        f"/api/course-occurrences/{generated['id']}/status",
        headers=ADMIN_HEADERS,
        json={"status": "moved"},
    )

    assert response.status_code == 422


def test_generation_preserves_admin_changes(client):
    setup_active_schedule(client)
    generated = generate_all(client).json()["items"][0]

    cancelled = client.patch(
        f"/api/course-occurrences/{generated['id']}/status",
        headers=ADMIN_HEADERS,
        json={"status": "cancelled"},
    )
    assert cancelled.status_code == 200

    second_generation = generate_all(client)

    assert second_generation.status_code == 201
    assert second_generation.json()["created_count"] == 0

    occurrence = client.get(
        f"/api/course-occurrences/{generated['id']}",
        headers=ADMIN_HEADERS,
    ).json()

    assert occurrence["status"] == "cancelled"


def test_occurrence_list_filters_by_course_and_date(client):
    course, _ = setup_active_schedule(client)
    generate_all(client)

    response = client.get(
        f"/api/course-occurrences?course_id={course['id']}"
        f"&from_date={last_saturday().isoformat()}"
        f"&to_date={last_saturday().isoformat()}",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_generate_occurrences_requires_authentication(client):
    response = client.post("/api/course-occurrences/generate")

    assert response.status_code == 401


def test_generate_single_course_requires_authentication(client):
    response = client.post("/api/course-occurrences/generate/1")

    assert response.status_code == 401


def test_occurrence_status_update_requires_authentication(client):
    response = client.patch(
        "/api/course-occurrences/1/status",
        json={"status": "cancelled"},
    )

    assert response.status_code == 401


def test_cancel_after_move_keeps_rescheduled_date(client):
    setup_active_schedule(client)
    generated = generate_all(client).json()["items"][0]
    moved_date = last_saturday() + timedelta(days=2)

    moved = client.patch(
        f"/api/course-occurrences/{generated['id']}/status",
        headers=ADMIN_HEADERS,
        json={
            "status": "moved",
            "session_date": moved_date.isoformat(),
        },
    )

    assert moved.status_code == 200

    cancelled = client.patch(
        f"/api/course-occurrences/{generated['id']}/status",
        headers=ADMIN_HEADERS,
        json={"status": "cancelled"},
    )

    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert cancelled.json()["session_date"] == moved_date.isoformat()
