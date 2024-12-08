import requests
import json


lat = 82.23
lon = 101.1
api_key = '05853877d8a45f4353e1be717814134d'
url = requests.get(f'https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={api_key}').json()


data  =url

# print(data["current"]["temp"])
print(data["current"]["wind_speed"])
