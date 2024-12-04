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
    def delete_meal(cls, location_id: int) -> None:
        """
        Soft delete a location by marking it as deleted.

        Args:
            location_id (int): The ID of the location to delete.

        Raises:
            ValueError: If the location with the given ID does not exist or is already deleted.
        """
        location = cls.query.filter_by(id=location_id).first()
        if not location:
            logger.info("Meal %s not found", location_id)
            raise ValueError(f"Meal {location_id} not found")
        if location.deleted:
            logger.info("Meal with ID %s has already been deleted", location_id)
            raise ValueError(f"Meal with ID {location_id} has been deleted")

        location.deleted = True
        db.session.commit()
        logger.info("Meal with ID %s marked as deleted.", location_id)

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
        if not Locations or location.deleted:
            logger.info("Location with %s %s not found", "name" if location else "ID", location or location_id)
            raise ValueError(f"Location {location or location_id} not found")
        # Convert the meal object to a dictionary and cache it
        logger.info("Location retrieved from database and cached: %s", location_id)
        location_dict = asdict(Locations)
        redis_client.hset(cache_key, mapping={k: str(v) for k, v in location_dict.items()})
        return location_dict

    @classmethod
    def get_meal_by_name(cls, meal_name: str) -> dict[str, Any]:
        """
        Retrieve a meal by its name, using a cached association between name and ID.

        Args:
            meal_name (str): The name of the meal.

        Returns:
            dict: The meal data as a dictionary.

        Raises:
            ValueError: If the meal does not exist or is deleted.
        """
        logger.info("Retrieving meal by name: %s", meal_name)
        cache_key = f"meal_name:{meal_name}"

        # Check if name-to-ID association is cached
        meal_id = redis_client.get(cache_key)
        if meal_id:
            logger.info("Meal ID %s retrieved from cache for name: %s", meal_id.decode(), meal_name)
            # Use get_meal_by_id to retrieve the full meal data from ID
            return cls.get_meal_by_id(int(meal_id.decode()), meal_name)

        # Fallback to database if cache miss
        meal = cls.query.filter_by(meal=meal_name).first()
        if not meal or meal.deleted:
            logger.info("Meal with name %s not found", meal_name)
            raise ValueError(f"Meal {meal_name} not found")

        # Cache the name-to-ID association and retrieve the full meal data
        # TODO: This should happen when a meal is created, not here
        logger.info("Caching meal ID %s for name: %s", meal.id, meal_name)
        redis_client.set(cache_key, str(meal.id))
        return cls.get_meal_by_id(meal.id, meal_name)

    @classmethod
    def update_location(cls, location_id: int, **kwargs) -> None:
        """
        Update attributes of a meal.

        Args:
            meal_id (int): The ID of the meal to update.
            kwargs: Key-value pairs of attributes to update (excluding 'meal').

        Raises:
            ValueError: If any attribute is invalid or if the meal is not found.
        """
        location = cls.query.filter_by(id=location_id).first()
        if not location or location.deleted is True:
            logger.info("Location with ID %s not found", location_id)
            raise ValueError(f"Location {location_id} not found")

        logger.debug("Updating location with ID %s: %s", location_id, kwargs)

        db.session.commit()
        logger.info("Location with ID %s updated successfully", location_id)

    @classmethod
    def update_meal_stats(cls, meal_id: int, result: str) -> None:
        """
        Update meal stats (battles and wins).

        Args:
            meal_id (int): The ID of the meal.
            result (str): 'win' or 'loss' to update the stats.

        Raises:
            ValueError: If the meal is not found, deleted, or the result is invalid.
        """
        meal = cls.query.filter_by(id=meal_id).first()
        if not meal:
            logger.info("Meal with ID %s not found", meal_id)
            raise ValueError(f"Meal {meal_id} not found")
        if meal.deleted:
            logger.info("Meal with ID %s has been deleted", meal_id)
            raise ValueError(f"Meal {meal_id} has been deleted")

        if result == 'win':
            meal.battles += 1
            meal.wins += 1
        elif result == 'loss':
            meal.battles += 1
        else:
            raise ValueError(f"Invalid result: {result}. Expected 'win' or 'loss'.")

        db.session.commit()
        logger.info("Meal stats updated for ID %s: %s", meal_id, result)

def update_cache_for_meal(mapper, connection, target):
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
    cache_key = f"meal:{target.id}"
    if target.deleted:
        redis_client.delete(cache_key)
    else:
        redis_client.hset(
            cache_key,
            mapping={k.encode(): str(v).encode() for k, v in asdict(target).items()}
        )

# Register the listener for update and delete events
event.listen(Meals, 'after_update', update_cache_for_meal)
event.listen(Meals, 'after_delete', update_cache_for_meal)