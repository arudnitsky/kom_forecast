from get_wind_forecast import get_wind_forecast
from typing import List, Tuple, Dict, Any, TypeAlias
from datetime import datetime
from zoneinfo import ZoneInfo
from kom_reader import KOMSegment, read_kom_list
from config import Config  # Add this import
import math

WindCondition: TypeAlias = Tuple[float, Dict[str, Any]]
WindConditions: TypeAlias = List[WindCondition]

def wind_direction_score(segment_deg: int, wind_deg: float) -> float:
    """
    Calculate score for wind direction wrt segment direction using cosine for natural decay
    
    Args:
        segment_deg: Segment direction in degrees
        wind_deg: Wind direction in degrees (direction wind is coming from)
    
    Returns:
        float: Favorability score (0-1)
        - 1.0: Perfect alignment (wind exactly in segment direction)
        - 0.0: Any other direction (including perpendicular and headwinds)
    """
    # Convert wind direction from "coming from" to "going to"
    wind_to_deg = (wind_deg + 180) % 360
    
    # Calculate absolute angle difference
    angle_diff = abs(segment_deg - wind_to_deg)
    angle_diff = min(angle_diff, 360 - angle_diff)
    
    # Return 0 if beyond tolerance
    if angle_diff > Config.DIRECTION_TOLERANCE:
        return 0.0
    
    # Use cosine function for smooth decay
    normalized_angle = (angle_diff / Config.DIRECTION_TOLERANCE) * (math.pi / 2)
    return math.cos(normalized_angle)

def calculate_overall_segment_favorability(segment_deg: int, wind_data: Dict[str, Any], min_wind_speed: float = 8.0, direction_tolerance: int = 45) -> float:
    """Calculate overall favorability score"""
    # Skip if wind speed is less than minimum
    if wind_data['wind_speed'] < min_wind_speed:
        return 0
        
    # Get directional favorability (0-1)
    direction_score = wind_direction_score(segment_deg, wind_data['wind_degrees'])
    if direction_score == 0:
        return 0
    
    # Normalize wind speed (0-1, capped at 20mph)
    wind_speed_score = min(wind_data['wind_speed'] / 20.0, 1.0)
    
    # Weight speed more heavily than direction
    # Direction: 30%, Speed: 70%
    return (direction_score * 0.1) + (wind_speed_score * 0.9)

def get_segments() -> List[KOMSegment]:
    """Get all segments from the KOM list"""
    return read_kom_list()

def is_daylight_hours(dt: datetime, sunrise: datetime, sunset: datetime) -> bool:
    """Check if time is between sunrise and sunset"""
    return sunrise.time() <= dt.time() < sunset.time()

def format_wind_conditions(conditions: WindConditions, segment_deg: int) -> List[str]:
    """Format wind conditions into printable strings with angle difference"""
    output = []
    current_date = None
    
    for score, day in conditions:
        date = day['datetime'].date()
        if current_date != date:
            current_date = date
            sunrise_str = day['sunrise'].strftime("%I:%M %p")
            sunset_str = day['sunset'].strftime("%I:%M %p")
            output.append(f"\n  {date.strftime('%Y-%m-%d')} ({Config.SUNRISE_ICON} {sunrise_str} - {Config.SUNSET_ICON} {sunset_str})")
        
        # Calculate absolute angle difference
        wind_to_deg = (day['wind_degrees'] + 180) % 360
        angle_diff = abs(segment_deg - wind_to_deg)
        angle_diff = min(angle_diff, 360 - angle_diff)
        
        # Only include conditions that meet quality threshold
        score_percent = round(score * 100)
        if score_percent >= Config.QUALITY_PERCENTAGE:
            time_str = day['datetime'].strftime("%I:%M %p")
            output.append(
                f"    {time_str} | {day['temperature']:>3.0f}° | {day['wind_speed']:>4.1f} mph from {day['wind_direction']:<3} "
                f"| {angle_diff:>3}° off | {score_percent:>3}% favorable"
            )
    
    return output

def get_favorable_wind_conditions_for_a_segment(
    segment_deg: int, 
    forecast_data: List[Dict[str, Any]], 
    min_wind_speed: float,
    direction_tolerance: int
) -> List[Tuple[float, Dict[str, Any]]]:
    """Get favorable wind conditions for a segment"""
    favorable_conditions = []
    
    for day in forecast_data:
        if not is_daylight_hours(day['datetime'], day['sunrise'], day['sunset']):
            continue
            
        if day['wind_speed'] < Config.MIN_WIND_SPEED:
            continue
            
        favorability = wind_direction_score(segment_deg, day['wind_degrees'])

        if favorability > 0:
            overall_segment_favorability = calculate_overall_segment_favorability(
                segment_deg, 
                day, 
                min_wind_speed,
                direction_tolerance
            )            
            favorable_conditions.append((overall_segment_favorability, day))
    
    return sorted(favorable_conditions, reverse=True, key=lambda x: x[0])

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

def calculate_speed_difference(segment: KOMSegment) -> tuple[float, float]:
    """
    Calculate speed difference needed to beat KOM
    Returns: (speed_difference, kom_speed) in mph
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

def format_time_difference(kom_time: str, my_time: str) -> str:
    """Calculate and format the time difference"""
    kom_seconds = parse_time_to_seconds(kom_time)
    my_seconds = parse_time_to_seconds(my_time)
    diff_seconds = my_seconds - kom_seconds
    
    minutes = int(diff_seconds // 60)
    seconds = int(diff_seconds % 60)
    return f"{minutes}:{seconds:02d}"

def print_segment_opportunity(segment: KOMSegment, conditions: WindConditions) -> None:
    
    formatted_wind_conditions = format_wind_conditions(conditions, segment.get_direction_degrees())
    if len(formatted_wind_conditions) == 1:
        return

    # Calculate speeds and difference needed
    my_speed, speed_diff, kom_speed = calculate_speed_difference(segment)

    """Print segment details and favorable conditions"""
    print(f"\n{segment.segment_name} - {segment.distance} {segment.direction}")
    print(f"\nKOM  : {segment.kom_holder} {segment.kom_time} {kom_speed:.1f} mph")
    print(f"Me   : rank {segment.my_rank} {segment.my_time} {my_speed:.1f} mph")
    
    # Calculate and show time difference
    time_diff = format_time_difference(segment.kom_time, segment.my_time)
    print(f"Need : -{time_diff} min +{speed_diff:.1f} mph ")

    print("\nFavorable Winds:")
    for line in formatted_wind_conditions:
        print(line)
    print("-" * 67)

def main():
    try:
        # Get the forecast data
        forecast_data = get_wind_forecast()
        if forecast_data is None:
            raise RuntimeError("Failed to get wind forecast data")
        
        # Get the segments data
        segments = get_segments()
        
        print(f"(Config: winds {Config.MIN_WIND_SPEED}+ mph, tolerance {Config.DIRECTION_TOLERANCE}°, {Config.QUALITY_PERCENTAGE}%+ favorability)")
        print(f"\nPotential KOM Opportunities:")
        print("=" * 61)
        
        opportunities_found = False
        
        for segment in segments:
            if segment.my_rank == "1":
                continue
                
            # Updated to only pass required parameters
            favorable_conditions = get_favorable_wind_conditions_for_a_segment(
                segment.get_direction_degrees(),
                forecast_data,
                Config.MIN_WIND_SPEED,
                Config.DIRECTION_TOLERANCE
            )
            
            if favorable_conditions:
                opportunities_found = True
                print_segment_opportunity(segment, favorable_conditions)
        
        if not opportunities_found:
            print(f"\nNo segments found with favorable wind conditions")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
