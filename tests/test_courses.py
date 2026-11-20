from app.features.auth.service import create_access_token

ADMIN_HEADERS = {"Authorization": f"Bearer {create_access_token()}"}


def create_lesson(client):
    response = client.post(
        "/api/lessons",
        headers=ADMIN_HEADERS,
        json={"name": "ریاضی", "grade": "دهم", "field": "ریاضی"},
    )
    assert response.status_code == 201
    return response.json()


def course_payload(lesson_id, **overrides):
    payload = {
        "title": "ریاضی دهم - گروه اول",
        "lesson_id": lesson_id,
        "price_per_session": 500000,
        "start_date": "2026-09-23",
        "status": "pending",
    }
    payload.update(overrides)
    return payload


def test_create_course(client):
    lesson = create_lesson(client)

    response = client.post(
        "/api/courses",
        headers=ADMIN_HEADERS,
        json=course_payload(lesson["id"]),
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "ریاضی دهم - گروه اول"
    assert data["lesson_id"] == lesson["id"]
    assert data["lesson"]["name"] == "ریاضی"
    assert data["price_per_session"] == 500000
    assert data["currency"] == "toman"
    assert data["start_date"] == "2026-09-23"
    assert data["status"] == "pending"


def test_get_courses(client):
    lesson = create_lesson(client)
    client.post(
        "/api/courses",
        headers=ADMIN_HEADERS,
        json=course_payload(lesson["id"]),
    )

    response = client.get("/api/courses", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_course_not_found(client):
    response = client.get("/api/courses/999", headers=ADMIN_HEADERS)
    assert response.status_code == 404


def test_create_course_with_unknown_lesson(client):
    response = client.post(
        "/api/courses",
        headers=ADMIN_HEADERS,
        json=course_payload(999),
    )
    assert response.status_code == 404


def test_create_course_rejects_non_positive_price(client):
    lesson = create_lesson(client)
    response = client.post(
        "/api/courses",
        headers=ADMIN_HEADERS,
        json=course_payload(lesson["id"], price_per_session=0),
    )
    assert response.status_code == 422


def test_create_course_rejects_invalid_status(client):
    lesson = create_lesson(client)
    response = client.post(
        "/api/courses",
        headers=ADMIN_HEADERS,
        json=course_payload(lesson["id"], status="unknown"),
    )
    assert response.status_code == 422


def test_update_course(client):
    lesson = create_lesson(client)
    created = client.post(
        "/api/courses",
        headers=ADMIN_HEADERS,
        json=course_payload(lesson["id"]),
    ).json()

    response = client.put(
        f"/api/courses/{created['id']}",
        headers=ADMIN_HEADERS,
        json=course_payload(
            lesson["id"],
            title="ریاضی دهم - گروه دوم",
            price_per_session=600000,
            status="active",
        ),
    )

    assert response.status_code == 200
    assert response.json()["title"] == "ریاضی دهم - گروه دوم"
    assert response.json()["price_per_session"] == 600000
    assert response.json()["status"] == "active"


def test_delete_course(client):
    lesson = create_lesson(client)
    created = client.post(
        "/api/courses",
        headers=ADMIN_HEADERS,
        json=course_payload(lesson["id"]),
    ).json()

    response = client.delete(
        f"/api/courses/{created['id']}",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert client.get(f"/api/courses/{created['id']}", headers=ADMIN_HEADERS).status_code == 404


def test_create_course_requires_admin_password(client):
    lesson = create_lesson(client)
    response = client.post(
        "/api/courses",
        json=course_payload(lesson["id"]),
    )
    assert response.status_code == 401
