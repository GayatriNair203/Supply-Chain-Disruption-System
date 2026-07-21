import os
import requests


TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")


CITY_COORDS = {
    "Houston": (29.7604, -95.3698),
    "Dallas": (32.7767, -96.7970),
    "Atlanta": (33.7490, -84.3880),
    "Chicago": (41.8781, -87.6298),
    "Los Angeles": (34.0522, -118.2437),
    "Seattle": (47.6062, -122.3321),
    "Miami": (25.7617, -80.1918),
    "New York": (40.7128, -74.0060),
    "Boston": (42.3601, -71.0589),
    "Denver": (39.7392, -104.9903),
    "Phoenix": (33.4484, -112.0740),
    "San Francisco": (37.7749, -122.4194),
    "Orlando": (28.5383, -81.3792),
    "Charlotte": (35.2271, -80.8431),
    "Memphis": (35.1495, -90.0490),
}


def get_route_data(origin: str, destination: str):
    if not TOMTOM_API_KEY:
        return {
            "origin": origin,
            "destination": destination,
            "error": "TomTom API key not found",
            "route_risk": "Unknown",
        }

    if origin not in CITY_COORDS or destination not in CITY_COORDS:
        return {
            "origin": origin,
            "destination": destination,
            "error": "Coordinates not available",
            "route_risk": "Unknown",
        }

    origin_lat, origin_lon = CITY_COORDS[origin]
    dest_lat, dest_lon = CITY_COORDS[destination]

    url = (
        "https://api.tomtom.com/routing/1/calculateRoute/"
        f"{origin_lat},{origin_lon}:{dest_lat},{dest_lon}/json"
    )

    params = {
        "key": TOMTOM_API_KEY,
        "traffic": "true",
        "travelMode": "truck",
        "routeType": "fastest",
    }

    try:
        response = requests.get(url, params=params, timeout=15)

        if response.status_code != 200:
            return {
                "origin": origin,
                "destination": destination,
                "error": f"TomTom Routing API error: {response.status_code}",
                "route_risk": "Unknown",
            }

        data = response.json()
        summary = data["routes"][0]["summary"]

        distance_km = round(summary["lengthInMeters"] / 1000, 1)
        travel_time_hours = round(summary["travelTimeInSeconds"] / 3600, 1)
        traffic_delay_minutes = round(summary.get("trafficDelayInSeconds", 0) / 60, 1)

        if traffic_delay_minutes >= 90 or distance_km >= 1800:
            route_risk = "High"
        elif traffic_delay_minutes >= 30 or distance_km >= 900:
            route_risk = "Medium"
        else:
            route_risk = "Low"

        return {
            "origin": origin,
            "destination": destination,
            "distance_km": distance_km,
            "travel_time_hours": travel_time_hours,
            "traffic_delay_minutes": traffic_delay_minutes,
            "route_risk": route_risk,
        }

    except Exception as e:
        return {
            "origin": origin,
            "destination": destination,
            "error": str(e),
            "route_risk": "Unknown",
        }