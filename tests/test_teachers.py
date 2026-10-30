from app.core.config import ADMIN_PASSWORD


ADMIN_HEADERS = {
    "X-Admin-Password": ADMIN_PASSWORD
}


def test_create_teacher(client):
    response = client.post(
        "/api/teachers",
        headers=ADMIN_HEADERS,
        json={
            "first_name": "Ali",
            "last_name": "Ahmadi",
            "phone": "09123456789",
            "photo": None
        }
    )

    assert response.status_code == 201
    data = response.json()

    assert data["id"] is not None
    assert data["first_name"] == "Ali"
    assert data["last_name"] == "Ahmadi"


def test_get_teachers(client):
    client.post(
        "/api/teachers",
        headers=ADMIN_HEADERS,
        json={
            "first_name": "Ali",
            "last_name": "Ahmadi",
            "phone": "09123456789"
        }
    )

    response = client.get("/api/teachers")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_update_teacher(client):
    create_response = client.post(
        "/api/teachers",
        headers=ADMIN_HEADERS,
        json={
            "first_name": "Ali",
            "last_name": "Ahmadi",
            "phone": "09123456789"
        }
    )

    teacher_id = create_response.json()["id"]

    response = client.put(
        f"/api/teachers/{teacher_id}",
        headers=ADMIN_HEADERS,
        json={
            "first_name": "Reza",
            "last_name": "Ahmadi",
            "phone": "09123456789"
        }
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Reza"


def test_delete_teacher(client):
    create_response = client.post(
        "/api/teachers",
        headers=ADMIN_HEADERS,
        json={
            "first_name": "Ali",
            "last_name": "Ahmadi",
            "phone": "09123456789"
        }
    )

    teacher_id = create_response.json()["id"]

    response = client.delete(
        f"/api/teachers/{teacher_id}",
        headers=ADMIN_HEADERS
    )

    assert response.status_code == 200

    get_response = client.get(f"/api/teachers/{teacher_id}")
    assert get_response.status_code == 404


def test_create_teacher_without_admin_password(client):
    response = client.post(
        "/api/teachers",
        json={
            "first_name": "Ali",
            "last_name": "Ahmadi",
            "phone": "09123456789"
        }
    )

    assert response.status_code == 422


def test_create_teacher_with_wrong_admin_password(client):
    response = client.post(
        "/api/teachers",
        headers={"X-Admin-Password": "wrong-password"},
        json={
            "first_name": "Ali",
            "last_name": "Ahmadi",
            "phone": "09123456789"
        }
    )

    assert response.status_code == 401


def test_delete_teacher_with_sessions(client):
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
        f"/api/teachers/{teacher['id']}",
        headers=ADMIN_HEADERS
    )

    assert response.status_code == 409