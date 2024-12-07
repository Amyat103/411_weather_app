#!/bin/bash

# Define the base URL for the Flask API
BASE_URL="http://localhost:2222/api"

# Flag to control whether to echo JSON output
ECHO_JSON=false

# Parse command-line arguments
while [ "$#" -gt 0 ]; do
  case $1 in
    --echo-json) ECHO_JSON=true ;;
    *) echo "Unknown parameter passed: $1"; exit 1 ;;
  esac
  shift
done


###############################################
#
# Health checks
#
###############################################

# Function to check the health of the service
check_health() {
  echo "Checking health status..."
  curl -s -X GET "$BASE_URL/health" | grep -q '"status": "healthy"'
  if [ $? -eq 0 ]; then
    echo "Service is healthy."
  else
    echo "Health check failed."
    exit 1
  fi
}

##############################################
#
# User management
#
##############################################

# Function to create a user
create_user() {
  echo "Creating a new user..."
  curl -s -X POST "$BASE_URL/create-user" -H "Content-Type: application/json" \
    -d '{"username":"testuser", "password":"password123"}' | grep -q '"status": "user added"'
  if [ $? -eq 0 ]; then
    echo "User created successfully."
  else
    echo "Failed to create user."
    exit 1
  fi
}

# Function to log in a user
login_user() {
  echo "Logging in user..."
  response=$(curl -s -X POST "$BASE_URL/login" -H "Content-Type: application/json" \
    -d '{"username":"testuser", "password":"password123"}')
  if echo "$response" | grep -q '"message": "User testuser logged in successfully."'; then
    echo "User logged in successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Login Response JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to log in user."
    if [ "$ECHO_JSON" = true ]; then
      echo "Error Response JSON:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

# Function to log out a user
logout_user() {
  echo "Logging out user..."
  response=$(curl -s -X POST "$BASE_URL/logout" -H "Content-Type: application/json" \
    -d '{"username":"testuser"}')
  if echo "$response" | grep -q '"message": "User testuser logged out successfully."'; then
    echo "User logged out successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Logout Response JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to log out user."
    if [ "$ECHO_JSON" = true ]; then
      echo "Error Response JSON:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

##############################################
#
# Locations
#
##############################################

# Function to add a Location
create_location() {
  echo "Adding a location..."
  curl -s -X POST "$BASE_URL/create-location" -H "Content-Type: application/json" \
    -d '{"location":"Boston", "latitude":42.3601, "longitude":71.0589}' | grep -q '"status": "location added"'
  if [ $? -eq 0 ]; then
    echo "Location added successfully."
  else
    echo "Failed to add location."
    exit 1
  fi
}

# Function to delete a location by ID (1)
delete_location_by_id() {
  echo "Deleting location by ID (1)..."
  response=$(curl -s -X DELETE "$BASE_URL/delete-location/1")
  if echo "$response" | grep -q '"status": "location deleted"'; then
    echo "Location deleted successfully by ID (1)."
  else
    echo "Failed to delete location by ID (1)."
    exit 1
  fi
}

# Function to get a location by ID (1)
get_location_by_id() {
  echo "Getting location by ID (1)..."
  response=$(curl -s -X GET "$BASE_URL/get-location-by-id/1")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Location retrieved successfully by ID (1)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Location JSON (ID 1):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get location by ID (1)."
    exit 1
  fi
}

# Function to get a location by name
get_location_by_name() {
  echo "Getting location by name (Boston)..."
  response=$(curl -s -X GET "$BASE_URL/get-location-by-name/Boston")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Location retrieved successfully by name (Boston)."
    if [ "$ECHO_JSON" = true ]; then
      echo "Location JSON (Boston):"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get location by name (Boston)."
    exit 1
  fi
}

############################################
#
# Favorites
#
############################################

# Function to clear favorites
clear_favorites() {
  echo "Clearing favorites..."
  curl -s -X POST "$BASE_URL/clear-favorites" -H "Content-Type: application/json" | grep -q '"status": "favorites cleared"'
  if [ $? -eq 0 ]; then
    echo "Favorites cleared successfully."
  else
    echo "Failed to clear favorites."
    exit 1
  fi
}

# Function to get the current list of favorites
get_all_favorites() {
  echo "Getting the current list of favorites..."
  response=$(curl -s -X GET "$BASE_URL/get-all-favorites")

  # Check if the response contains locations or an empty list
  if echo "$response" | grep -q '"favorites"'; then
    echo "Favorites retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Favorites JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get favorites or no favorites found."
    if [ "$ECHO_JSON" = true ]; then
      echo "Error or empty response:"
      echo "$response" | jq .
    fi
    exit 1
  fi
}

# Function to add location to favorites
add_location_to_favorites() {
  echo "Adding a location to favorites..."
  curl -s -X POST "$BASE_URL/add-location-to-favorites" -H "Content-Type: application/json" \
    -d '{"location":"Boston"}' | grep -q '"status": "Location added to favorites"'
  if [ $? -eq 0 ]; then
    echo "Location added to favorites successfully."
  else
    echo "Failed to add location to favorites."
    exit 1
  fi
}

######################################################
#
# Leaderboard
#
######################################################

# Function to get weather for all favorites
get_weather_for_all_favorites() {
  echo "Getting weather for all favorites..."
  response=$(curl -s -X GET "$BASE_URL/get-weather-for-all-favorites")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "All favorites retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Favorites JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get weather for all favorites."
    exit 1
  fi
}

# Function to get the weather for the favorite
get_weather_for_favorite() {
  echo "Getting weather for favorite..."
  response=$(curl -s -X GET "$BASE_URL/get-weather-for-favorite")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Weather for favorite retrieved successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Weather for favorite:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to get weather for favorite."
    exit 1
  fi
}

# Function to initialize the database
init_db() {
  echo "Initializing the database..."
  response=$(curl -s -X POST "$BASE_URL/init-db")
  if echo "$response" | grep -q '"status": "success"'; then
    echo "Database initialized successfully."
    if [ "$ECHO_JSON" = true ]; then
      echo "Initialization Response JSON:"
      echo "$response" | jq .
    fi
  else
    echo "Failed to initialize the database."
    exit 1
  fi
}



# Run all the steps in order
check_health
init_db
create_user
login_user
create_location
clear_favorites
add_location_to_favorites
add_location_to_favorites
get_all_favorites
get_weather_for_all_favorites
logout_user
get_location_by_name
get_location_by_id
delete_location_by_id

echo "All tests passed successfully!"