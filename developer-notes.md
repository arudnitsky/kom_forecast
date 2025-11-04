# Developer notes for KOM-Forecast

uv self update
uv init kom-forecast
uv add requests
uv run main.py

http://bikecalculator.com/how.html



Charlotte, MI coordinates:42°33′49″N 84°50′09″W

## Openweathermap 

### Geocoding api call by zip code
http://api.openweathermap.org/geo/1.0/zip?zip={zip code},{country code}&appid={API key}

curl http://api.openweathermap.org/geo/1.0/zip?zip={48813},{US}&appid={<API key>}

{"zip":"48813","name":"Charlotte","lat":42.5702,"lon":-84.8352,"country":"US"}

### Weather data
https://openweathermap.org/forecast5

curl "api.openweathermap.org/data/2.5/forecast?lat=42.5702&lon=-84.8352&cnt=5&units=imperial&appid=<API key>"

Daily Forecast 16 Days
https://openweathermap.org/forecast16
curl "api.openweathermap.org/data/2.5/forecast?lat=42.5702&lon=-84.8352&cnt={1}&appid=${OPENWEATHER_API_KEY}"


### Weather emojis
https://openweathermap.org/weather-conditions



## SunsetSunrise.io API

https://api.sunrisesunset.io/json?lat=42.5702&lng=-84.8352&timezone=EDT&date_start=2025-10-23&date_end=2025-10-25
{
    "results": [
        {
            "date": "2025-10-23",
            "sunrise": "8:03:15 AM",
            "sunset": "6:46:19 PM",
            "first_light": "6:29:00 AM",
            "last_light": "8:20:35 PM",
            "dawn": "7:34:30 AM",
            "dusk": "7:15:05 PM",
            "solar_noon": "1:24:47 PM",
            "golden_hour": "6:07:13 PM",
            "day_length": "10:43:04",
            "timezone": "America/Detroit",
            "utc_offset": -240
        },
        {
            "date": "2025-10-24",
            "sunrise": "8:04:29 AM",
            "sunset": "6:44:51 PM",
            "first_light": "6:30:07 AM",
            "last_light": "8:19:12 PM",
            "dawn": "7:35:40 AM",
            "dusk": "7:13:40 PM",
            "solar_noon": "1:24:40 PM",
            "golden_hour": "6:05:38 PM",
            "day_length": "10:40:22",
            "timezone": "America/Detroit",
            "utc_offset": -240
        },
        {
            "date": "2025-10-25",
            "sunrise": "8:05:42 AM",
            "sunset": "6:43:24 PM",
            "first_light": "6:31:15 AM",
            "last_light": "8:17:52 PM",
            "dawn": "7:36:50 AM",
            "dusk": "7:12:16 PM",
            "solar_noon": "1:24:33 PM",
            "golden_hour": "6:04:04 PM",
            "day_length": "10:37:41",
            "timezone": "America/Detroit",
            "utc_offset": -240
        }
    ],
    "status": "OK"
}


segment = KOMSegment(
    segment_name=row["Segment name"],
    distance=row["Distance"],
    climb=row["Climb"],
    direction=row["Direction"],
    kom_holder=row["KOM holder"],
    kom_time=row["KOM Time"],
    speed=row["Speed"],
    my_rank=row["My Rank"],
    my_time=row["My Time"],
    my_speed=row["My Speed"],
)

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