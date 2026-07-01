# Weather CLI

A simple command-line weather app. No API key required — powered by the free
[Open-Meteo](https://open-meteo.com) API.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
# Current weather
python weather.py "London"

# Current weather in imperial units (°F, mph)
python weather.py "New York" --units imperial

# Current weather + 5-day forecast
python weather.py "Tokyo" --forecast 5

# Combine options
python weather.py "Paris" --forecast 3 --units imperial
```

### Options

| Flag | Description |
|---|---|
| `city` | City name to look up (required), e.g. `"London"` |
| `--units` | `metric` (default) or `imperial` |
| `--forecast DAYS` | Include a daily forecast for N days (1–16) |

## Example output

```
⛅  Weather for London, England, United Kingdom
-----------------------------------------------
  Condition:    Partly cloudy
  Temperature:  15.3°C (feels like 14.1°C)
  Humidity:     72%
  Wind:         12.4 km/h

Day         Condition               High      Low       Precip
------------------------------------------------------------------
Wed 07/01   ⛅ Partly cloudy         18.2°C    11.0°C    0.0mm
Thu 07/02   🌦️ Slight rain          16.5°C    10.2°C    3.2mm
Fri 07/03   ☀️ Clear sky            20.1°C    12.4°C    0.0mm
```

## How it works

1. **Geocoding** — the city name is resolved to latitude/longitude via Open-Meteo's
   geocoding API.
2. **Forecast** — current conditions (and optional daily forecast) are fetched from
   Open-Meteo's forecast API using those coordinates.
3. Weather codes (WMO standard) are mapped to human-readable descriptions and emoji.

## Tests

A test suite with mocked API responses is included:

```bash
python test_weather.py
```

## Possible extensions

- Cache geocoding results locally to avoid repeat lookups
- Add a `--json` flag for machine-readable output
- Support multiple cities in one command
- Add hourly forecast support

THX-JUN2626-298
