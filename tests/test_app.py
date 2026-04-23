import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the activities database before each test"""
    # Store original data
    original_activities = {
        name: {
            "description": data["description"],
            "schedule": data["schedule"],
            "max_participants": data["max_participants"],
            "participants": data["participants"].copy()  # Copy the list
        }
        for name, data in activities.items()
    }

    yield

    # Reset to original state after test
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Test cases for GET /activities endpoint"""

    def test_get_activities_success(self, client):
        # Arrange
        expected_activities = list(activities.keys())

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9  # Based on the current activities
        for activity_name in expected_activities:
            assert activity_name in data
            assert "description" in data[activity_name]
            assert "schedule" in data[activity_name]
            assert "max_participants" in data[activity_name]
            assert "participants" in data[activity_name]


class TestSignupForActivity:
    """Test cases for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        initial_participants = activities[activity_name]["participants"].copy()

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity_name in data["message"]
        assert email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == len(initial_participants) + 1

    def test_signup_activity_not_found(self, client):
        # Arrange
        invalid_activity = "NonExistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{invalid_activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_signup_already_signed_up(self, client):
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already in participants

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Student already signed up" in data["detail"]
        # Verify participant wasn't added again
        assert activities[activity_name]["participants"].count(existing_email) == 1