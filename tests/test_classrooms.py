
from app.core.config import ADMIN_PASSWORD

ADMIN_HEADERS = {"X-Admin-Password": ADMIN_PASSWORD}


def test_create_classroom(client):
    response = client.post(
        "/api/classrooms",
        headers=ADMIN_HEADERS,
        json={
            "name": "کلاس ۱",
            "address": "سهند",
            "capacity": 20,
            "latitude": 37.95,
            "longitude": 45.77
        }
    )

    assert response.status_code == 201

    data = response.json()
    assert data["id"] is not None
    assert data["name"] == "کلاس ۱"
    assert data["address"] == "سهند"
    assert data["capacity"] == 20


def test_get_classrooms(client):
    client.post(
        "/api/classrooms",
        headers=ADMIN_HEADERS,
        json={
            "name": "کلاس ۱",
            "address": "سهند",
            "capacity": 20
        }
    )

    response = client.get("/api/classrooms")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "کلاس ۱"


def test_update_classroom(client):
    create_response = client.post(
        "/api/classrooms",
        headers=ADMIN_HEADERS,
        json={
            "name": "کلاس ۱",
            "address": "سهند",
            "capacity": 20
        }
    )

    classroom_id = create_response.json()["id"]

    response = client.put(
        f"/api/classrooms/{classroom_id}",
        headers=ADMIN_HEADERS,
        json={
            "name": "کلاس ۲",
            "address": "اسکو",
            "capacity": 30
        }
    )

    assert response.status_code == 200
    assert response.json()["name"] == "کلاس ۲"
    assert response.json()["address"] == "اسکو"
    assert response.json()["capacity"] == 30


def test_delete_classroom(client):
    create_response = client.post(
        "/api/classrooms",
        headers=ADMIN_HEADERS,
        json={
            "name": "کلاس ۱",
            "address": "سهند",
            "capacity": 20
        }
    )

    classroom_id = create_response.json()["id"]

    response = client.delete(
        f"/api/classrooms/{classroom_id}",
        headers=ADMIN_HEADERS
    )

    assert response.status_code == 200

    get_response = client.get(
        f"/api/classrooms/{classroom_id}"
    )

    assert get_response.status_code == 404


def test_create_classroom_without_admin_password(client):
    response = client.post(
        "/api/classrooms",
        json={
            "name": "کلاس ۱",
            "address": "سهند",
            "capacity": 20
        }
    )

    assert response.status_code == 422


def test_create_classroom_with_wrong_admin_password(client):
    response = client.post(
        "/api/classrooms",
        headers={"X-Admin-Password": "wrong-password"},
        json={
            "name": "کلاس ۱",
            "address": "سهند",
            "capacity": 20
        }
    )

    assert response.status_code == 401


def test_delete_classroom_with_sessions(client):
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
        f"/api/classrooms/{classroom['id']}",
        headers=ADMIN_HEADERS
    )

    assert response.status_code == 409
