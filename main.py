import math
from datetime import datetime
from typing import Any, Dict, List, Tuple, TypeAlias

from config import Config
from get_wind_forecast import get_wind_forecast
from kom_reader import KOMSegment, read_kom_segments_from_file

WindForecast: TypeAlias = Dict[str, Any]
FavorableWindForecast: TypeAlias = Tuple[float, WindForecast]


def parse_time_to_seconds(time_str: str) -> float:
    """
    Convert time string to seconds
    Handles formats: 'M:SS min', 'MM:SS min'
    """
    # Remove 'min' and whitespace
    clean_time = time_str.replace(" min", "").strip()

    # Split minutes and seconds
    minutes, seconds = map(float, clean_time.split(":"))
    return minutes * 60 + seconds


def calculate_speed_difference_needed(segment: KOMSegment) -> tuple[float, float]:
    """
    Calculate speed difference needed to beat KOM
    Returns: (my_speed from my best attemp, speed_difference, kom_speed) in mph
    """
    # Convert km to miles
    distance_miles = float(segment.distance.split()[0]) * 0.621371

    # Convert times to hours
    kom_time_hours = parse_time_to_seconds(segment.kom_time) / 3600
    my_time_hours = parse_time_to_seconds(segment.my_time) / 3600

    # Calculate speeds (distance/time gives mph since distance is in miles and time in hours)
    kom_speed = distance_miles / kom_time_hours
    my_speed = distance_miles / my_time_hours

    return my_speed, kom_speed - my_speed, kom_speed


def format_time_difference_needed(kom_time: str, my_time: str) -> str:
    """Calculate and format the time difference"""
    kom_seconds = parse_time_to_seconds(kom_time)
    my_seconds = parse_time_to_seconds(my_time)
    diff_seconds = my_seconds - kom_seconds

    minutes = int(diff_seconds // 60)
    seconds = int(diff_seconds % 60)
    return f"{minutes}:{seconds:02d}"


def calculate_absolute_angle_difference(segment_deg: float, wind_deg: float) -> float:
    """
    Calculate absolute angle difference between segment direction and wind direction.

    Args:
        segment_deg (float): Segment direction in degrees.
        wind_deg (float): Wind direction in degrees (direction wind is coming from).

    Returns:
        float: Absolute angle difference in degrees.
    """
    # Convert wind direction from "coming from" to "going to"
    wind_to_deg = (wind_deg + 180) % 360

    # Calculate absolute angle difference
    angle_diff = abs(segment_deg - wind_to_deg)
    return min(angle_diff, 360 - angle_diff)


def format_opportunity(score: float, forecast: WindForecast, segment_deg: float) -> str:
    """
    Format a single opportunity for output.

    Args:
        score (float): Favorability score (0-1).
        forecast (Forecast): Dictionary containing wind data for a time period.
        segment_deg (float): Segment direction in degrees.

    Returns:
        str: Formatted opportunity line.
    """
    angle_diff = calculate_absolute_angle_difference(
        segment_deg, forecast["wind_degrees"]
    )

    score_percent = round(score * 100)
    time_str = forecast["datetime"].strftime("%I:%M %p")

    return (
        f"{forecast['icon']} | {time_str} | {forecast['temperature']:>3.0f}° | "
        f"{forecast['wind_speed']:>4.1f} mph from {forecast['wind_direction']:<3} "
        f"| {angle_diff:>3}° off | {score_percent:>3}% favorable"
    )


def format_day_header(forecast: WindForecast) -> str:
    """Return formatted day header with day name, date, sunrise and sunset."""
    date = forecast["datetime"].date()
    sunrise_str = forecast["sunrise"].strftime("%I:%M %p")
    sunset_str = forecast["sunset"].strftime("%I:%M %p")
    day_name = date.strftime("%A")
    return f"{day_name} {date.strftime('%Y-%m-%d')} ({Config.SUNRISE_ICON} {sunrise_str} - {Config.SUNSET_ICON} {sunset_str})"


def print_segment_details(segment: KOMSegment) -> None:
    """
    Print segment details and stats.
    """
    print(f"{segment.segment_name} {segment.distance} {segment.direction}\n")

    my_speed, speed_diff, kom_speed = calculate_speed_difference_needed(segment)
    print(f"  KOM  : {segment.kom_holder} {segment.kom_time} {kom_speed:.1f} mph")
    print(f"  Me   : rank {segment.my_rank} {segment.my_time} {my_speed:.1f} mph")

    time_diff = format_time_difference_needed(segment.kom_time, segment.my_time)
    print(f"  Need : -{time_diff} min +{speed_diff:.1f} mph ")


def print_favorable_segment_opportunities(
    segment: KOMSegment, favorable_opportunities: List[WindForecast]
) -> None:

    print_segment_details(segment)
    print()
    # print("Favorable Conditions:\n")
    # All opportunities have the same date
    _, first_opportunity = favorable_opportunities[0]
    print("  " + format_day_header(first_opportunity))
    for score, forecast in favorable_opportunities:
        opportunity = format_opportunity(
            score, forecast, segment.get_direction_degrees()
        )
        print("  " + opportunity)
    print()
    print()


def calculate_wind_alignment_score(
    segment_deg: int, wind_deg: float, degree_tolerance: float
) -> float:
    """
    Calculate score for wind direction with respect to segment direction using cosine for natural decay.

    Args:
        segment_deg (int): Segment direction in degrees.
        wind_deg (float): Wind direction in degrees (direction wind is coming from).

    Returns:
        float: Favorability score (0-1).
            1.0: Perfect alignment (wind exactly in segment direction).
            0.0: Completely unfavorable alignment(including perpendicular and headwinds).
    """

    angle_diff = calculate_absolute_angle_difference(segment_deg, wind_deg)

    # Return 0 if beyond tolerance
    if angle_diff > degree_tolerance:
        return 0.0

    # Use cosine function for smooth decay
    normalized_angle = (angle_diff / degree_tolerance) * (math.pi / 2)
    return math.cos(normalized_angle)


def is_daylight_hours(
    datetime_to_check: datetime, sunrise: datetime, sunset: datetime
) -> bool:
    """Check if a given datetime is within daylight hours (between sunrise and sunset)."""
    return sunrise.time() <= datetime_to_check.time() < sunset.time()


def find_favorable_wind_conditions_for_a_segment(
    segment_deg: int,
    forecast_list: List[WindForecast],
    min_wind_speed_needed: float,
    direction_tolerance_in_degrees: float,
    desired_quality_percentage: int,
) -> List[Tuple[float, WindForecast]]:
    """
    Calculate when it's favorable to attempt a segment.

    Args:
        segment_deg (int): Segment direction in degrees.
        forecast_list (List[Forecast]): List of forecast data dictionaries for each time period.
        min_wind_speed_needed (float): Minimum wind speed threshold for consideration.
        direction_tolerance_in_degrees (float): Maximum angle difference for wind to be considered favorable.

    Returns:
        List[Tuple[float, Forecast]]: Sorted list of tuples containing favorability score and day data, descending by score.
    """
    favorable_conditions = []

    for forecast in forecast_list:
        if not is_daylight_hours(
            forecast["datetime"], forecast["sunrise"], forecast["sunset"]
        ):
            continue

        if forecast["wind_speed"] < min_wind_speed_needed:
            continue

        wind_alignment_score = calculate_wind_alignment_score(
            segment_deg, forecast["wind_degrees"], direction_tolerance_in_degrees
        )
        if wind_alignment_score == 0.0:
            continue

        # Normalize wind speed (0-1, capped at Config.TOP_WIND_SPEED)
        wind_speed_score = min(forecast["wind_speed"] / Config.TOP_WIND_SPEED, 1.0)

        # Weight speed more heavily than direction
        # Direction: 30%, Speed: 70%
        overall_score = (wind_alignment_score * 0.3) + (wind_speed_score * 0.7)

        # Score must be better than quality threshold
        overall_score_percentage = round(overall_score * 100)
        if overall_score_percentage < desired_quality_percentage:
            continue

        favorable_conditions.append((overall_score, forecast))

    return sorted(favorable_conditions, reverse=True, key=lambda x: x[0])


def main():
    try:
        # Get the forecast data
        forecast_list = get_wind_forecast()
        if forecast_list is None:
            raise RuntimeError("Failed to get wind forecast data")

        # Get the segments data
        segments = read_kom_segments_from_file()

        from datetime import datetime, timedelta

        today = datetime.now()
        five_days_out = today + timedelta(days=5)
        print(
            f"5-day KOM Segment Forecast\n"
            f"{today.strftime('%A, %B %d %Y')} - {five_days_out.strftime('%A, %B %d %Y')}"
        )
        print(
            f"[Config: winds {Config.MIN_WIND_SPEED}+ mph, tolerance {Config.DIRECTION_TOLERANCE}°, {Config.QUALITY_PERCENTAGE}%+ favorability]\n\n"
        )
        opportunities_found = False

        for segment in segments:
            if segment.my_rank == "1":
                continue

            favorable_opportunities = find_favorable_wind_conditions_for_a_segment(
                segment.get_direction_degrees(),
                forecast_list,
                Config.MIN_WIND_SPEED,
                Config.DIRECTION_TOLERANCE,
                Config.QUALITY_PERCENTAGE,
            )

            if len(favorable_opportunities) > 0:
                opportunities_found = True
                print_favorable_segment_opportunities(segment, favorable_opportunities)

        if not opportunities_found:
            print(f"\nNo segments found with favorable wind conditions")

    except Exception as e:
        import traceback

        print(f"Error: {e}")
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
