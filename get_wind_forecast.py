from datetime import datetime, timedelta
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

import requests

from config import Config


def degrees_to_cardinal(degrees: float) -> str:
    """Convert degrees to cardinal direction"""
    directions = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    ]
    val = int((degrees / 22.5) + 0.5)
    return directions[val % 16]


def convert_icon_code_to_emoji(icon_code: str) -> str:
    """Convert OpenWeatherMap icon code to emoji"""
    icon_map = {
        "01d": "☀️",
        "01n": "🌑",
        "02d": "🌤️",
        "02n": "☁️",
        "03d": "☁️",
        "03n": "☁️",
        "04d": "☁️",
        "04n": "☁️",
        "09d": "🌧️",
        "09n": "🌧️",
        "10d": "🌦️",
        "10n": "🌧️",
        "11d": "🌩️",
        "11n": "🌩️",
        "13d": "❄️",
        "13n": "❄️",
        "50d": "🌫️",
        "50n": "🌫️",
    }
    return icon_map.get(icon_code, "")


def get_sunrise_sunset_data(
    start_date: datetime, num_days: int
) -> Dict[str, Dict[str, datetime]]:
    """Get sunrise/sunset times from SunsetSunrise.io API for a range of dates"""
    end_date = start_date + timedelta(days=num_days - 1)

    params = {
        "lat": Config.LAT,
        "lng": Config.LON,
        "timezone": "UTC",  # request UTC times, convert to local below
        "date_start": start_date.strftime("%Y-%m-%d"),
        "date_end": end_date.strftime("%Y-%m-%d"),
    }

    url = "https://api.sunrisesunset.io/json"

    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise RuntimeError(
            f"Sunrise/sunset API returned status code {response.status_code}"
        )

    data = response.json()

    if data.get("status") != "OK":
        raise RuntimeError(f"Sunrise/sunset API returned status: {data.get('status')}")

    sun_times = {}

    for result in data["results"]:
        date_str = result["date"]
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Parse sunrise and sunset times (format: "8:03:15 AM")
        sunrise_str = result["sunrise"]
        sunset_str = result["sunset"]

        # Combine date and time -> interpret as UTC, then convert to local timezone
        sunrise_naive = datetime.strptime(
            f"{date_str} {sunrise_str}", "%Y-%m-%d %I:%M:%S %p"
        )
        sunset_naive = datetime.strptime(
            f"{date_str} {sunset_str}", "%Y-%m-%d %I:%M:%S %p"
        )

        # Attach UTC tz then convert to configured local timezone
        sunrise_utc = sunrise_naive.replace(tzinfo=ZoneInfo("UTC"))
        sunset_utc = sunset_naive.replace(tzinfo=ZoneInfo("UTC"))

        sunrise_local = sunrise_utc.astimezone(ZoneInfo(Config.TIMEZONE))
        sunset_local = sunset_utc.astimezone(ZoneInfo(Config.TIMEZONE))

        sun_times[date_obj] = {"sunrise": sunrise_local, "sunset": sunset_local}

    return sun_times


def get_wind_forecast() -> List[Dict[str, Any]]:
    """Get wind forecast for next 5 days (single API call cnt=40) and merge sunrise/sunset from sunrisesunset.io"""
    result: List[Dict[str, Any]] = []

    # Start from tomorrow at midnight (local timezone)
    now = datetime.now(tz=ZoneInfo(Config.TIMEZONE))
    start_date = (now + timedelta(days=1)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # Get sunrise/sunset data for the next 5 days
    sun_times = get_sunrise_sunset_data(start_date, 5)

    # Fetch all forecast periods (up to 40 entries = 5 days) in a single call
    params = {
        "lat": Config.LAT,
        "lon": Config.LON,
        "cnt": 40,
        "appid": Config.get_api_key(),
        "units": "imperial",
    }

    url = "http://api.openweathermap.org/data/2.5/forecast"
    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise RuntimeError(f"Forecast API returned status code {response.status_code}")

    data = response.json()

    for period in data.get("list", []):
        dt = datetime.fromtimestamp(period["dt"], tz=ZoneInfo(Config.TIMEZONE))
        date_key = dt.date()

        if date_key not in sun_times:
            continue

        sunrise = sun_times[date_key]["sunrise"]
        sunset = sun_times[date_key]["sunset"]

        forecast_data = {
            "datetime": dt,
            "date_string": dt.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "wind_speed": period["wind"]["speed"],
            "wind_direction": degrees_to_cardinal(period["wind"]["deg"]),
            "wind_degrees": period["wind"]["deg"],
            "wind_gust": period["wind"].get("gust"),
            "sunrise": sunrise,
            "sunset": sunset,
            "temperature": period["main"]["temp"],
            "icon": convert_icon_code_to_emoji(period["weather"][0]["icon"]),
        }
        result.append(forecast_data)

    return result


def print_forecast(forecast_data: List[Dict[str, Any]]) -> None:
    """Print formatted forecast data"""
    print("\nDaily Maximum Wind Speeds:")
    print("=" * 50)

    for data in forecast_data:
        print(f"\n{data['date_string']}")
        print(
            f"Maximum Wind: {data['wind_speed']:>5.1f} mph from the {data['wind_direction']} ({data['wind_degrees']}°)"
        )
        if data["wind_gust"]:
            print(f"Wind Gusts:  {data['wind_gust']:>5.1f} mph")
        else:
            print("Wind Gusts:    N/A")
        print(f"Sunrise:     {data['sunrise'].strftime('%H:%M:%S %Z')}")
        print(f"Sunset:      {data['sunset'].strftime('%H:%M:%S %Z')}")
        print("-" * 50)


if __name__ == "__main__":
    try:
        forecast = get_wind_forecast()
        print_forecast(forecast)
    except Exception as e:
        print(f"Error: {e}")
