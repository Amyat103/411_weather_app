# Weather Application

## High-level Overview

This weather application uses the OpenWeatherMap API to get weather data
for given locations, from latitude and longitude values. The application
also allows users the ability to set favorite locations, get weather
information for those locations, and the application stores everything
in a database. Because of this, users can easily get weather information
for their personal interests and needs.

### Running the app and Weather API

- Run the docker script
- Get API key form Open Weather App's API and add it to environment file

## Routes

#### Route: `/create-account`

- Request Type: POST
- Purpose: Creates a new user account with a username and password
- Request Body:
  - username (String): User's chosen username
  - password (String): User's chosen password
- Response Format: JSON
  - Success Response Example:
    - Code: 201
    - Content: { "message": "Account created successfully", "status": "201" }
  - Example Request: { "username": "newuser123", "password": "securepassword" }
  - Example Response: { "message": "Account created successfully", "status": "201" }

#### Route: `/delete-user`

- Request Type: DELETE
- Purpose: Deletes a user
- Request Body:
  - username (String): Username of the user to delete
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: { "status": "user deleted" }
  - Example Request: { "username": "newuser123" }
  - Example Response: { "status": "user deleted", "Username": "newuser123" }

#### Route: `/login`

- Request Type: POST
- Purpose: Logs a user in and loads their favorites
- Request Body:
  - username (String): User's chosen username
  - password (String): User's chosen password
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: { "message": "Login successful" }
  - Example Request: { "username": "newuser123", "password": "securepassword" }
  - Example Response: { "message": "Login successful", "status": "200" }

#### Route: `/logout`

- Request Type: POST
- Purpose: Logs a user out and saves their favorites to MongoDB
- Request Body:
  - username (String): User's chosen username
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: { "message": "User {username} logged out successfully" }
  - Example Request: { "username": "newuser123" }
  - Example Response: { "message": "User newuser123 logged out successfully", "status": "200" }

#### Route: `/update-password`

- Request Type: POST
- Purpose: Updates a user's password
- Request Body:
  - username (String): User's chosen username
  - current_password (String): Current password for verification
  - new_password (String): New password to set
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: { "message": "Password updated successfully" }
  - Example Request: {
    "username": "newuser123",
    "current_password": "securepassword",
    "new_password": "new_password"
    }
  - Example Response: { "message": "Password updated successfully", "status": "200" }

#### Route: `/create-location`

- Request Type: POST
- Purpose: Adds a new location to the database
- Request Body:
  - location (String): Name of location
  - latitude (float): Latitude of the location, decimal (−90; 90)
  - longitude (float): Longitude of the location, decimal (-180; 180)
- Response Format: JSON
  - Success Response Example:
    - Code: 201
    - Content: { "status": "location added" }
  - Example Request: {
    "location": "Boston",
    "latitude": 42.3601,
    "longitude": 71.0589
    }
  - Example Response: { "status": "location added" }

#### Route: `/delete-location`

- Request Type: DELETE
- Purpose: Deletes a location from the database
- Request Body:
  - location_id (int): The ID of the location to delete
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: { "status": "location deleted" }
  - Example Request: { "location_id": 1 }
  - Example Response: { "status": "location deleted" }

#### Route: `/get-location-by-id`

- Request Type: GET
- Purpose: Get a location by its ID
- Request Body:
  - location_id (int): The ID of the location
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: { "status": "success", "location": location }
  - Example Request: { "location_id": 1 }
  - Example Response: { "status": "success", "location": <location> }

#### Route: `/get-location-by-name`

- Request Type: GET
- Purpose: Get a location by its name
- Request Body:
  - location_name (String): The name of the location
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: { "status": "success", "location": location }
  - Example Request: { "location_name": "Boston" }
  - Example Response: { "status": "success", "location": <location> }

#### Route: `/api/init-db`

- Request Type: POST
- Purpose: Initializes or recreates all database tables, dropping existing ones if present.
- Request Body: None
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: { "status": "success", "message": "Database initialized successfully." }
  - Error Response Example:
    - Code: 500
    - Content: { "status": "error", "message": "Failed to initialize database." }

#### Route: `/api/clear-favorites`

- Request Type: POST
- Purpose: Clears all locations from the favorites list.
- Request Body: None
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: { "status": "favorites cleared" }
  - Error Response Example:
    - Code: 500
    - Content: { "error": "Error message" }

#### Route: `/api/get-all-favorites`

- Request Type: GET
- Purpose: Retrieves all favorite locations from the database.
- Request Body: None
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: { "status": "success", "favorites": [...] }
  - Error Response Example:
    - Code: 500
    - Content: { "error": "Error message" }

#### Route: `/api/add-location-to-favorites`

- Request Type: POST
- Purpose: Adds a specified location to the favorites list.
- Request Body:
  - location (String): The name of the location to add.
- Response Format: JSON
  - Success Response Example:
    - Code: 201
    - Content: { "status": "success", "message": "Location added to favorites" }
  - Error Response Example:
    - Code: 400
    - Content: { "error": "Invalid input. Name of location is required." }
    - Code: 500
    - Content: { "error": "Error message" }

#### Route: `/api/get-weather-for-all-favorites`

- Request Type: GET
- Purpose: Retrieves weather information for all favorite locations.
- Request Body: None
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: { "status": "success" }
  - Error Response Example:
    - Code: 500
    - Content: { "error": "Error message" }

#### Route: `/api/get-weather-for-favorite`

- Request Type: GET
- Purpose: Retrieves weather information for the current favorite location.
- Request Body: None
- Response Format: JSON
  - Success Response Example:
    - Code: 200
    - Content: { "status": "success" }
  - Error Response Example:
    - Code: 500
    - Content: { "error": "Error message" }

## Testing (Unit and Smoke)

## Unit tests

4 units tests

- ### User Model
  ![User Model](/data/unit_test_user.png)
- ### Location Model
  ![Location Model](/data/unit_test_location.png)
- ### Favorites Model
  ![Favorites Model](/data/unit_test_favorites.png)
- ### MongoDB Session Model
  ![MongoDB Session Model](/data/unit_test_mongo.png)

## Smoke Test

![Smoke Test](/data/smoke_test_res.png)
