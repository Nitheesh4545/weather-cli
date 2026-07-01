#!/usr/bin/env python3
"""
weather.py — A simple command-line weather app.

Uses the free Open-Meteo API (https://open-meteo.com) — no API key required.

Usage:
    python weather.py "London"
    python weather.py "New York" --units imperial
    python weather.py "Tokyo" --forecast 5
    python weather.py "Paris" --forecast 3 --units imperial
"""

import argparse
import sys
from datetime import datetime

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# WMO weather interpretation codes -> (description, emoji)
WEATHER_CODES = {
    0: ("Clear sky", "☀️"),
    1: ("Mainly clear", "🌤️"),
    2: ("Partly cloudy", "⛅"),
    3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"),
    48: ("Depositing rime fog", "🌫️"),
    51: ("Light drizzle", "🌦️"),
    53: ("Moderate drizzle", "🌦️"),
    55: ("Dense drizzle", "🌧️"),
    56: ("Light freezing drizzle", "🌧️"),
    57: ("Dense freezing drizzle", "🌧️"),
    61: ("Slight rain", "🌦️"),
    63: ("Moderate rain", "🌧️"),
    65: ("Heavy rain", "🌧️"),
    66: ("Light freezing rain", "🌨️"),
    67: ("Heavy freezing rain", "🌨️"),
    71: ("Slight snow fall", "🌨️"),
    73: ("Moderate snow fall", "❄️"),
    75: ("Heavy snow fall", "❄️"),
    77: ("Snow grains", "❄️"),
    80: ("Slight rain showers", "🌦️"),
    81: ("Moderate rain showers", "🌧️"),
    82: ("Violent rain showers", "⛈️"),
    85: ("Slight snow showers", "🌨️"),
    86: ("Heavy snow showers", "❄️"),
    95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with slight hail", "⛈️"),
    99: ("Thunderstorm with heavy hail", "⛈️"),
}


class WeatherAppError(Exception):
    """Raised for any user-facing error in the app."""


def geocode_city(city: str) -> dict:
    """Look up latitude/longitude and display name for a city."""
    try:
        resp = requests.get(
            GEOCODE_URL,
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=10,
        )
        resp.raise_for_status()
    except requests.RequestException as e:
        raise WeatherAppError(f"Could not reach the geocoding service: {e}")

    data = resp.json()
    results = data.get("results")
    if not results:
        raise WeatherAppError(f'No location found for "{city}". Check the spelling and try again.')

    place = results[0]
    return {
        "name": place["name"],
        "country": place.get("country", ""),
        "admin1": place.get("admin1", ""),
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "timezone": place.get("timezone", "auto"),
    }


def fetch_weather(latitude: float, longitude: float, units: str, forecast_days: int) -> dict:
    """Fetch current weather and an optional daily forecast."""
    temp_unit = "fahrenheit" if units == "imperial" else "celsius"
    wind_unit = "mph" if units == "imperial" else "kmh"
    precip_unit = "inch" if units == "imperial" else "mm"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
                   "weather_code,wind_speed_10m,wind_direction_10m",
        "temperature_unit": temp_unit,
        "wind_speed_unit": wind_unit,
        "precipitation_unit": precip_unit,
        "timezone": "auto",
    }

    if forecast_days > 0:
        params["daily"] = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum"
        params["forecast_days"] = min(forecast_days, 16)

    try:
        resp = requests.get(FORECAST_URL, params=params, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise WeatherAppError(f"Could not reach the weather service: {e}")

    return resp.json()


def describe_code(code: int) -> tuple:
    return WEATHER_CODES.get(code, ("Unknown", "❔"))


def print_current(location: dict, weather: dict, units: str) -> None:
    current = weather.get("current", {})
    if not current:
        raise WeatherAppError("No current weather data returned.")

    temp_symbol = "°F" if units == "imperial" else "°C"
    speed_unit = "mph" if units == "imperial" else "km/h"

    desc, emoji = describe_code(current.get("weather_code", -1))
    place_bits = [location["name"]]
    if location.get("admin1"):
        place_bits.append(location["admin1"])
    if location.get("country"):
        place_bits.append(location["country"])
    place_str = ", ".join(place_bits)

    print()
    print(f"{emoji}  Weather for {place_str}")
    print("-" * (len(place_str) + 16))
    print(f"  Condition:    {desc}")
    print(f"  Temperature:  {current.get('temperature_2m')}{temp_symbol} "
          f"(feels like {current.get('apparent_temperature')}{temp_symbol})")
    print(f"  Humidity:     {current.get('relative_humidity_2m')}%")
    print(f"  Wind:         {current.get('wind_speed_10m')} {speed_unit}")
    print()


def print_forecast(weather: dict, units: str) -> None:
    daily = weather.get("daily")
    if not daily:
        return

    temp_symbol = "°F" if units == "imperial" else "°C"
    dates = daily.get("time", [])
    codes = daily.get("weather_code", [])
    highs = daily.get("temperature_2m_max", [])
    lows = daily.get("temperature_2m_min", [])
    precip = daily.get("precipitation_sum", [])

    print(f"{'Day':<12}{'Condition':<24}{'High':<10}{'Low':<10}{'Precip'}")
    print("-" * 66)
    for i in range(len(dates)):
        date_obj = datetime.strptime(dates[i], "%Y-%m-%d")
        day_label = date_obj.strftime("%a %m/%d")
        desc, emoji = describe_code(codes[i]) if i < len(codes) else ("Unknown", "❔")
        high = f"{highs[i]}{temp_symbol}" if i < len(highs) else "-"
        low = f"{lows[i]}{temp_symbol}" if i < len(lows) else "-"
        rain = f"{precip[i]}{'in' if units == 'imperial' else 'mm'}" if i < len(precip) else "-"
        print(f"{day_label:<12}{emoji + ' ' + desc:<24}{high:<10}{low:<10}{rain}")
    print()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="weather",
        description="Get current weather and forecasts from the command line.",
    )
    parser.add_argument("city", help='City name to look up, e.g. "London" or "New York"')
    parser.add_argument(
        "--units",
        choices=["metric", "imperial"],
        default="metric",
        help="Units to display (default: metric)",
    )
    parser.add_argument(
        "--forecast",
        type=int,
        default=0,
        metavar="DAYS",
        help="Include an N-day daily forecast (1-16 days)",
    )
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        location = geocode_city(args.city)
        weather = fetch_weather(
            location["latitude"], location["longitude"], args.units, args.forecast
        )
        print_current(location, weather, args.units)
        if args.forecast > 0:
            print_forecast(weather, args.units)
        return 0
    except WeatherAppError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nCancelled.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
