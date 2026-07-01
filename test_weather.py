import sys
from unittest.mock import patch, MagicMock
import weather

MOCK_GEOCODE_RESPONSE = {
    "results": [
        {
            "name": "London",
            "country": "United Kingdom",
            "admin1": "England",
            "latitude": 51.5074,
            "longitude": -0.1278,
            "timezone": "Europe/London",
        }
    ]
}

MOCK_FORECAST_RESPONSE = {
    "current": {
        "temperature_2m": 15.3,
        "apparent_temperature": 14.1,
        "relative_humidity_2m": 72,
        "weather_code": 2,
        "wind_speed_10m": 12.4,
        "wind_direction_10m": 210,
    },
    "daily": {
        "time": ["2026-07-01", "2026-07-02", "2026-07-03"],
        "weather_code": [2, 61, 0],
        "temperature_2m_max": [18.2, 16.5, 20.1],
        "temperature_2m_min": [11.0, 10.2, 12.4],
        "precipitation_sum": [0.0, 3.2, 0.0],
    },
}


def fake_get(url, params=None, timeout=None):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    if "geocoding" in url:
        resp.json.return_value = MOCK_GEOCODE_RESPONSE
    else:
        resp.json.return_value = MOCK_FORECAST_RESPONSE
    return resp


def fake_get_no_results(url, params=None, timeout=None):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = {"results": []}
    return resp


print("=== TEST 1: current weather only ===")
with patch("requests.get", side_effect=fake_get):
    code = weather.main(["London"])
    assert code == 0

print("=== TEST 2: current + forecast, imperial units ===")
with patch("requests.get", side_effect=fake_get):
    code = weather.main(["London", "--units", "imperial", "--forecast", "3"])
    assert code == 0

print("=== TEST 3: city not found (error path) ===")
with patch("requests.get", side_effect=fake_get_no_results):
    code = weather.main(["Nowhereville"])
    assert code == 1

print("\nAll tests passed.")
