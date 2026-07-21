import requests

API_KEY = "f82659018bdd4d61aca221528251311"


def get_weather(city: str):
    """
    WeatherAPI.com version (human-readable weather)
    """

    url = "http://api.weatherapi.com/v1/current.json"

    params = {
        "key": API_KEY,
        "q": city
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return {
            "city": city,
            "error": "Weather API failed"
        }

    data = response.json()

    return {
        "city": city,
        "condition": data["current"]["condition"]["text"],
        "temperature_c": data["current"]["temp_c"],
        "wind_kph": data["current"]["wind_kph"],
        "humidity": data["current"]["humidity"]
    }