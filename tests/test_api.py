import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


SEED_ACTIVITIES = copy.deepcopy(activities)


def signup_path(activity_name: str) -> str:
    return f"/activities/{quote(activity_name, safe='')}/signup"


@pytest.fixture(autouse=True)
def reset_activities() -> None:
    activities.clear()
    activities.update(copy.deepcopy(SEED_ACTIVITIES))
    yield
    activities.clear()
    activities.update(copy.deepcopy(SEED_ACTIVITIES))


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_root_redirects_to_static_index(client: TestClient) -> None:
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_seeded_data(client: TestClient) -> None:
    response = client.get("/activities")

    assert response.status_code == 200

    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
    assert payload["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_new_student_to_activity(client: TestClient) -> None:
    email = "new.student@mergington.edu"

    response = client.post(signup_path("Chess Club"), params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in activities["Chess Club"]["participants"]


def test_signup_rejects_unknown_activity(client: TestClient) -> None:
    response = client.post(signup_path("Robotics Club"), params={"email": "student@mergington.edu"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_student(client: TestClient) -> None:
    response = client.post(
        signup_path("Chess Club"),
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}


def test_unregister_removes_existing_student(client: TestClient) -> None:
    email = "emma@mergington.edu"

    response = client.delete(signup_path("Programming Class"), params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Programming Class"}
    assert email not in activities["Programming Class"]["participants"]


def test_unregister_rejects_unknown_activity(client: TestClient) -> None:
    response = client.delete(signup_path("Robotics Club"), params={"email": "student@mergington.edu"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_student_not_signed_up(client: TestClient) -> None:
    response = client.delete(
        signup_path("Programming Class"),
        params={"email": "not.enrolled@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}