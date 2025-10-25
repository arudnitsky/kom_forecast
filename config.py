import os


class Config:
    """Configuration settings for segment wind analysis"""

    # Wind conditions for testing
    # MIN_WIND_SPEED = 1.0  # Minimum wind speed to consider (mph)
    # DIRECTION_TOLERANCE = 50  # Maximum degrees off perfect alignment
    # QUALITY_PERCENTAGE = 0  # Minimum favorable percentage to show
    # TOP_WIND_SPEED = 20.0  # Wind speed at which favorability caps (mph)

    # Wind conditions
    MIN_WIND_SPEED = 15.0  # Minimum wind speed to consider (mph)
    DIRECTION_TOLERANCE = 15  # Maximum degrees off perfect alignment
    QUALITY_PERCENTAGE = 75  # Minimum favorable percentage to show
    TOP_WIND_SPEED = 20.0  # Wind speed at which favorability caps (mph)

    # Cached forecast file for testing
    CACHE_FILE = "forecast_cache.json"

    # Location - Charlotte, MI
    LAT = 42.5702  # Latitude for weather forecast
    LON = -84.8352  # Longitude for weather forecast
    TIMEZONE = "America/New_York"  # Timezone for time calculations

    # Output formatting
    # SUNRISE_ICON = "☀️"  # Icon for sunrise times
    # SUNSET_ICON = "🌑"  # Icon for sunset times

    SUNRISE_ICON = "🌅"  # Icon for sunrise times 
    SUNSET_ICON = "🌌"  # Icon for sunset times 

    @classmethod
    def get_api_key(cls) -> str:
        """Get API key from environment variable"""
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            raise ValueError("OPENWEATHER_API_KEY environment variable not set")
        return api_key
