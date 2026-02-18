"""
Tests for the Mergington High School Activities API.
"""

import copy
import pytest
from fastapi.testclient import TestClient

import src.app as app_module
from src.app import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_activities():
    """Restore the activities dict to its original state after each test."""
    original = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


@pytest.fixture()
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------

class TestGetActivities:
    def test_returns_200(self, client):
        response = client.get("/activities")
        assert response.status_code == 200

    def test_returns_dict(self, client):
        data = client.get("/activities").json()
        assert isinstance(data, dict)

    def test_contains_expected_activities(self, client):
        data = client.get("/activities").json()
        expected = {"Chess Club", "Programming Class", "Gym Class", "Soccer Club",
                    "Basketball Club", "Art Club", "Music Club", "Debate Club", "Science Club"}
        assert expected.issubset(data.keys())

    def test_activity_has_required_fields(self, client):
        data = client.get("/activities").json()
        for activity in data.values():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestSignup:
    def test_signup_success(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in response.json()["message"]

    def test_signup_adds_participant(self, client):
        client.post("/activities/Chess Club/signup",
                    params={"email": "newstudent@mergington.edu"})
        data = client.get("/activities").json()
        assert "newstudent@mergington.edu" in data["Chess Club"]["participants"]

    def test_signup_unknown_activity_returns_404(self, client):
        response = client.post(
            "/activities/Unknown Activity/signup",
            params={"email": "ghost@mergington.edu"},
        )
        assert response.status_code == 404

    def test_signup_duplicate_returns_400(self, client):
        email = "michael@mergington.edu"  # already in Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email},
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_full_activity_returns_400(self, client):
        """Fill Art Club (max 10, starts with 2) then attempt one more signup."""
        for i in range(8):
            r = client.post(
                "/activities/Art Club/signup",
                params={"email": f"student{i}@mergington.edu"},
            )
            assert r.status_code == 200

        overflow = client.post(
            "/activities/Art Club/signup",
            params={"email": "overflow@mergington.edu"},
        )
        assert overflow.status_code == 400


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------

class TestUnregister:
    def test_unregister_success(self, client):
        email = "michael@mergington.edu"  # already in Chess Club
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": email},
        )
        assert response.status_code == 200
        assert email in response.json()["message"]

    def test_unregister_removes_participant(self, client):
        email = "michael@mergington.edu"
        client.delete("/activities/Chess Club/signup", params={"email": email})
        data = client.get("/activities").json()
        assert email not in data["Chess Club"]["participants"]

    def test_unregister_unknown_activity_returns_404(self, client):
        response = client.delete(
            "/activities/Unknown Activity/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 404

    def test_unregister_non_participant_returns_400(self, client):
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "notamember@mergington.edu"},
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# GET / (redirect)
# ---------------------------------------------------------------------------

class TestRoot:
    def test_root_redirects(self, client):
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (301, 302, 307, 308)
        assert "/static/index.html" in response.headers["location"]
