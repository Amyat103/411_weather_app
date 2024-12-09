import pytest

from weather_app.models.mongo_session_model import login_user, logout_user

class MockFavorite:
    def __init__(self, location_id):
        self.location_id = location_id

    def to_dict(self):
        return {"location_id": self.location_id}

@pytest.fixture
def sample_user_id():
    return 1  # Primary key for user

@pytest.fixture
def sample_favorites():
    return [
        {"location_id": 1},
        {"location_id": 2}
    ]  # Sample location data


def test_login_user_creates_session_if_not_exists(mocker, sample_user_id):
    """Test login_user creates a session with no locations if it does not exist."""
    mock_find = mocker.patch(
        "weather_app.clients.mongo_client.sessions_collection.find_one", 
        return_value=None
    )
    mock_insert = mocker.patch(
        "weather_app.clients.mongo_client.sessions_collection.insert_one"
    )
    mock_favorite_model = mocker.Mock()

    login_user(sample_user_id, mock_favorite_model)

    mock_find.assert_called_once_with({"user_id": sample_user_id})
    mock_insert.assert_called_once_with({"user_id": sample_user_id, "favorites": []})
    mock_favorite_model.clear_favorites.assert_not_called()
    mock_favorite_model.add_location_to_favorites.assert_not_called()


def test_login_user_loads_favorites_if_session_exists(mocker, sample_user_id, sample_favorites):
    """Test login_user loads favorites if session exists."""
    mock_find = mocker.patch(
        "weather_app.clients.mongo_client.sessions_collection.find_one",
        return_value={"user_id": sample_user_id, "favorites": sample_favorites}
    )
    mock_favorite_model = mocker.Mock()

    login_user(sample_user_id, mock_favorite_model)

    mock_find.assert_called_once_with({"user_id": sample_user_id})
    mock_favorite_model.clear_favorites.assert_called_once()
    mock_favorite_model.add_location_to_favorites.assert_has_calls(
        [mocker.call(location) for location in sample_favorites]
    )


def test_logout_user_updates_favorites(mocker, sample_user_id):
    """Test logout_user updates the favorites list in the session."""
    mock_update = mocker.patch(
        "weather_app.clients.mongo_client.sessions_collection.update_one",
        return_value=mocker.Mock(matched_count=1)
    )
    mock_favorite_model = mocker.Mock()

    # Use MockFavorite for get_all_favorites return value
    mock_favorite_model.get_all_favorites.return_value = [
        MockFavorite(location_id=1),
        MockFavorite(location_id=2)
    ]

    logout_user(sample_user_id, mock_favorite_model)

    mock_update.assert_called_once_with(
        {"user_id": sample_user_id},
        {"$set": {"favorites": [{"location_id": 1}, {"location_id": 2}]}},
        upsert=False
    )
    mock_favorite_model.clear_favorites.assert_called_once()


def test_logout_user_raises_value_error_if_no_user(mocker, sample_user_id):
    """Test logout_user raises ValueError if no session document exists."""
    mock_update = mocker.patch(
        "weather_app.clients.mongo_client.sessions_collection.update_one",
        return_value=mocker.Mock(matched_count=0)
    )
    mock_favorite_model = mocker.Mock()

    # Use MockFavorite objects for get_all_favorites return value
    mock_favorite_model.get_all_favorites.return_value = [
        MockFavorite(location_id=1),
        MockFavorite(location_id=2)
    ]

    with pytest.raises(ValueError, match=f"User with ID {sample_user_id} not found for logout."):
        logout_user(sample_user_id, mock_favorite_model)

    mock_update.assert_called_once_with(
        {"user_id": sample_user_id},
        {"$set": {"favorites": [{"location_id": 1}, {"location_id": 2}]}},
        upsert=False
    )
