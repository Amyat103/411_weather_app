import hashlib
import logging
import os

from sqlalchemy.exc import IntegrityError

from weather_app.db import db
from weather_app.utils.logger import configure_logger

logger = logging.getLogger(__name__)
configure_logger(logger)


class Users(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    salt = db.Column(db.String(32), nullable=False)  # 16-byte salt in hex
    password = db.Column(db.String(64), nullable=False)  # SHA-256 hash in hex
    favorite_locations = db.Column(db.String(255), nullable=False, default="")

    @classmethod
    def _generate_hashed_password(cls, password: str) -> tuple[str, str]:
        """
        Generates a salted, hashed password.

        Args:
            password (str): The password to hash.

        Returns:
            tuple: A tuple containing the salt and hashed password.
        """
        salt = os.urandom(16).hex()
        hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
        return salt, hashed_password

    @classmethod
    def create_user(cls, username: str, password: str) -> None:
        """
        Create a new user with a salted, hashed password.

        Args:
            username (str): The username of the user.
            password (str): The password to hash and store.

        Raises:
            ValueError: If a user with the username already exists.
        """
        salt, hashed_password = cls._generate_hashed_password(password)
        new_user = cls(username=username, salt=salt, password=hashed_password)
        try:
            db.session.add(new_user)
            db.session.commit()
            logger.info("User successfully added to the database: %s", username)
        except IntegrityError:
            db.session.rollback()
            logger.error("Duplicate username: %s", username)
            raise ValueError(f"User with username '{username}' already exists")
        except Exception as e:
            db.session.rollback()
            logger.error("Database error: %s", str(e))
            raise

    @classmethod
    def check_password(cls, username: str, password: str) -> bool:
        """
        Check if a given password matches the stored password for a user.

        Args:
            username (str): The username of the user.
            password (str): The password to check.

        Returns:
            bool: True if the password is correct, False otherwise.

        Raises:
            ValueError: If the user does not exist.
        """
        user = cls.query.filter_by(username=username).first()
        if not user:
            logger.info("User %s not found", username)
            raise ValueError(f"User {username} not found")
        hashed_password = hashlib.sha256((password + user.salt).encode()).hexdigest()
        return hashed_password == user.password

    @classmethod
    def delete_user(cls, username: str) -> None:
        """
        Delete a user from the database.

        Args:
            username (str): The username of the user to delete.

        Raises:
            ValueError: If the user does not exist.
        """
        user = cls.query.filter_by(username=username).first()
        if not user:
            logger.info("User %s not found", username)
            raise ValueError(f"User {username} not found")
        db.session.delete(user)
        db.session.commit()
        logger.info("User %s deleted successfully", username)

    @classmethod
    def get_id_by_username(cls, username: str) -> int:
        """
        Retrieve the ID of a user by username.

        Args:
            username (str): The username of the user.

        Returns:
            int: The ID of the user.

        Raises:
            ValueError: If the user does not exist.
        """
        user = cls.query.filter_by(username=username).first()
        if not user:
            logger.info("User %s not found", username)
            raise ValueError(f"User {username} not found")
        return user.id

    @classmethod
    def update_password(cls, username: str, new_password: str) -> None:
        """
        Update the password for a user.

        Args:
            username (str): The username of the user.
            new_password (str): The new password to set.

        Raises:
            ValueError: If the user does not exist.
        """
        user = cls.query.filter_by(username=username).first()
        if not user:
            logger.info("User %s not found", username)
            raise ValueError(f"User {username} not found")

        salt, hashed_password = cls._generate_hashed_password(new_password)
        user.salt = salt
        user.password = hashed_password
        db.session.commit()
        logger.info("Password updated successfully for user: %s", username)

    @classmethod
    def add_favorite_location(cls, username: str, location: str) -> None:
        """
        Add a favorite location to a user's account.

        Args:
            username (str): The username of the user.
            location (str): The location to add.

        Raises:
            ValueError: If the user does not exist.
        """
        user = cls.query.filter_by(username=username).first()
        if not user:
            logger.info("User %s not found", username)
            raise ValueError(f"User {username} not found")

        if user.favorite_locations is "":
            user.favorite_locations = location
        else:
            if user.favorite_locations == "":
                user.favorite_locations = location
            else:
                locations = user.favorite_locations.split(",")
        
                if location not in locations:
                    user.favorite_locations = user.favorite_locations + "," + location
                    db.session.commit()
                    logger.info(
                        "Favorite location added successfully for user: %s", username
                    )

    @classmethod
    def remove_favorite_location(cls, username: str, location: str) -> None:
        """
        Remove a favorite location from a user's account.

        Args:
            username (str): The username of the user.
            location (str): The location to remove.

        Raises:
            ValueError: If the user does not exist or the location is not a favorite.
        """
        user = cls.query.filter_by(username=username).first()
        if not user:
            logger.info("User %s not found", username)
            raise ValueError(f"User {username} not found")

        if not user.favorite_locations:
            logger.info("No favorite locations found for user: %s", username)
            raise ValueError(f"No favorite locations found for user {username}")

        locations = user.favorite_locations.split(",")
        if location not in locations:
            logger.info(
                "Favorite location %s not found for user: %s", location, username
            )
            raise ValueError(
                f"Favorite location {location} not found for user {username}"
            )

        locations.remove(location)
        user.favorite_locations = ",".join(locations) if locations else ""
        db.session.commit()
        logger.info("Favorite location removed successfully for user: %s", username)

    @classmethod
    def get_favorite_locations(cls, username: str) -> list[str]:
        """
        Retrieve the favorite locations for a user.

        Args:
            username (str): The username of the user.

        Returns:
            list: The list of favorite locations.

        Raises:
            ValueError: If the user does not exist.
        """
        user = cls.query.filter_by(username=username).first()
        if not user:
            logger.info("User %s not found", username)
            raise ValueError(f"User {username} not found")

        if not user.favorite_locations:
            return ""
        return user.favorite_locations.split(",")
