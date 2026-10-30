
from app.core.config import ADMIN_PASSWORD

ADMIN_HEADERS = {"X-Admin-Password": ADMIN_PASSWORD}


def create_teacher(client):
    response = client.post(
        "/api/teachers",
        headers=ADMIN_HEADERS,
        json={
            "first_name": "Ali",
            "last_name": "Ahmadi",
            "phone": "09123456789"
        }
    )
    assert response.status_code == 201
    return response.json()


def create_lesson(client):
    response = client.post(
        "/api/lessons",
        headers=ADMIN_HEADERS,
        json={
            "name": "ریاضی",
            "grade": "هفتم",
            "field": "ریاضی"
        }
    )
    assert response.status_code == 201
    return response.json()


def create_classroom(client, name="کلاس ۱"):
    response = client.post(
        "/api/classrooms",
        headers=ADMIN_HEADERS,
        json={
            "name": name,
            "address": "سهند",
            "capacity": 20
        }
    )
    assert response.status_code == 201
    return response.json()


def create_session_payload(
    teacher_id,
    lesson_id,
    classroom_id,
    start_time="10:00",
    end_time="11:00",
    weekday="شنبه"
):
    return {
        "teacher_id": teacher_id,
        "lesson_id": lesson_id,
        "classroom_id": classroom_id,
        "weekday": weekday,
        "start_time": start_time,
        "end_time": end_time,
        "registered_count": 0
    }


def create_session(
    client,
    teacher_id,
    lesson_id,
    classroom_id,
    start_time="10:00",
    end_time="11:00",
    weekday="شنبه"
):
    response = client.post(
        "/api/sessions",
        headers=ADMIN_HEADERS,
        json=create_session_payload(
            teacher_id,
            lesson_id,
            classroom_id,
            start_time,
            end_time,
            weekday
        )
    )
    assert response.status_code == 200
    return response.json()


# CRUD


def test_create_session(client):
    teacher = create_teacher(client)
    lesson = create_lesson(client)
    classroom = create_classroom(client)

    response = client.post(
        "/api/sessions",
        headers=ADMIN_HEADERS,
        json=create_session_payload(
            teacher["id"],
            lesson["id"],
            classroom["id"]
        )
    )

    assert response.status_code == 200

    data = response.json()
    assert data["id"] is not None
    assert data["weekday"] == "شنبه"
    assert data["start_time"] == "10:00"
    assert data["end_time"] == "11:00"


def test_get_sessions(client):
    teacher = create_teacher(client)
    lesson = create_lesson(client)
    classroom = create_classroom(client)

    create_session(
        client,
        teacher["id"],
        lesson["id"],
        classroom["id"]
    )

    response = client.get("/api/sessions")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_update_session(client):
    teacher = create_teacher(client)
    lesson = create_lesson(client)
    classroom = create_classroom(client)

    session = create_session(
        client,
        teacher["id"],
        lesson["id"],
        classroom["id"]
    )

    response = client.put(
        f"/api/sessions/{session['id']}",
        headers=ADMIN_HEADERS,
        json=create_session_payload(
            teacher["id"],
            lesson["id"],
            classroom["id"],
            start_time="12:00",
            end_time="13:00",
            weekday="یکشنبه"
        )
    )

    assert response.status_code == 200
    assert response.json()["start_time"] == "12:00"
    assert response.json()["weekday"] == "یکشنبه"


def test_delete_session(client):
    teacher = create_teacher(client)
    lesson = create_lesson(client)
    classroom = create_classroom(client)

    session = create_session(
        client,
        teacher["id"],
        lesson["id"],
        classroom["id"]
    )

    response = client.delete(
        f"/api/sessions/{session['id']}",
        headers=ADMIN_HEADERS
    )

    assert response.status_code == 200

    get_response = client.get(
        f"/api/sessions/{session['id']}"
    )

    assert get_response.status_code == 404


# Authentication


def test_create_session_without_admin_password(client):
    teacher = create_teacher(client)
    lesson = create_lesson(client)
    classroom = create_classroom(client)

    response = client.post(
        "/api/sessions",
        json=create_session_payload(
            teacher["id"],
            lesson["id"],
            classroom["id"]
        )
    )

    assert response.status_code == 422


def test_create_session_with_wrong_admin_password(client):
    teacher = create_teacher(client)
    lesson = create_lesson(client)
    classroom = create_classroom(client)

    response = client.post(
        "/api/sessions",
        headers={"X-Admin-Password": "wrong-password"},
        json=create_session_payload(
            teacher["id"],
            lesson["id"],
            classroom["id"]
        )
    )

    assert response.status_code == 401


# Validation


def test_create_session_with_invalid_weekday(client):
    teacher = create_teacher(client)
    lesson = create_lesson(client)
    classroom = create_classroom(client)

    response = client.post(
        "/api/sessions",
        headers=ADMIN_HEADERS,
        json=create_session_payload(
            teacher["id"],
            lesson["id"],
            classroom["id"],
            weekday="جمعه‌کاری"
        )
    )

    assert response.status_code == 422


def test_create_session_with_invalid_time_format(client):
    teacher = create_teacher(client)
    lesson = create_lesson(client)
    classroom = create_classroom(client)

    response = client.post(
        "/api/sessions",
        headers=ADMIN_HEADERS,
        json=create_session_payload(
            teacher["id"],
            lesson["id"],
            classroom["id"],
            start_time="10:30 AM",
            end_time="11:30"
        )
    )

    assert response.status_code == 422


def test_create_session_with_start_time_after_end_time(client):
    teacher = create_teacher(client)
    lesson = create_lesson(client)
    classroom = create_classroom(client)

    response = client.post(
        "/api/sessions",
        headers=ADMIN_HEADERS,
        json=create_session_payload(
            teacher["id"],
            lesson["id"],
            classroom["id"],
            start_time="12:00",
            end_time="11:00"
        )
    )

    assert response.status_code == 422


def test_create_session_with_nonexistent_teacher(client):
    lesson = create_lesson(client)
    classroom = create_classroom(client)

    response = client.post(
        "/api/sessions",
        headers=ADMIN_HEADERS,
        json=create_session_payload(
            9999,
            lesson["id"],
            classroom["id"]
        )
    )

    assert response.status_code == 404


# Time conflicts


def test_prevent_teacher_time_conflict(client):
    teacher = create_teacher(client)
    lesson = create_lesson(client)
    classroom1 = create_classroom(client, "کلاس ۱")
    classroom2 = create_classroom(client, "کلاس ۲")

    create_session(
        client,
        teacher["id"],
        lesson["id"],
        classroom1["id"],
        "10:00",
        "11:00"
    )

    response = client.post(
        "/api/sessions",
        headers=ADMIN_HEADERS,
        json=create_session_payload(
            teacher["id"],
            lesson["id"],
            classroom2["id"],
            "10:30",
            "11:30"
        )
    )

    assert response.status_code == 409


def test_prevent_classroom_time_conflict(client):
    teacher1 = create_teacher(client)
    teacher2 = client.post(
        "/api/teachers",
        headers=ADMIN_HEADERS,
        json={
            "first_name": "Reza",
            "last_name": "Ahmadi",
            "phone": "09111111111"
        }
    ).json()

    lesson = create_lesson(client)
    classroom = create_classroom(client)

    create_session(
        client,
        teacher1["id"],
        lesson["id"],
        classroom["id"],
        "10:00",
        "11:00"
    )

    response = client.post(
        "/api/sessions",
        headers=ADMIN_HEADERS,
        json=create_session_payload(
            teacher2["id"],
            lesson["id"],
            classroom["id"],
            "10:30",
            "11:30"
        )
    )

    assert response.status_code == 409


def test_allow_adjacent_sessions(client):
    teacher = create_teacher(client)
    lesson = create_lesson(client)
    classroom = create_classroom(client)

    create_session(
        client,
        teacher["id"],
        lesson["id"],
        classroom["id"],
        "10:00",
        "11:00"
    )

    response = client.post(
        "/api/sessions",
        headers=ADMIN_HEADERS,
        json=create_session_payload(
            teacher["id"],
            lesson["id"],
            classroom["id"],
            "11:00",
            "12:00"
        )
    )

    assert response.status_code == 200
