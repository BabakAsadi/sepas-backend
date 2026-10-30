from app.core.config import ADMIN_PASSWORD

ADMIN_HEADERS = {"X-Admin-Password": ADMIN_PASSWORD}


def test_create_lesson(client):
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

    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "ریاضی"
    assert data["grade"] == "هفتم"


def test_get_lessons(client):
    client.post(
        "/api/lessons",
        headers=ADMIN_HEADERS,
        json={
            "name": "ریاضی",
            "grade": "هفتم",
            "field": "ریاضی"
        }
    )

    response = client.get("/api/lessons")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "ریاضی"

def test_update_lesson(client):
    create_response = client.post(
        "/api/lessons",
        headers=ADMIN_HEADERS,
        json={
            "name": "ریاضی",
            "grade": "هفتم",
            "field": "ریاضی"
        }
    )

    lesson_id = create_response.json()["id"]

    response = client.put(
        f"/api/lessons/{lesson_id}",
        headers=ADMIN_HEADERS,
        json={
            "name": "علوم",
            "grade": "هشتم",
            "field": "تجربی"
        }
    )

    assert response.status_code == 200
    assert response.json()["name"] == "علوم"
    assert response.json()["grade"] == "هشتم"

def test_delete_lesson(client):
    create_response = client.post(
        "/api/lessons",
        headers=ADMIN_HEADERS,
        json={
            "name": "ریاضی",
            "grade": "هفتم",
            "field": "ریاضی"
        }
    )

    lesson_id = create_response.json()["id"]

    response = client.delete(
        f"/api/lessons/{lesson_id}",
        headers=ADMIN_HEADERS
    )

    assert response.status_code == 200

    get_response = client.get(f"/api/lessons/{lesson_id}")
    assert get_response.status_code == 404

def test_create_lesson_without_admin_password(client):
    response = client.post(
        "/api/lessons",
        json={
            "name": "ریاضی",
            "grade": "هفتم",
            "field": "ریاضی"
        }
    )

    assert response.status_code == 422


def test_create_lesson_with_wrong_admin_password(client):
    response = client.post(
        "/api/lessons",
        headers={"X-Admin-Password": "wrong-password"},
        json={
            "name": "ریاضی",
            "grade": "هفتم",
            "field": "ریاضی"
        }
    )

    assert response.status_code == 401


def test_delete_lesson_with_sessions(client):
    teacher = client.post(
        "/api/teachers",
        headers=ADMIN_HEADERS,
        json={
            "first_name": "Ali",
            "last_name": "Ahmadi",
            "phone": "09123456789"
        }
    ).json()

    lesson = client.post(
        "/api/lessons",
        headers=ADMIN_HEADERS,
        json={
            "name": "ریاضی",
            "grade": "هفتم",
            "field": "ریاضی"
        }
    ).json()

    classroom = client.post(
        "/api/classrooms",
        headers=ADMIN_HEADERS,
        json={
            "name": "کلاس ۱",
            "address": "سهند",
            "capacity": 20
        }
    ).json()

    session = client.post(
        "/api/sessions",
        headers=ADMIN_HEADERS,
        json={
            "teacher_id": teacher["id"],
            "lesson_id": lesson["id"],
            "classroom_id": classroom["id"],
            "weekday": "شنبه",
            "start_time": "10:00",
            "end_time": "11:00",
            "registered_count": 0
        }
    )

    assert session.status_code == 200

    response = client.delete(
        f"/api/lessons/{lesson['id']}",
        headers=ADMIN_HEADERS
    )

    assert response.status_code == 409