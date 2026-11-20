
from app.features.auth.service import create_access_token

ADMIN_HEADERS = {"Authorization": f"Bearer {create_access_token()}"}


def create_lesson(client):
    return client.post("/api/lessons", headers=ADMIN_HEADERS, json={
        "name": "ریاضی", "grade": "دهم", "field": "ریاضی"
    }).json()


def create_course(client):
    lesson = create_lesson(client)
    response = client.post("/api/courses", headers=ADMIN_HEADERS, json={
        "title": "ریاضی دهم", "lesson_id": lesson["id"],
        "price_per_session": 500000, "start_date": "2026-09-01"
    })
    assert response.status_code == 201
    return response.json()


def create_teacher(client, first_name="علی"):
    response = client.post("/api/teachers", headers=ADMIN_HEADERS, json={
        "first_name": first_name, "last_name": "احمدی", "phone": "09123456789"
    })
    assert response.status_code == 201
    return response.json()


def create_classroom(client, name="کلاس ۱"):
    response = client.post("/api/classrooms", headers=ADMIN_HEADERS, json={
        "name": name, "address": "تهران", "capacity": 20
    })
    assert response.status_code == 201
    return response.json()


def schedule_payload(course_id, teacher_id, classroom_id, **overrides):
    payload = {
        "course_id": course_id,
        "teacher_id": teacher_id,
        "classroom_id": classroom_id,
        "weekday": "شنبه",
        "start_time": "16:00",
        "end_time": "17:30",
        "effective_from": "2026-09-01",
        "effective_until": None,
    }
    payload.update(overrides)
    return payload


def setup_schedule_dependencies(client):
    course = create_course(client)
    teacher = create_teacher(client)
    classroom = create_classroom(client)
    return course, teacher, classroom


def test_create_course_schedule(client):
    course, teacher, classroom = setup_schedule_dependencies(client)
    response = client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(course["id"], teacher["id"], classroom["id"])
    )

    assert response.status_code == 201
    data = response.json()
    assert data["course_id"] == course["id"]
    assert data["course_title"] == "ریاضی دهم"
    assert data["teacher_name"] == "علی احمدی"
    assert data["classroom_name"] == "کلاس ۱"
    assert data["weekday"] == "شنبه"
    assert data["effective_from"] == "2026-09-01"
    assert data["effective_until"] is None


def test_list_course_schedules_and_filter_by_course(client):
    course, teacher, classroom = setup_schedule_dependencies(client)

    client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(course["id"], teacher["id"], classroom["id"])
    )

    assert len(client.get(
        "/api/course-schedules",
        headers=ADMIN_HEADERS
    ).json()) == 1

    assert len(client.get(
        f"/api/course-schedules?course_id={course['id']}",
        headers=ADMIN_HEADERS
    ).json()) == 1

    assert client.get(
        "/api/course-schedules?course_id=999",
        headers=ADMIN_HEADERS
    ).json() == []


def test_filter_course_schedules_by_teacher(client):
    course1, teacher1, classroom1 = setup_schedule_dependencies(client)

    course2 = create_course(client)
    classroom2 = create_classroom(client, "کلاس ۲")
    teacher2 = create_teacher(client, "رضا")

    client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(
            course1["id"], teacher1["id"], classroom1["id"]
        )
    )

    client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(
            course2["id"], teacher2["id"], classroom2["id"]
        )
    )

    response = client.get(
        f"/api/course-schedules?teacher_id={teacher1['id']}",
        headers=ADMIN_HEADERS
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["teacher_id"] == teacher1["id"]


def test_filter_course_schedules_by_classroom(client):
    course1, teacher1, classroom1 = setup_schedule_dependencies(client)

    course2 = create_course(client)
    teacher2 = create_teacher(client, "رضا")
    classroom2 = create_classroom(client, "کلاس ۲")

    client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(
            course1["id"], teacher1["id"], classroom1["id"]
        )
    )

    client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(
            course2["id"], teacher2["id"], classroom2["id"]
        )
    )

    response = client.get(
        f"/api/course-schedules?classroom_id={classroom1['id']}",
        headers=ADMIN_HEADERS
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["classroom_id"] == classroom1["id"]


def test_filter_course_schedules_by_teacher_and_classroom(client):
    course1, teacher1, classroom1 = setup_schedule_dependencies(client)

    course2 = create_course(client)
    teacher2 = create_teacher(client, "رضا")
    classroom2 = create_classroom(client, "کلاس ۲")

    client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(
            course1["id"], teacher1["id"], classroom1["id"]
        )
    )

    client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(
            course2["id"], teacher2["id"], classroom2["id"]
        )
    )

    response = client.get(
        f"/api/course-schedules?teacher_id={teacher1['id']}"
        f"&classroom_id={classroom1['id']}",
        headers=ADMIN_HEADERS
    )

    assert response.status_code == 200
    assert len(response.json()) == 1

    data = response.json()[0]
    assert data["teacher_id"] == teacher1["id"]
    assert data["classroom_id"] == classroom1["id"]


def test_filter_course_schedules_with_nonexistent_ids(client):
    response = client.get(
        "/api/course-schedules?teacher_id=999",
        headers=ADMIN_HEADERS
    )

    assert response.status_code == 200
    assert response.json() == []

    response = client.get(
        "/api/course-schedules?classroom_id=999",
        headers=ADMIN_HEADERS
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_course_schedule_not_found(client):
    assert client.get(
        "/api/course-schedules/999",
        headers=ADMIN_HEADERS
    ).status_code == 404


def test_create_schedule_rejects_missing_references(client):
    response = client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(999, 999, 999)
    )
    assert response.status_code == 404


def test_create_schedule_rejects_invalid_weekday(client):
    course, teacher, classroom = setup_schedule_dependencies(client)

    response = client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(
            course["id"], teacher["id"], classroom["id"],
            weekday="روز نامعتبر"
        )
    )

    assert response.status_code == 422


def test_create_schedule_rejects_invalid_time_range(client):
    course, teacher, classroom = setup_schedule_dependencies(client)

    response = client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(
            course["id"], teacher["id"], classroom["id"],
            start_time="17:30", end_time="16:00"
        )
    )

    assert response.status_code == 422


def test_create_schedule_rejects_effective_date_before_course_start(client):
    course, teacher, classroom = setup_schedule_dependencies(client)

    response = client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(
            course["id"], teacher["id"], classroom["id"],
            effective_from="2026-08-31"
        )
    )

    assert response.status_code == 422


def test_schedule_conflict_for_same_teacher(client):
    course, teacher, classroom = setup_schedule_dependencies(client)

    first = client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(course["id"], teacher["id"], classroom["id"])
    )
    assert first.status_code == 201

    another_course = create_course(client)
    another_classroom = create_classroom(client, "کلاس ۲")

    conflict = client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(
            another_course["id"], teacher["id"], another_classroom["id"]
        )
    )

    assert conflict.status_code == 409


def test_schedule_conflict_for_same_classroom(client):
    course, teacher, classroom = setup_schedule_dependencies(client)

    first = client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(course["id"], teacher["id"], classroom["id"])
    )
    assert first.status_code == 201

    another_course = create_course(client)
    another_teacher = create_teacher(client, "رضا")

    conflict = client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(
            another_course["id"], another_teacher["id"], classroom["id"]
        )
    )

    assert conflict.status_code == 409


def test_non_overlapping_effective_periods_do_not_conflict(client):
    course, teacher, classroom = setup_schedule_dependencies(client)

    first = client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(
            course["id"], teacher["id"], classroom["id"],
            effective_until="2026-12-31"
        )
    )
    assert first.status_code == 201

    another_course = create_course(client)

    second = client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(
            another_course["id"], teacher["id"], classroom["id"],
            effective_from="2027-01-01"
        )
    )

    assert second.status_code == 201


def test_update_course_schedule(client):
    course, teacher, classroom = setup_schedule_dependencies(client)

    created = client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(course["id"], teacher["id"], classroom["id"])
    ).json()

    response = client.put(
        f"/api/course-schedules/{created['id']}",
        headers=ADMIN_HEADERS,
        json=schedule_payload(
            course["id"], teacher["id"], classroom["id"],
            weekday="یکشنبه", start_time="18:00", end_time="19:00"
        )
    )

    assert response.status_code == 200
    assert response.json()["weekday"] == "یکشنبه"
    assert response.json()["start_time"] == "18:00"


def test_delete_course_schedule(client):
    course, teacher, classroom = setup_schedule_dependencies(client)

    created = client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(course["id"], teacher["id"], classroom["id"])
    ).json()

    response = client.delete(
        f"/api/course-schedules/{created['id']}",
        headers=ADMIN_HEADERS
    )

    assert response.status_code == 200
    assert client.get(
        f"/api/course-schedules/{created['id']}",
        headers=ADMIN_HEADERS
    ).status_code == 404


def test_schedule_write_requires_admin_password(client):
    course, teacher, classroom = setup_schedule_dependencies(client)

    response = client.post(
        "/api/course-schedules",
        json=schedule_payload(course["id"], teacher["id"], classroom["id"])
    )

    assert response.status_code == 401


def test_cannot_delete_schedule_after_occurrences_exist(client):
    from datetime import date, timedelta

    today = date.today()
    last_sat = today - timedelta(days=(today.weekday() - 5) % 7)

    lesson = create_lesson(client)

    course = client.post(
        "/api/courses",
        headers=ADMIN_HEADERS,
        json={
            "title": "دوره تست",
            "lesson_id": lesson["id"],
            "price_per_session": 500000,
            "start_date": last_sat.isoformat(),
            "status": "active",
        }
    ).json()

    teacher = create_teacher(client)
    classroom = create_classroom(client)

    schedule = client.post(
        "/api/course-schedules",
        headers=ADMIN_HEADERS,
        json=schedule_payload(
            course["id"], teacher["id"], classroom["id"],
            effective_from=last_sat.isoformat()
        )
    ).json()

    generated = client.post(
        "/api/course-occurrences/generate",
        headers=ADMIN_HEADERS,
        json={"through_date": last_sat.isoformat()}
    )

    assert generated.status_code == 201

    response = client.delete(
        f"/api/course-schedules/{schedule['id']}",
        headers=ADMIN_HEADERS
    )

    assert response.status_code == 409
