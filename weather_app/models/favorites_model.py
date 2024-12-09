import logging
import os
import time
from typing import Any, List

from weather_app.models.location_model import Locations
from weather_app.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


TTL = os.getenv("TTL", 60)  # Default TTL is 60 seconds


class FavoritesModel:
    """
    A class to manage a favorites list of locations.

    Attributes:
        favorite_location (int): The current favorite location.
        favorites (List[Locations]): The list of favorited locations.

    """

    def __init__(self):
        """
        Initializes the FavoritesModel with an empty favorites and the current favorite set to 1.
        """
        self.favorite_location = 1
        self.favorites: List[Locations] = []

    ##################################################
    # Location Management Functions
    ##################################################

    def add_location_to_favorites(self, location: Locations) -> None:
        """
        Adds a location to the favorites.

        Args:
            location (Locations): the location to add to the favorites.

        Raises:
            TypeError: If the location is not a valid Locations instance.
            ValueError: If a location with the same 'id' already exists.
        """
        logger.info("Adding new location to favorites")
        if not isinstance(location, Locations):
            logger.error("Location is not a valid location")
            raise TypeError("Location is not a valid location")

        location_id = self.validate_location_id(location.id, check_in_favorites=False)
        if location_id in [i.id for i in self.favorites]:
            logger.error("Location with ID %d already exists in favorites", location.id)
            raise ValueError(f"Location with ID {location.id} already exists in favorites")

        self.favorites.append(location)

    def remove_location_by_location_id(self, location_id: int) -> None:
        """
        Removes a location from the favorites by its location ID.

        Args:
            location_id (int): The ID of the location to remove from the favorites.

        Raises:
            ValueError: If the favorites is empty or the location ID is invalid.
        """
        logger.info("Removing location with id %d from favorites", location_id)
        self.check_if_empty()
        location_id = self.validate_location_id(location_id)
        self.favorites = [i for i in self.favorites if i.id != location_id]
        logger.info("Location with id %d has been removed", location_id)

    def remove_location_by_index(self, index: int) -> None:
        """
        Removes a location from the favorites by an index (1-indexed).

        Args:
            index (int): The index of the location to remove.

        Raises:
            ValueError: If the favorites is empty or the index is invalid.
        """
        logger.info("Removing location %d from favorites", index)
        self.check_if_empty()
        index = self.validate_index(index)
        favorites_index = index - 1
        logger.info("Removing location: %s", self.favorites[favorites_index].location)
        del self.favorites[favorites_index]

    def clear_favorites(self) -> None:
        """
        Clears all locations from the favorites. If the favorites is already empty, logs a warning.
        """
        logger.info("Clearing favorites")
        if self.get_favorites_length() == 0:
            logger.warning("Clearing an empty favorites")
        self.favorites.clear()

    ##################################################
    # Favorites Retrieval Functions
    ##################################################

    def get_all_favorites(self) -> List[Locations]:
        """
        Returns a list of all locations in the favorites.
        """
        self.check_if_empty()
        logger.info("Getting all locations in the favorites")
        return self.favorites

    def get_location_by_location_id(self, location_id: int) -> Locations:
        """
        Retrieves a location from the favorites by its location ID.

        Args:
            location_id (int): The ID of the location to retrieve.

        Raises:
            ValueError: If the favorites is empty or the location is not found.
        """
        self.check_if_empty()
        location_id = self.validate_location_id(location_id)
        logger.info("Getting location with id %d from favorites", location_id)
        return next((location for location in self.favorites if location.id == location_id), None)

    def get_location_by_index(self, index: int) -> Locations:
        """
        Retrieves a location from the favorites by an index (1-indexed).

        Args:
            index(int): The index of the location to retrieve.

        Raises:
            ValueError: If the favorites is empty or the index is invalid.
        """
        self.check_if_empty()
        index = self.validate_index(index)
        favorites_index = index - 1
        logger.info("Getting location at index %d from favorites", index)
        return self.favorites[favorites_index]

    def get_current_favorite(self) -> Locations:
        """
        Returns the current favorite location.
        """
        self.check_if_empty()
        return self.get_location_by_index(self.favorite_location)

    def get_favorites_length(self) -> int:
        """
        Returns the number of locations in the favorites.
        """
        return len(self.favorites)

    def set_favorite_by_index(self, index: int):
        self.favorite_location = index

    ##################################################
    # Favorites Weather Functions
    ##################################################

    def get_weather_for_location(self, location: Locations) -> str:
        """
    Retrieve a formatted string of weather details for a given location.

    Args:
        location (Locations): The location object containing weather details.

    Returns:
        str: A formatted string with the location's name, latitude, longitude, 
             current temperature, wind speed, and UV index.
    """
        return ("Location: " + location.location + "\n"
                + "Latitude: " + location.latitude + "\n"
                + "Longitude: " + location.longitude + "\n"
                + "Current Temperature: " + location.current_temperature + "\n"
                + "Current Wind Speed: " + location.current_wind_speed + "\n"
                + "Current UVI: " + location.current_uvi + "\n\n")
    
    def get_weather_for_all_favorites(self) -> List[str]:
        
        weathers = []
        for i in range(len(self.favorites)):
            weathers = weathers + self.get_weather_for_location(self.favorites[i])
        return weathers
    
    def get_weather_for_favorite(self):
        return self.get_weather_for_location(self.get_current_favorite())

    ##################################################
    # Utility Functions
    ##################################################

    def validate_location_id(self, location_id: int, check_in_favorites: bool = True) -> int:
        """
        Validates the given location ID, ensuring it is a non-negative integer.

        Args:
            location_id (int): The location ID to validate.
            check_in_favorites (bool, optional): If True, checks if the location ID exists in the favorites.
                                                If False, skips the check. Defaults to True.

        Raises:
            ValueError: If the location ID is not a valid non-negative integer.
        """
        try:
            location_id = int(location_id)
            if location_id < 0:
                logger.error("Invalid location id %d", location_id)
                raise ValueError(f"Invalid location id: {location_id}")
        except ValueError:
            logger.error("Invalid location id %s", location_id)
            raise ValueError(f"Invalid location id: {location_id}")

        if check_in_favorites:
            if location_id not in [i.id for i in self.favorites]:
                logger.error("Location with id %d not found in favorites", location_id)
                raise ValueError(f"Location with id {location_id} not found in favorites")

        return location_id

    def validate_index(self, index: int) -> int:
        """
        Validates the given index, ensuring it is a non-negative integer within the favorites's range.

        Args:
            index (int): The index to validate.

        Raises:
            ValueError: If the index is not a valid non-negative integer or is out of range.
        """
        try:
            index = int(index)
            if index < 1 or index > self.get_favorites_length():
                logger.error("Invalid index %d", index)
                raise ValueError(f"Invalid index: {index}")
        except ValueError:
            logger.error("Invalid index %s", index)
            raise ValueError(f"Invalid index: {index}")

        return index

    def check_if_empty(self) -> None:
        """
        Checks if the favorites is empty, logs an error, and raises a ValueError if it is.

        Raises:
            ValueError: If the favorites is empty.
        """
        if not self.favorites:
            logger.error("Favorites is empty")
            raise ValueError("Favorites is empty")
import logging
import os
import time
from typing import Any, List

from weather_app.models.location_model import Locations
from weather_app.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


TTL = os.getenv("TTL", 60)  # Default TTL is 60 seconds


class FavoritesModel:
    """
    A class to manage a favorites list of locations.

    Attributes:
        favorite_location (int): The current favorite location.
        favorites (List[Locations]): The list of favorited locations.

    """

    def __init__(self):
        """
        Initializes the FavoritesModel with an empty favorites and the current favorite set to 1.
        """
        self.favorite_location = 1
        self.favorites: List[Locations] = []

    ##################################################
    # Location Management Functions
    ##################################################

    def add_location_to_favorites(self, location: Locations) -> None:
        """
        Adds a location to the favorites.

        Args:
            location (Locations): the location to add to the favorites.

        Raises:
            TypeError: If the location is not a valid Locations instance.
            ValueError: If a location with the same 'id' already exists.
        """
        logger.info("Adding new location to favorites")
        if isinstance(location, dict):
            location = Locations(**location)

        if not isinstance(location, Locations):
            logger.error("Location is not a valid location")
            raise TypeError("Location is not a valid location")

        location_id = self.validate_location_id(location.id, check_in_favorites=False)
        if location_id in [i.id for i in self.favorites]:
            logger.error("Location with ID %d already exists in favorites", location.id)
            raise ValueError(f"Location with ID {location.id} already exists in favorites")

        self.favorites.append(location)

    def remove_location_by_location_id(self, location_id: int) -> None:
        """
        Removes a location from the favorites by its location ID.

        Args:
            location_id (int): The ID of the location to remove from the favorites.

        Raises:
            ValueError: If the favorites is empty or the location ID is invalid.
        """
        logger.info("Removing location with id %d from favorites", location_id)
        self.check_if_empty()
        location_id = self.validate_location_id(location_id)
        self.favorites = [i for i in self.favorites if i.id != location_id]
        logger.info("Location with id %d has been removed", location_id)

    def remove_location_by_index(self, index: int) -> None:
        """
        Removes a location from the favorites by an index (1-indexed).

        Args:
            index (int): The index of the location to remove.

        Raises:
            ValueError: If the favorites is empty or the index is invalid.
        """
        logger.info("Removing location %d from favorites", index)
        self.check_if_empty()
        index = self.validate_index(index)
        favorites_index = index - 1
        logger.info("Removing location: %s", self.favorites[favorites_index].location)
        del self.favorites[favorites_index]

    def clear_favorites(self) -> None:
        """
        Clears all locations from the favorites. If the favorites is already empty, logs a warning.
        """
        logger.info("Clearing favorites")
        if self.get_favorites_length() == 0:
            logger.warning("Clearing an empty favorites")
        self.favorites.clear()

    ##################################################
    # Favorites Retrieval Functions
    ##################################################

    def get_all_favorites(self) -> List[Locations]:
        """
        Returns a list of all locations in the favorites.
        """
        self.check_if_empty()
        logger.info("Getting all locations in the favorites")
        return self.favorites

    def get_location_by_location_id(self, location_id: int) -> Locations:
        """
        Retrieves a location from the favorites by its location ID.

        Args:
            location_id (int): The ID of the location to retrieve.

        Raises:
            ValueError: If the favorites is empty or the location is not found.
        """
        self.check_if_empty()
        location_id = self.validate_location_id(location_id)
        logger.info("Getting location with id %d from favorites", location_id)
        return next((location for location in self.favorites if location.id == location_id), None)

    def get_location_by_index(self, index: int) -> Locations:
        """
        Retrieves a location from the favorites by an index (1-indexed).

        Args:
            index(int): The index of the location to retrieve.

        Raises:
            ValueError: If the favorites is empty or the index is invalid.
        """
        self.check_if_empty()
        index = self.validate_index(index)
        favorites_index = index - 1
        logger.info("Getting location at index %d from favorites", index)
        return self.favorites[favorites_index]

    def get_current_favorite(self) -> Locations:
        """
        Returns the current favorite location.
        """
        self.check_if_empty()
        return self.get_location_by_index(self.favorite_location)

    def get_favorites_length(self) -> int:
        """
        Returns the number of locations in the favorites.
        """
        return len(self.favorites)

    def set_favorite_by_index(self, index: int):
        self.favorite_location = index

    ##################################################
    # Favorites Weather Functions
    ##################################################

    def get_weather_for_location(self, location: Locations) -> list[any]:
        """
    Retrieve weather details for a given location.

    Args:
        location (Locations or dict): The location for which to retrieve weather information. 
            If a dictionary is provided, it is converted into a Locations object.

    Returns:
        list[any]: A list containing the location name, latitude, longitude, 
                   current temperature, wind speed, and UV index.
    """
        if isinstance(location, dict):
            location = Locations(**location)

        return [location.location, location.latitude, location.longitude, location.current_temperature, location.current_wind_speed, location.current_uvi]
    
    def get_weather_for_all_favorites(self) -> List[any]:
        """
    Retrieve weather details for all favorite locations.

    Iterates over the list of favorite locations and collects their weather details.

    Returns:
        list[any]: A list of weather details for all favorite locations.
                   Each entry in the list corresponds to the result from 
                   `get_weather_for_location`.
    """
        weathers = []
        for i in range(len(self.favorites)):
            weathers = weathers + self.get_weather_for_location(self.favorites[i])
        return weathers
    
    def get_weather_for_favorite(self):
        """
    Retrieve weather details for the current favorite location.

    Returns:
        list[any]: Weather details for the current favorite location.
                   The result is the same as `get_weather_for_location`.
    """
        return self.get_weather_for_location(self.get_current_favorite())

    ##################################################
    # Utility Functions
    ##################################################

    def validate_location_id(self, location_id: int, check_in_favorites: bool = True) -> int:
        """
        Validates the given location ID, ensuring it is a non-negative integer.

        Args:
            location_id (int): The location ID to validate.
            check_in_favorites (bool, optional): If True, checks if the location ID exists in the favorites.
                                                If False, skips the check. Defaults to True.

        Raises:
            ValueError: If the location ID is not a valid non-negative integer.
        """
        try:
            location_id = int(location_id)
            if location_id < 0:
                logger.error("Invalid location id %d", location_id)
                raise ValueError(f"Invalid location id: {location_id}")
        except ValueError:
            logger.error("Invalid location id %s", location_id)
            raise ValueError(f"Invalid location id: {location_id}")

        if check_in_favorites:
            if location_id not in [i.id for i in self.favorites]:
                logger.error("Location with id %d not found in favorites", location_id)
                raise ValueError(f"Location with id {location_id} not found in favorites")

        return location_id

    def validate_index(self, index: int) -> int:
        """
        Validates the given index, ensuring it is a non-negative integer within the favorites's range.

        Args:
            index (int): The index to validate.

        Raises:
            ValueError: If the index is not a valid non-negative integer or is out of range.
        """
        try:
            index = int(index)
            if index < 1 or index > self.get_favorites_length():
                logger.error("Invalid index %d", index)
                raise ValueError(f"Invalid index: {index}")
        except ValueError:
            logger.error("Invalid index %s", index)
            raise ValueError(f"Invalid index: {index}")

        return index

    def check_if_empty(self) -> None:
        """
        Checks if the favorites is empty, logs an error, and raises a ValueError if it is.

        Raises:
            ValueError: If the favorites is empty.
        """
        if not self.favorites:
            logger.error("Favorites is empty")
            raise ValueError("Favorites is empty")