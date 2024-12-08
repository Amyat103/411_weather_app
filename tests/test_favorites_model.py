import time


import pytest


from weather_app.models.favorites_model import FavoritesModel
from weather_app.models.location_model import Locations




@pytest.fixture
def favorites_model():
   """Fixture to provide a new instance of FavoritesModel for each test."""
   return FavoritesModel()


@pytest.fixture
def sample_location1():
   return Locations(
       id=1,
       location="Boston",
       latitude=42.3601,
       longitude=71.0589,
       current_temperature=34,
       current_wind_speed=15,
       current_uvi=0
   )


@pytest.fixture
def sample_location2():
   return Locations(
       id=2,
       location="New York",
       latitude=40.7128,
       longitude=-74.0060,
       current_temperature=28,
       current_wind_speed=10,
       current_uvi=0
   )


@pytest.fixture
def sample_favorites(sample_location1, sample_location2):
   return [sample_location1, sample_location2]




##################################################
# Add Song Management Test Cases
##################################################


def test_add_location_to_favorites(favorites_model, sample_location1):
   """Test adding a location to the favorites."""
   favorites_model.add_location_to_favorites(sample_location1)


   assert len(favorites_model.favorites) == 1
   assert favorites_model.favorites[0].id == sample_location1.id
   assert favorites_model.favorites[0].location == sample_location1.location


def test_add_duplicate_location_to_favorites(favorites_model, sample_location1):
   """Test adding a duplicate location to the favorites raises ValueError."""
   favorites_model.add_location_to_favorites(sample_location1)


   with pytest.raises(ValueError, match=f"Location with ID {sample_location1.id} already exists in favorites"):
       favorites_model.add_location_to_favorites(sample_location1)


##################################################
# Remove Song Management Test Cases
##################################################


def test_remove_location_by_location_id(favorites_model, sample_location1, sample_location2):
   """Test removing a location by its ID."""
   # Add sample locations
   favorites_model.favorites = [sample_location1, sample_location2]


   # Remove one location
   favorites_model.remove_location_by_location_id(sample_location1.id)


   # Check that the correct location is removed
   assert len(favorites_model.favorites) == 1
   assert favorites_model.favorites[0].id == sample_location2.id


def test_remove_location_by_index(favorites_model, sample_location1, sample_location2):
   favorites_model.favorites = [sample_location1, sample_location2]
   favorites_model.remove_location_by_index(1)  # Remove first location
   assert len(favorites_model.favorites) == 1
   assert favorites_model.favorites[0].id == sample_location2.id


def test_clear_favorites(favorites_model, sample_location1):
   """Test clearing all favorite locations."""
   # Use the correct method name to add a location to favorites
   favorites_model.add_location_to_favorites(sample_location1)


   # Clear the favorites list
   favorites_model.clear_favorites()


   # Assert that the favorites list is empty
   assert len(favorites_model.favorites) == 0




##################################################
# Retrieval Test Cases
##################################################


def test_get_all_favorites(favorites_model, sample_location1, sample_location2):
   favorites_model.favorites = [sample_location1, sample_location2]
   favorites = favorites_model.get_all_favorites()
   assert len(favorites) == 2
   assert favorites[0].id == sample_location1.id
   assert favorites[1].id == sample_location2.id


def test_get_location_by_location_id(favorites_model, sample_location1):
   favorites_model.favorites = [sample_location1]
   location = favorites_model.get_location_by_location_id(sample_location1.id)
   assert location.id == sample_location1.id
   assert location.location == sample_location1.location


def test_get_location_by_index(favorites_model, sample_location1, sample_location2):
   favorites_model.favorites = [sample_location1, sample_location2]
   location = favorites_model.get_location_by_index(2)
   assert location.id == sample_location2.id
   assert location.location == sample_location2.location


def test_get_current_favorite(favorites_model, sample_location1):
   favorites_model.favorites = [sample_location1]
   favorites_model.favorite_location = 1  # Current favorite is the first one
   current_favorite = favorites_model.get_current_favorite()
   assert current_favorite.id == sample_location1.id
   assert current_favorite.location == sample_location1.location


def test_get_favorites_length(favorites_model, sample_favorites):
   favorites_model.favorites = sample_favorites
   assert favorites_model.get_favorites_length() == 2


##################################################
# Validation and Utility Test Cases
##################################################


def test_validate_location_id_invalid(favorites_model):
   with pytest.raises(ValueError, match="Invalid location id: -1"):
       favorites_model.validate_location_id(-1)
   with pytest.raises(ValueError, match="Invalid location id: invalid"):
       favorites_model.validate_location_id("invalid")


def test_validate_index_invalid(favorites_model):
   favorites_model.favorites = []
   with pytest.raises(ValueError, match="Invalid index: 0"):
       favorites_model.validate_index(0)
   with pytest.raises(ValueError, match="Invalid index: 1"):
       favorites_model.validate_index(1)


def test_check_if_empty_empty(favorites_model):
   favorites_model.favorites = []
   with pytest.raises(ValueError, match="Favorites is empty"):
       favorites_model.check_if_empty()
