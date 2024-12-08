from dotenv import load_dotenv
from flask import Flask, jsonify, make_response, Response, request
from werkzeug.exceptions import BadRequest, Unauthorized
# from flask_cors import CORS

from config import ProductionConfig
from weather_app.db import db
from weather_app.models.favorites_model import FavoritesModel
from weather_app.models.location_model import Locations
from weather_app.models.mongo_session_model import login_user, logout_user
from weather_app.models.user_model import Users

# Load environment variables from .env file
load_dotenv()

def create_app(config_class=ProductionConfig):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)  # Initialize db with app
    with app.app_context():
        db.create_all()  # Recreate all tables

    favorites_model = FavoritesModel()



    ####################################################
    #
    # Healthchecks
    #
    ####################################################


    @app.route('/api/health', methods=['GET'])
    def healthcheck() -> Response:
        """
        Health check route to verify the service is running.

        Returns:
            JSON response indicating the health status of the service.
        """
        app.logger.info('Health check')
        return make_response(jsonify({'status': 'healthy'}), 200)

    ##########################################################
    #
    # User management
    #
    ##########################################################

    @app.route('/api/create-user', methods=['POST'])
    def create_user() -> Response:
        """
        Route to create a new user.

        Expected JSON Input:
            - username (str): The username for the new user.
            - password (str): The password for the new user.

        Returns:
            JSON response indicating the success of user creation.
        Raises:
            400 error if input validation fails.
            500 error if there is an issue adding the user to the database.
        """
        app.logger.info('Creating new user')
        try:
            # Get the JSON data from the request
            data = request.get_json()

            # Extract and validate required fields
            username = data.get('username')
            password = data.get('password')

            if not username or not password:
                return make_response(jsonify({'error': 'Invalid input, both username and password are required'}), 400)

            # Call the User function to add the user to the database
            app.logger.info('Adding user: %s', username)
            Users.create_user(username, password)

            app.logger.info("User added: %s", username)
            return make_response(jsonify({'status': 'user added', 'username': username}), 201)
        except Exception as e:
            app.logger.error("Failed to add user: %s", str(e))
            return make_response(jsonify({'error': str(e)}), 500)

    @app.route('/api/delete-user', methods=['DELETE'])
    def delete_user() -> Response:
        """
        Route to delete a user.

        Expected JSON Input:
            - username (str): The username of the user to be deleted.

        Returns:
            JSON response indicating the success of user deletion.
        Raises:
            400 error if input validation fails.
            500 error if there is an issue deleting the user from the database.
        """
        app.logger.info('Deleting user')
        try:
            # Get the JSON data from the request
            data = request.get_json()

            # Extract and validate required fields
            username = data.get('username')

            if not username:
                return make_response(jsonify({'error': 'Invalid input, username is required'}), 400)

            # Call the User function to delete the user from the database
            app.logger.info('Deleting user: %s', username)
            Users.delete_user(username)

            app.logger.info("User deleted: %s", username)
            return make_response(jsonify({'status': 'user deleted', 'username': username}), 200)
        except Exception as e:
            app.logger.error("Failed to delete user: %s", str(e))
            return make_response(jsonify({'error': str(e)}), 500)

    @app.route('/api/login', methods=['POST'])
    def login():
        """
        Route to log in a user and load their combatants.

        Expected JSON Input:
            - username (str): The username of the user.
            - password (str): The user's password.

        Returns:
            JSON response indicating the success of the login.

        Raises:
            400 error if input validation fails.
            401 error if authentication fails (invalid username or password).
            500 error for any unexpected server-side issues.
        """
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            app.logger.error("Invalid request payload for login.")
            raise BadRequest("Invalid request payload. 'username' and 'password' are required.")

        username = data['username']
        password = data['password']

        try:
            # Validate user credentials
            if not Users.check_password(username, password):
                app.logger.warning("Login failed for username: %s", username)
                raise Unauthorized("Invalid username or password.")

            # Get user ID
            user_id = Users.get_id_by_username(username)

            # Load user's combatants into the battle model
            login_user(user_id, favorites_model)

            app.logger.info("User %s logged in successfully.", username)
            return jsonify({"message": f"User {username} logged in successfully."}), 200

        except Unauthorized as e:
            return jsonify({"error": str(e)}), 401
        except Exception as e:
            app.logger.error("Error during login for username %s: %s", username, str(e))
            return jsonify({"error": "An unexpected error occurred."}), 500


    @app.route('/api/logout', methods=['POST'])
    def logout():
        """
        Route to log out a user and save their combatants to MongoDB.

        Expected JSON Input:
            - username (str): The username of the user.

        Returns:
            JSON response indicating the success of the logout.

        Raises:
            400 error if input validation fails or user is not found in MongoDB.
            500 error for any unexpected server-side issues.
        """
        data = request.get_json()
        if not data or 'username' not in data:
            app.logger.error("Invalid request payload for logout.")
            raise BadRequest("Invalid request payload. 'username' is required.")

        username = data['username']

        try:
            # Get user ID
            user_id = Users.get_id_by_username(username)

            # Save user's combatants and clear the battle model
            logout_user(user_id, favorites_model)

            app.logger.info("User %s logged out successfully.", username)
            return jsonify({"message": f"User {username} logged out successfully."}), 200

        except ValueError as e:
            app.logger.warning("Logout failed for username %s: %s", username, str(e))
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            app.logger.error("Error during logout for username %s: %s", username, str(e))
            return jsonify({"error": "An unexpected error occurred."}), 500


    ##########################################################
    #
    # Locations
    #
    ##########################################################


    @app.route('/api/create-location', methods=['POST'])
    def add_location() -> Response:
        """
        Route to add a new location to the database.

        Expected JSON Input:
            - location (str): Name of location.
            - latitude (float): Latitude of the location, decimal (−90; 90)
            - longitude (float): Longitude of the location, decimal (-180; 180)

        Returns:
            JSON response indicating the success of the location addition.
        Raises:
            400 error if input validation fails.
            500 error if there is an issue adding the location to the database.
        """
        app.logger.info('Creating new location')
        try:
            # Get the API data from the request
            data1 = request.get_json()
            lat = data1.get('latitude')
            lon = data1.get('longitude')

            # Get data from OpenWeatherMap API
            api_key = ''
            url = f'https://api.openweathermap.org/data/3.0/onecall?lat={lat}lon={lon}&appid={api_key}'
            data = request.get(url)

            # Extract and validate required fields
            location = lon = data1.get('location')
            latitude = lat
            longitude = lon
            current_temperature = data['current']['temp']
            current_wind_speed = data['current']['wind_speed']
            current_rain = data['daily']['rain']

            if not location or not latitude or not longitude or not current_temperature or not current_wind_speed or not current_rain:
                raise BadRequest("Invalid input. All fields are required with valid values.")

            # Call the Locations function to add the location to the database
            app.logger.info('Adding location: %s, %f, %f, %f, %f, %f', location, latitude, longitude, current_temperature, current_wind_speed, current_rain)
            Locations.create_location(location, latitude, longitude, current_temperature, current_wind_speed, current_rain)

            app.logger.info("Location added: %s", location)
            return make_response(jsonify({'status': 'location added', 'location': location}), 201)
        except Exception as e:
            app.logger.error("Failed to add location: %s", str(e))
            return make_response(jsonify({'error': str(e)}), 500)


    @app.route('/api/delete-location/<int:location_id>', methods=['DELETE'])
    def delete_location(location_id: int) -> Response:
        """
        Route to delete a location by its ID. This performs a soft delete by marking it as deleted.

        Path Parameter:
            - location_id (int): The ID of the location to delete.

        Returns:
            JSON response indicating success of the operation or error message.
        """
        try:
            app.logger.info(f"Deleting location by ID: {location_id}")

            Locations.delete_location(location_id)
            return make_response(jsonify({'status': 'location deleted'}), 200)
        except Exception as e:
            app.logger.error(f"Error deleting location: {e}")
            return make_response(jsonify({'error': str(e)}), 500)


    @app.route('/api/get-location-by-id/<int:location_id>', methods=['GET'])
    def get_location_by_id(location_id: int) -> Response:
        """
        Route to get a location by its ID.

        Path Parameter:
            - location_id (int): The ID of the location.

        Returns:
            JSON response with the location details or error message.
        """
        try:
            app.logger.info(f"Retrieving location by ID: {location_id}")

            location = Locations.get_location_by_id(location_id)
            return make_response(jsonify({'status': 'success', 'location': location}), 200)
        except Exception as e:
            app.logger.error(f"Error retrieving location by ID: {e}")
            return make_response(jsonify({'error': str(e)}), 500)


    @app.route('/api/get-location-by-name/<string:location_name>', methods=['GET'])
    def get_location_by_name(location_name: str) -> Response:
        """
        Route to get a location by its name.

        Path Parameter:
            - location_name (str): The name of the location.

        Returns:
            JSON response with the location details or error message.
        """
        try:
            app.logger.info(f"Retrieving location by name: {location_name}")

            if not location_name:
                return make_response(jsonify({'error': 'Location name is required'}), 400)

            location = Locations.get_location_by_name(location_name)
            return make_response(jsonify({'status': 'success', 'location': location}), 200)
        except Exception as e:
            app.logger.error(f"Error retrieving location by name: {e}")
            return make_response(jsonify({'error': str(e)}), 500)


    @app.route('/api/init-db', methods=['POST'])
    def init_db():
        """
        Initialize or recreate database tables.

        This route initializes the database tables defined in the SQLAlchemy models.
        If the tables already exist, they are dropped and recreated to ensure a clean
        slate. Use this with caution as all existing data will be deleted.

        Returns:
            Response: A JSON response indicating the success or failure of the operation.

        Logs:
            Logs the status of the database initialization process.
        """
        try:
            with app.app_context():
                app.logger.info("Dropping all existing tables.")
                db.drop_all()  # Drop all existing tables
                app.logger.info("Creating all tables from models.")
                db.create_all()  # Recreate all tables
            app.logger.info("Database initialized successfully.")
            return jsonify({"status": "success", "message": "Database initialized successfully."}), 200
        except Exception as e:
            app.logger.error("Failed to initialize database: %s", str(e))
            return jsonify({"status": "error", "message": "Failed to initialize database."}), 500
        
    # update_location

    # update_cache_for_location

    ############################################################
    #
    # Favorites
    #
    ############################################################

    @app.route('/api/clear-favorites', methods=['POST'])
    def clear_favorites() -> Response:
        """
        Route to clear the list of favorites.

        Returns:
            JSON response indicating success of the operation.
        Raises:
            500 error if there is an issue clearing locations.
        """
        try:
            app.logger.info('Clearing all favorites...')
            favorites_model.clear_favorites()
            app.logger.info('Favorites cleared.')
            return make_response(jsonify({'status': 'favorites cleared'}), 200)
        except Exception as e:
            app.logger.error("Failed to clear favorites: %s", str(e))
            return make_response(jsonify({'error': str(e)}), 500)

    @app.route('/api/get-all-favorites', methods=['GET'])
    def get_all_favorites() -> Response:
        """
        Route to get the list of combatants for the battle.

        Returns:
            JSON response with the list of combatants.
        """
        try:
            app.logger.info('Getting combatants...')
            combatants = favorites_model.get_all_favorites()
            return make_response(jsonify({'status': 'success', 'favorites': combatants}), 200)
        except Exception as e:
            app.logger.error("Failed to get favorites: %s", str(e))
            return make_response(jsonify({'error': str(e)}), 500)

    @app.route('/api/add-location-to-favorites', methods=['POST'])
    def add_location_to_favorites() -> Response:
        """
        Route to add a location to the favorites by location key.

        Expected JSON Input:
            - location (str): The location's name.

        Returns:
            JSON response indicating success of the addition or error message.
        """
        try:
            data = request.get_json()

            location_name = data.get('location')

            if not location_name:
                return make_response(jsonify({'error': 'Invalid input. Name of location is required.'}), 400)

            # Lookup the song by compound key
            location = Locations.get_location_by_name(location_name)

            # Add song to playlist
            favorites_model.add_location_to_favorites(location)

            app.logger.info(f"Location added to favorites: {location}")
            return make_response(jsonify({'status': 'success', 'message': 'Location added to playlist'}), 201)

        except Exception as e:
            app.logger.error(f"Error adding location to playlist: {e}")
            return make_response(jsonify({'error': str(e)}), 500)


    ############################################################
    #
    # Favorites Functions
    #
    ############################################################


    @app.route('/api/get-weather-for-all-favorites', methods=['POST'])
    def get_weather_for_all_favorites() -> Response:
        """
        Route to getting weather for all favorites.

        Returns:
            JSON response indicating success of the operation.
        Raises:
            500 error if there is an issue getting weather for all favorites.
        """
        try:
            app.logger.info('Getting weather for all favorites')
            favorites_model.get_weather_for_all_favorites()
            return make_response(jsonify({'status': 'success'}), 200)
        except Exception as e:
            app.logger.error(f"Error getting weather for all favorites: {e}")
            return make_response(jsonify({'error': str(e)}), 500)

    @app.route('/api/get-weather-for-favorite', methods=['POST'])
    def get_weather_for_favorite() -> Response:
        """
        Route to getting weather for current favorite.

        Returns:
            JSON response indicating success of the operation.
        Raises:
            500 error if there is an issue getting weather for all favorites.
        """
        try:
            app.logger.info('Getting weather for favorite')
            favorites_model.get_weather_for_favorite()
            return make_response(jsonify({'status': 'success'}), 200)
        except Exception as e:
            app.logger.error(f"Error getting weather for favorite: {e}")
            return make_response(jsonify({'error': str(e)}), 500)

    return app




if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5002)