import logging
from typing import Any, List

from weather_app.clients.mongo_client import sessions_collection
from weather_app.utils.logger import configure_logger


logger = logging.getLogger(__name__)
configure_logger(logger)


def login_user(user_id: int, favorite_model) -> None:
    """
    Load the user's locations from MongoDB into the FavoritesModel's locations list.

    Checks if a session document exists for the given `user_id` in MongoDB.
    If it exists, clears any current locations in `favorite_model` and loads
    the stored locations from MongoDB into `favorite_model`.

    If no session is found, it creates a new session document for the user
    with an empty favorite list in MongoDB.

    Args:
        user_id (int): The ID of the user whose session is to be loaded.
        favorite_model (FavoritesModel): An instance of `FavoritesModel` where the user's favorite locations
                                    will be loaded.
    """
    logger.info("Attempting to log in user with ID %d.", user_id)
    session = sessions_collection.find_one({"user_id": user_id})

    if session:
        logger.info("Session found for user ID %d. Loading favorites into FavoriteModels.", user_id)
        favorite_model.clear_favorites()
        for location in session.get("favorites", []):
            logger.debug("Preparing location: %s", location)
            favorite_model.add_location_to_favorites(location)
        logger.info("location successfully loaded for user ID %d.", user_id)
    else:
        logger.info("No session found for user ID %d. Creating a new session with empty favorite list.", user_id)
        sessions_collection.insert_one({"user_id": user_id, "favorites": []})
        logger.info("New session created for user ID %d.", user_id)

def logout_user(user_id: int, favorite_model) -> None:
    """
    Store the current favorites from the FavoritesModel back into MongoDB.

    Retrieves the current favorites from `favorites_model` and attempts to store them in
    the MongoDB session document associated with the given `user_id`. If no session
    document exists for the user, raises a `ValueError`.

    After saving the combatants to MongoDB, the favorites list in `favorite_model` is
    cleared to ensure a fresh state for the next login.

    Args:
        user_id (int): The ID of the user whose session data is to be saved.
        favorite_model (FavoritesModel): An instance of `FavoritesModel` from which the user's
                                    current favorites are retrieved.

    Raises:
        ValueError: If no session document is found for the user in MongoDB.
    """
    logger.info("Attempting to log out user with ID %d.", user_id)
    favorites_data = favorite_model.get_all_favorites()
    logger.debug("Current favorites for user ID %d: %s", user_id, favorites_data)

    result = sessions_collection.update_one(
        {"user_id": user_id},
        {"$set": {"favorites": favorites_data}},
        upsert=False  # Prevents creating a new document if not found
    )

    if result.matched_count == 0:
        logger.error("No session found for user ID %d. Logout failed.", user_id)
        raise ValueError(f"User with ID {user_id} not found for logout.")

    logger.info("Favorites successfully saved for user ID %d. Clearing FavoritesModel favorites.", user_id)
    favorite_model.clear_favorites()
    logger.info("FavoritesModel favorites cleared for user ID %d.", user_id)
