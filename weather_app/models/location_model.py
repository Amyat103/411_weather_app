from dataclasses import asdict, dataclass
import logging
from typing import Any, List

from sqlalchemy import event
from sqlalchemy.exc import IntegrityError

from weather_app.clients.redis_client import redis_client
from weather_app.db import db
from weather_app.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


@dataclass
class Locations(db.Model):
    __tablename__ = 'locations'

    id: int = db.Column(db.Integer, primary_key=True)
    location: str = db.Column(db.String(80), unique=True, nullable=False)
    latitude: float = db.Column(db.Float, nullable=False)
    longitude: float = db.Column(db.Float, nullable=False)
    current_temperature: float = db.Column(db.Float, nullable=False)
    current_wind_speed: float = db.Column(db.Float, nullable=False)
    current_rain: float = db.Column(db.Float, nullable=False)
    deleted: bool = db.Column(db.Boolean, default=False)

    def __post_init__(self):
        if self.current_wind_speed < 0:
            raise ValueError("Wind speed must be a positive value.")

    @classmethod
    def create_location(cls, location: str, latitude: float, longitude: float, current_temperature: float, current_wind_speed: float, current_rain: float) -> None:
        """
        Create a new location in the database.

        Args:
            location (str): The name of the location.
            latitude (float): Latitude of the location, decimal (−90; 90)
            longitude (float): Longitude of the location, decimal (-180; 180)
            current_temperature (float): Temperature Fahrenheit
            current_wind_speed (float): Wind speed miles/hour
            current_rain (float): Precipitation, mm/h


        Raises:
            ValueError: If location is already made
            IntegrityError: If there is a database error.
        """
        # Create and commit the new meal
        new_location = cls(location=location, latitude=latitude, longitude=longitude, current_temperature=current_temperature, current_wind_speed=current_wind_speed, current_rain=current_rain)
        try:
            db.session.add(new_location)
            db.session.commit()
            logger.info("Location successfully added to the database: %s", location)
        except Exception as e:
            db.session.rollback()
            if isinstance(e, IntegrityError):
                logger.error("Duplicate location name: %s", location)
                raise ValueError(f"Location with name '{location}' already exists")
            else:
                logger.error("Database error: %s", str(e))
                raise

    @classmethod
    def delete_location(cls, location_id: int) -> None:
        """
        Soft delete a location by marking it as deleted.

        Args:
            location_id (int): The ID of the location to delete.

        Raises:
            ValueError: If the location with the given ID does not exist or is already deleted.
        """
        location = cls.query.filter_by(id=location_id).first()
        if not location:
            logger.info("Location %s not found", location_id)
            raise ValueError(f"Location {location_id} not found")
        if location.deleted:
            logger.info("Location with ID %s has already been deleted", location_id)
            raise ValueError(f"Location with ID {location_id} has been deleted")

        location.deleted = True
        db.session.commit()
        logger.info("Location with ID %s marked as deleted.", location_id)

    @classmethod
    def get_location_by_id(cls, location_id: int, location: str = None) -> dict[str, Any]:
        """
        Retrieve a location by its ID.

        Args:
            location_id (int): The ID of the location.
            location (str, optional): The name of the location, if available.

        Returns:
            dict: The location data as a dictionary.

        Raises:
            ValueError: If the location does not exist or is deleted.
        """
        logger.info("Retrieving location by ID: %s", location_id)
        cache_key = f"location_{location_id}" #look at??????
        cached_location = redis_client.hgetall(cache_key)
        if cached_location:
            logger.info("Location retrieved from cache: %s", location_id)
            location_data = {k.decode(): v.decode() for k, v in cached_location.items()}
            # meal_data['deleted'] is a string. We need to convert it to a bool
            location_data['deleted'] = location_data.get('deleted', 'false').lower() == 'true'
            if location_data['deleted']:
                logger.info("Location with %s %s not found", "name" if location else "ID", location or location_id)
                raise ValueError(f"Location {location or location_id} not found")
            return location_data
        Locations = cls.query.filter_by(id=location_id).first()
        if not Locations or Locations.deleted:
            logger.info("Location with %s %s not found", "name" if location else "ID", location or location_id)
            raise ValueError(f"Location {location or location_id} not found")
        # Convert the meal object to a dictionary and cache it
        logger.info("Location retrieved from database and cached: %s", location_id)
        location_dict = asdict(Locations)
        redis_client.hset(cache_key, mapping={k: str(v) for k, v in location_dict.items()})
        return location_dict

    @classmethod
    def get_location_by_name(cls, location_name: str) -> dict[str, Any]:
        """
        Retrieve a location by its name, using a cached association between name and ID.

        Args:
            location_name (str): The name of the location.

        Returns:
            dict: The location data as a dictionary.

        Raises:
            ValueError: If the location does not exist or is deleted.
        """
        logger.info("Retrieving location by name: %s", location_name)
        cache_key = f"location_name:{location_name}"

        # Check if name-to-ID association is cached
        location_id = redis_client.get(cache_key)
        if location_id:
            logger.info("Location ID %s retrieved from cache for name: %s", location_id.decode(), location_name)
            # Use get_location_by_id to retrieve the full location data from ID
            return cls.get_location_by_id(int(location_id.decode()), location_name)

        # Fallback to database if cache miss
        location = cls.query.filter_by(location=location_name).first()
        if not location or location.deleted:
            logger.info("Location with name %s not found", location_name)
            raise ValueError(f"Location {location_name} not found")

        # Cache the name-to-ID association and retrieve the full location data
        # TODO: This should happen when a location is created, not here
        logger.info("Caching location ID %s for name: %s", location.id, location_name)
        redis_client.set(cache_key, str(location.id))
        return cls.get_location_by_id(location.id, location_name)

    @classmethod
    def update_location(cls, location_id: int, **kwargs) -> None:
        """
        Update attributes of a location.

        Args:
            location_id (int): The ID of the location to update.
            kwargs: Key-value pairs of attributes to update (excluding 'location', 'latitude' and 'longitude').

        Raises:
            ValueError: If any attribute is invalid or if the location is not found.
        """
        location = cls.query.filter_by(id=location_id).first()
        if not location or location.deleted is True:
            logger.info("Location with ID %s not found", location_id)
            raise ValueError(f"Location {location_id} not found")

        logger.debug("Updating location with ID %s: %s", location_id, kwargs)

        for key, value in kwargs.items():
            if hasattr(location, key):
                setattr(location, key, value)
            else:
                logger.info("Invalid attribute: %s", key)
                raise ValueError(f"Invalid attribute: {key}")
        db.session.commit()
        logger.info("Location with ID %s updated successfully", location_id)


def update_cache_for_location(mapper, connection, target):
    """
    Update the Redis cache for a meal entry after an update or delete operation.

    This function is intended to be used as an SQLAlchemy event listener for the
    `after_update` and `after_delete` events on the Meals model. When a meal is
    updated or deleted, this function will either update the corresponding Redis
    cache entry with the new meal details or remove the entry if the meal has
    been marked as deleted.

    Args:
        mapper (Mapper): The SQLAlchemy Mapper object, which provides information
                         about the model being updated (automatically passed by SQLAlchemy).
        connection (Connection): The SQLAlchemy Connection object used for the
                                 database operation (automatically passed by SQLAlchemy).
        target (Meals): The instance of the Meals model that was updated or deleted.
                        The `target` object contains the updated meal data.

    Side-effects:
        - If the meal is marked as deleted (`target.deleted` is True), the function
          removes the corresponding cache entry from Redis.
        - If the meal is not marked as deleted, the function updates the Redis cache
          entry with the latest meal data using the `hset` command.
    """
    cache_key = f"location:{target.id}"
    if target.deleted:
        redis_client.delete(cache_key)
    else:
        redis_client.hset(
            cache_key,
            mapping={k.encode(): str(v).encode() for k, v in asdict(target).items()}
        )

# Register the listener for update and delete events
event.listen(Locations, 'after_update', update_cache_for_location)
event.listen(Locations, 'after_delete', update_cache_for_location)