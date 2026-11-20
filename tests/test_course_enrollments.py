from app.features.auth.service import create_access_token

ADMIN_HEADERS = {"Authorization": f"Bearer {create_access_token()}"}


def create_student(client, **overrides):
    payload = {
        "first_name": "علی",
        "last_name": "رضایی",
        "national_code": "1000000001",
        "grade": "دهم",
        "field": "ریاضی",
        "father_name": "محمد",
        "phone": "09120000000",
        "phone2": None,
    }
    payload.update(overrides)
    response = client.post("/api/students", headers=ADMIN_HEADERS, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def create_course(client):
    lesson_response = client.post(
        "/api/lessons",
        headers=ADMIN_HEADERS,
        json={"name": "ریاضی", "grade": "دهم", "field": "ریاضی"},
    )
    assert lesson_response.status_code == 201, lesson_response.text
    response = client.post(
        "/api/courses",
        headers=ADMIN_HEADERS,
        json={
            "title": "ریاضی دهم",
            "lesson_id": lesson_response.json()["id"],
            "price_per_session": 500000,
            "start_date": "2026-09-23",
            "status": "active",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def enrollment_payload(student_id, course_id, **overrides):
    payload = {
        "student_id": student_id,
        "course_id": course_id,
        "start_date": "2026-10-01",
        "end_date": None,
    }
    payload.update(overrides)
    return payload


def test_create_course_enrollment(client):
    student = create_student(client)
    course = create_course(client)

    response = client.post(
        "/api/course-enrollments",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(student["id"], course["id"]),
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["student_id"] == student["id"]
    assert data["student"]["first_name"] == "علی"
    assert data["course_id"] == course["id"]
    assert data["course"]["title"] == "ریاضی دهم"
    assert data["course"]["price_per_session"] == 500000
    assert data["start_date"] == "2026-10-01"
    assert data["end_date"] is None


def test_get_enrollments_can_filter_by_student_and_course(client):
    student = create_student(client)
    course = create_course(client)
    create_response = client.post(
        "/api/course-enrollments",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(student["id"], course["id"]),
    )
    assert create_response.status_code == 201

    by_student = client.get(
        f"/api/course-enrollments?student_id={student['id']}",
        headers=ADMIN_HEADERS,
    )
    by_course = client.get(
        f"/api/course-enrollments?course_id={course['id']}",
        headers=ADMIN_HEADERS,
    )

    assert by_student.status_code == 200
    assert by_course.status_code == 200
    assert len(by_student.json()) == 1
    assert len(by_course.json()) == 1


def test_student_can_enroll_in_multiple_courses(client):
    student = create_student(client)
    first_course = create_course(client)

    lesson_response = client.post(
        "/api/lessons",
        headers=ADMIN_HEADERS,
        json={"name": "فیزیک", "grade": "دهم", "field": "ریاضی"},
    )
    second_course_response = client.post(
        "/api/courses",
        headers=ADMIN_HEADERS,
        json={
            "title": "فیزیک دهم",
            "lesson_id": lesson_response.json()["id"],
            "price_per_session": 600000,
            "start_date": "2026-09-23",
            "status": "active",
        },
    )
    second_course = second_course_response.json()

    for course in (first_course, second_course):
        response = client.post(
            "/api/course-enrollments",
            headers=ADMIN_HEADERS,
            json=enrollment_payload(student["id"], course["id"]),
        )
        assert response.status_code == 201, response.text

    response = client.get(
        f"/api/course-enrollments?student_id={student['id']}",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_student_can_reenroll_after_previous_enrollment_ended(client):
    student = create_student(client)
    course = create_course(client)

    first = client.post(
        "/api/course-enrollments",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(
            student["id"], course["id"],
            start_date="2026-10-01", end_date="2026-11-15",
        ),
    )
    second = client.post(
        "/api/course-enrollments",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(
            student["id"], course["id"],
            start_date="2026-12-01", end_date=None,
        ),
    )

    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text


def test_overlapping_enrollment_for_same_course_is_rejected(client):
    student = create_student(client)
    course = create_course(client)
    first = client.post(
        "/api/course-enrollments",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(
            student["id"], course["id"],
            start_date="2026-10-01", end_date="2026-11-15",
        ),
    )
    assert first.status_code == 201

    overlapping = client.post(
        "/api/course-enrollments",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(
            student["id"], course["id"],
            start_date="2026-11-15", end_date=None,
        ),
    )
    assert overlapping.status_code == 409


def test_enrollment_start_cannot_be_before_course_start(client):
    student = create_student(client)
    course = create_course(client)

    response = client.post(
        "/api/course-enrollments",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(
            student["id"], course["id"], start_date="2026-09-01"
        ),
    )
    assert response.status_code == 422


def test_enrollment_rejects_unknown_student_or_course(client):
    student = create_student(client)
    course = create_course(client)

    unknown_student = client.post(
        "/api/course-enrollments",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(999, course["id"]),
    )
    unknown_course = client.post(
        "/api/course-enrollments",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(student["id"], 999),
    )

    assert unknown_student.status_code == 404
    assert unknown_course.status_code == 404


def test_enrollment_rejects_completed_course(client):
    student = create_student(client)
    course = create_course(client)

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

    response = client.post(
        "/api/course-enrollments",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(student["id"], course["id"]),
    )
    assert response.status_code == 409


def test_update_enrollment_dates(client):
    student = create_student(client)
    course = create_course(client)
    created = client.post(
        "/api/course-enrollments",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(student["id"], course["id"]),
    ).json()

    response = client.put(
        f"/api/course-enrollments/{created['id']}",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(
            student["id"], course["id"],
            start_date="2026-10-05", end_date="2026-11-20",
        ),
    )

    assert response.status_code == 200, response.text
    assert response.json()["start_date"] == "2026-10-05"
    assert response.json()["end_date"] == "2026-11-20"


def test_enrollment_end_date_must_not_be_before_start_date(client):
    student = create_student(client)
    course = create_course(client)

    response = client.post(
        "/api/course-enrollments",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(
            student["id"], course["id"],
            start_date="2026-10-10", end_date="2026-10-09",
        ),
    )
    assert response.status_code == 422


def test_enrollment_endpoints_require_admin_password(client):
    response = client.get("/api/course-enrollments")
    assert response.status_code == 401

def test_course_with_enrollment_cannot_be_deleted(client):
    student = create_student(client)
    course = create_course(client)
    created = client.post(
        "/api/course-enrollments",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(student["id"], course["id"]),
    )
    assert created.status_code == 201

    response = client.delete(
        f"/api/courses/{course['id']}",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 409


def test_student_with_enrollment_cannot_be_deleted(client):
    student = create_student(client)
    course = create_course(client)
    created = client.post(
        "/api/course-enrollments",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(student["id"], course["id"]),
    )
    assert created.status_code == 201

    response = client.delete(
        f"/api/students/{student['id']}",
        headers=ADMIN_HEADERS,
    )
    assert response.status_code == 409



def test_course_enrollment_can_be_deleted_without_session_history_or_allocations(client):
    student = create_student(client)
    course = create_course(client)
    created = client.post(
        "/api/course-enrollments",
        headers=ADMIN_HEADERS,
        json=enrollment_payload(student["id"], course["id"]),
    )
    assert created.status_code == 201, created.text
    enrollment_id = created.json()["id"]

    response = client.delete(
        f"/api/course-enrollments/{enrollment_id}",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 200, response.text
    assert response.json()["message"] == "عضویت با موفقیت حذف شد."

    missing = client.get(
        f"/api/course-enrollments/{enrollment_id}",
        headers=ADMIN_HEADERS,
    )
    assert missing.status_code == 404


def test_course_enrollment_delete_requires_admin(client):
    response = client.delete("/api/course-enrollments/1")
    assert response.status_code == 401
