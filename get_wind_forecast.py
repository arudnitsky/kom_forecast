import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict, Any
from config import Config

def degrees_to_cardinal(degrees: float) -> str:
    """Convert degrees to cardinal direction"""
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                 "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    val = int((degrees/22.5) + 0.5)
    return directions[val % 16]

def get_wind_forecast() -> List[Dict[str, Any]]:
    params = {
        'lat': Config.LAT,
        'lon': Config.LON,
        'cnt': 60,
        'appid': Config.get_api_key(),
        'units': 'imperial'
    }
    
    url = 'http://api.openweathermap.org/data/2.5/forecast'
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        raise RuntimeError(f"API returned status code {response.status_code}")
    
    data = response.json()
    result = []
    
    # Extract city sunrise/sunset data
    city_data = data.get('city', {})
    base_sunrise = datetime.fromtimestamp(city_data.get('sunrise', 0), tz=ZoneInfo("America/New_York"))
    base_sunset = datetime.fromtimestamp(city_data.get('sunset', 0), tz=ZoneInfo("America/New_York"))
    
    for period in data['list']:
        dt = datetime.fromtimestamp(period['dt'], tz=ZoneInfo("America/New_York"))
        
        # Adjust sunrise/sunset times for the current day
        sunrise = base_sunrise.replace(year=dt.year, month=dt.month, day=dt.day)
        sunset = base_sunset.replace(year=dt.year, month=dt.month, day=dt.day)
        
        forecast_data = {
            'datetime': dt,
            'date_string': dt.strftime('%Y-%m-%d %H:%M:%S %Z'),
            'wind_speed': period['wind']['speed'],
            'wind_direction': degrees_to_cardinal(period['wind']['deg']),
            'wind_degrees': period['wind']['deg'],
            'wind_gust': period['wind'].get('gust'),
            'sunrise': sunrise,
            'sunset': sunset,
            'temperature': period['main']['temp']
        }
        result.append(forecast_data)
    
    return result

def print_forecast(forecast_data: List[Dict[str, Any]]) -> None:
    """Print formatted forecast data"""
    print("\nDaily Maximum Wind Speeds:")
    print("=" * 50)
    
    for data in forecast_data:
        print(f"\n{data['date_string']}")
        print(f"Maximum Wind: {data['wind_speed']:>5.1f} mph from the {data['wind_direction']} ({data['wind_degrees']}°)")
        if data['wind_gust']:
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