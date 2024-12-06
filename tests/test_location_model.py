from dataclasses import asdict

import pytest

from weather_app.models.location_model import Locations

@pytest.fixture
def mock_redis_client(mocker):
    return mocker.patch('weather_app.models.location_model.redis_client')

######################################################
#
#    Add and delete
#
######################################################

def test_add_location(session):
    """Test adding a location to the database."""
    location = Locations.create_location("Boston", 42.3601, 71.0589, 34, 15, 0)

    # Query back the location to check it was added
    result = Locations.query.one()
    assert result.location == "Boston"
    assert result.latitude == 42.3601
    assert result.longitude == 71.0589
    assert result.current_temperature == 34
    assert result.current_wind_speed == 15
    assert result.current_rain == 0

def test_add_location_duplicate_name(session):
    """Test adding a location with a duplicate name."""
    Locations.create_location("Boston", 42.3601, 71.0589, 34, 15, 0)
    with pytest.raises(ValueError, match="Location with name 'Boston' already exists"):
        # Attempt to create a duplicate location
        Locations.create_location("Boston", 42.3601, 71.0589, 34, 15, 0)
        session.rollback()  # Rollback the transaction to clean up

def test_delete_location(session, mock_redis_client):
    """Test soft deleting a location by marking it as deleted."""
    Locations.create_location("Boston", 42.3601, 71.0589, 34, 15, 0)
    location = Locations.query.one()
    Locations.delete_location(location.id)

    # Fetch the location to confirm it's marked as deleted
    result = session.get(Locations, 1)
    assert result.deleted is True

def test_delete_location_triggers_cache_delete(session, mock_redis_client):
    """Test that deleting a location triggers cache removal in Redis."""
    # Create and add a location
    Locations.create_location("Boston", 42.3601, 71.0589, 34, 15, 0)
    location = session.get(Locations, 1)

    # Delete the meal
    Locations.delete_location(location.id)

    # Check that the Redis cache entry was deleted
    mock_redis_client.delete.assert_called_once_with(f"location:{location.id}")

def test_delete_location_bad_id(session):
    """Test deleting a location that does not exist."""
    with pytest.raises(ValueError, match="Location 999 not found"):
        Locations.delete_location(999)

def test_get_location_by_id_cache_hit(session, mock_redis_client):
    """Test retrieving a location by its ID from cache."""
    # Create and add a location to the database
    Locations.create_location("Boston", 42.3601, 71.0589, 34, 15, 0)
    location = Locations.query.one()

    # Set up mock Redis client to simulate cache hit with encoded data
    mock_redis_client.hgetall.return_value = {
        "id".encode(): "1".encode(),
        "location".encode(): "Boston".encode(),
        "latitude".encode(): "42.3601".encode(),
        "longitude".encode(): "71.0589".encode(),
        "current_temperature".encode(): "34".encode(),
        "current_wind_speed".encode(): "15".encode(),
        "current_rain".encode(): "0".encode(),
        "deleted".encode(): "False".encode(),
    }

    # Call the method
    result = Locations.get_location_by_id(location.id)

    # Assert Redis cache was accessed and the result is correct
    mock_redis_client.hgetall.assert_called_once_with(f"location_1")
    assert result["location"] == "Boston"


def test_get_location_by_id_cache_miss(session, mock_redis_client):
    """Test retrieving a location by its ID when it is not in cache."""
    # Create and add a location to the database
    Locations.create_location("Boston", 42.3601, 71.0589, 34, 15, 0)
    location = Locations.query.one()

    # Simulate cache miss by setting return_value to an empty dictionary
    mock_redis_client.hgetall.return_value = {}

    # Call the method
    result = Locations.get_location_by_id(location.id)

    # Assert Redis cache was accessed and data was subsequently cached with hset
    mock_redis_client.hgetall.assert_called_once_with(f"location_{location.id}")
    mock_redis_client.hset.assert_called_once_with(
        f"location_1",
        mapping={
            "id": "1",
            "location": "Boston",
            "latitude": "42.3601",
            "longitude": "71.0589",
            "current_temperature": "34",
            "current_wind_speed": "15",
            "current_rain": "0",
            "deleted": "False",
        }
    )
    assert result["location"] == "Boston"

def test_get_location_by_id_bad_id(session, mock_redis_client):
    """Test retrieving a location by an invalid ID."""

    # Ensure the Redis client returns an empty dict to simulate a cache miss
    mock_redis_client.hgetall.return_value = {}

    with pytest.raises(ValueError, match="Meal 999 not found"):
        Locations.get_location_by_id(999)

def test_get_location_by_id_deleted(session, mock_redis_client):
    """Test retrieving a location that has been marked as deleted."""

    # Set up the Redis client to return a deleted meal entry
    mock_redis_client.hgetall.return_value = {
        "id".encode(): "1".encode(),
        "location".encode(): "Boston".encode(),
        "latitude".encode(): "42.3601".encode(),
        "longitude".encode(): "71.0589".encode(),
        "current_temperature".encode(): "34".encode(),
        "current_wind_speed".encode(): "15".encode(),
        "current_rain".encode(): "0".encode(),
        "deleted".encode(): "True".encode(),  # Simulate the meal being marked as deleted
    }

    with pytest.raises(ValueError, match="Location 1 not found"):
        Locations.get_location_by_id(1)

def test_get_location_by_name_cache_hit(session, mock_redis_client):
    """Test retrieving a location by its name when the name-to-ID association is cached."""
    # Create the location and cache the name-to-ID association
    Locations.create_location("Boston", 42.3601, 71.0589, 34, 15, 0)
    location = Locations.query.one()
    mock_redis_client.get.return_value = str(location.id).encode()  # Simulate name-to-ID cache hit
    mock_redis_client.hgetall.return_value = {k.encode(): str(v).encode() for k, v in asdict(location).items()}

    # Retrieve location by name, expecting a cache hit for both ID and location data
    result = Locations.get_location_by_name("Boston")
    mock_redis_client.get.assert_called_once_with("location_name:Boston")
    mock_redis_client.hgetall.assert_called_once_with(f"location_{location.id}")
    assert result["location"] == "Boston"

def test_get_location_by_name_cache_miss(session, mock_redis_client):
    """Test retrieving a location by its name when the name-to-ID association is not cached."""
    # Create the location but simulate a cache miss for name-to-ID association
    Locations.create_location("Boston", 42.3601, 71.0589, 34, 15, 0)
    location = Locations.query.one()
    mock_redis_client.get.return_value = None  # Simulate cache miss for name-to-ID
    mock_redis_client.hgetall.return_value = {}  # Simulate cache miss for location data

    # Retrieve location by name; expect DB lookup and caching of both ID and location data
    result = Locations.get_location_by_name("Boston")
    mock_redis_client.get.assert_called_once_with("location_name:Boston")
    mock_redis_client.set.assert_called_once_with("location_name:Boston", str(location.id))
    mock_redis_client.hset.assert_called_once_with(f"location_{location.id}", mapping={k: str(v) for k, v in asdict(location).items()})
    assert result["location"] == "Boston"

def test_get_location_by_name_deleted(session, mock_redis_client):
    """Test retrieving a deleted location by its name."""
    # Create and delete the location
    Locations.create_location("Boston", 42.3601, 71.0589, 34, 15, 0)
    location = Locations.query.one()
    Locations.delete_location(location.id)

    # Cache reflects that the location is deleted
    mock_redis_client.get.return_value = str(location.id).encode()
    mock_redis_client.hgetall.return_value = {
        "id".encode(): "1".encode(),
        "location".encode(): "Boston".encode(),
        "latitude".encode(): "42.3601".encode(),
        "longitude".encode(): "71.0589".encode(),
        "current_temperature".encode(): "34".encode(),
        "current_wind_speed".encode(): "15".encode(),
        "current_rain".encode(): "0".encode(),
        "deleted".encode(): "True".encode()
    }

    # Attempt retrieval, expecting a ValueError
    with pytest.raises(ValueError, match="Location Boston not found"):
        Locations.get_location_by_name("Boston")

def test_get_location_by_name_bad_name(session, mock_redis_client):
    """Test retrieving a location by a name that does not exist in cache or database."""
    # Simulate a cache miss for a non-existent location name
    mock_redis_client.get.return_value = None

    # Attempt retrieval, expecting a ValueError
    with pytest.raises(ValueError, match="Location Ocean not found"):
        Locations.get_location_by_name("Ocean")
    mock_redis_client.get.assert_called_once_with("location_name:Ocean")

def test_update_location(session, mock_redis_client):
    """Test updating a location's details."""
    Locations.create_location("Boston", 42.3601, 71.0589, 34, 15, 0)
    location = Locations.query.one()
    Locations.update_location(location.id, current_temperature=28, current_wind_speed=14, current_rain=2)
    updated_location = Locations.query.one()
    assert updated_location.current_temperature == 28
    assert updated_location.current_wind_speed == 14
    assert updated_location.current_rain == 2

def test_update_location_triggers_cache_update(session, mock_redis_client):
    """Test that updating a location triggers a cache update in Redis."""
    # Create and add a location
    Locations.create_location("Boston", 42.3601, 71.0589, 34, 15, 0)
    location = session.get(Locations, 1)

    # Update the location
    Locations.update_location(location.id, current_temperature=20, current_wind_speed=10)

    # Check that the Redis cache was updated with the new values
    mock_redis_client.hset.assert_called_once_with(
        f"location:{location.id}",
        mapping={
            b"id": b"1",
            b"location": b"Boston",
            b"latitude": b"42.3601",
            b"longitude": b"71.0589",
            b"current_temperature": b"20",
            b"current_wind_speed": b"10",
            b"current_rain": b"0",
            b"deleted": b"False",
        }
    )

def test_update_location_deleted(session, mock_redis_client):
    """Test updating a deleted location."""
    Locations.create_location("Boston", 42.3601, 71.0589, 34, 15, 0)
    location = Locations.query.one()
    Locations.delete_location(location.id)
    with pytest.raises(ValueError, match="Location 1 not found"):
        Locations.update_location(location.id, current_temperature=28, current_wind_speed=14, current_rain=2)


def test_update_location_bad_id(session):
    """Test updating a location with an invalid ID."""
    with pytest.raises(ValueError, match="Location 999 not found"):
        Locations.update_location(999, current_temperature=28, current_wind_speed=14, current_rain=2)


