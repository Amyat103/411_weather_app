import json
import os

import load_dotenv
import requests

lat = 82.23
lon = 101.1
api_key = os.getenv("API_KEY")
url = requests.get(
    f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={api_key}"
).json()


data = url

# print(data["current"]["temp"])
print(data["current"]["wind_speed"])
