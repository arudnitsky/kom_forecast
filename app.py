"""
FastAPI web application for KOM-Forecast.

Serves the forecast UI and provides API endpoints for configuration and forecast data.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import Config
from get_wind_forecast import WindForecast, get_wind_forecast
from kom_reader import KOMSegment, read_kom_segments_from_file
from main import (
    build_segment_stats,
    calculate_absolute_angle_difference,
    calculate_speed_difference_needed,
    find_favorable_wind_conditions_for_a_segment,
    format_time_difference_needed,
)

app = FastAPI(title="KOM-Forecast", description="Strava KOM wind forecast tool")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


def build_opportunity_data(
    score: float, forecast: WindForecast, segment_deg: int
) -> Dict[str, Any]:
    """
    Build a dictionary representing a single forecast opportunity for template rendering.

    Args:
        score: Favorability score (0.0-1.0).
        forecast: Wind forecast data dictionary for a single time period.
        segment_deg: Segment heading in degrees.

    Returns:
        Dictionary with keys: score_percent, time_str, temperature, wind_speed,
        wind_direction, angle_diff, icon.
    """
    angle_diff = calculate_absolute_angle_difference(
        segment_deg, forecast["wind_degrees"]
    )
    return {
        "score_percent": round(score * 100),
        "time_str": forecast["datetime"].strftime("%I:%M %p"),
        "temperature": forecast["temperature"],
        "wind_speed": forecast["wind_speed"],
        "wind_direction": forecast["wind_direction"],
        "angle_diff": round(angle_diff),
        "icon": forecast["icon"],
    }


def build_day_group(
    date_key: str,
    first_forecast: WindForecast,
    opportunities: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build a day-group dictionary for template rendering.

    Args:
        date_key: ISO date string (YYYY-MM-DD).
        first_forecast: The first forecast entry for this day (used for sunrise/sunset).
        opportunities: List of opportunity dicts for this day.

    Returns:
        Dictionary with keys: date_key, day_name, date_display, sunrise, sunset, opportunities.
    """
    date_obj = first_forecast["datetime"].date()
    return {
        "date_key": date_key,
        "day_name": date_obj.strftime("%A"),
        "date_display": date_obj.strftime("%Y-%m-%d"),
        "sunrise": first_forecast["sunrise"].strftime("%I:%M %p"),
        "sunset": first_forecast["sunset"].strftime("%I:%M %p"),
        "opportunities": opportunities,
    }


def build_segment_view(
    segment: KOMSegment,
    favorable_opportunities: List[Tuple[float, WindForecast]],
) -> Dict[str, Any]:
    """
    Build a complete segment view dictionary for template rendering.

    Includes segment stats (KOM holder, times, speed difference needed)
    and grouped daily opportunities.

    Args:
        segment: The KOM segment dataclass.
        favorable_opportunities: Scored and sorted list of (score, forecast) tuples.

    Returns:
        Dictionary with segment metadata, stats, and a list of day_groups.
    """
    stats = build_segment_stats(segment)
    my_speed, speed_diff, kom_speed = calculate_speed_difference_needed(segment)
    time_diff = format_time_difference_needed(segment.kom_time, segment.my_time)
    segment_deg = segment.get_direction_degrees()

    # Group opportunities by date
    day_groups: List[Dict[str, Any]] = []
    current_date: Optional[str] = None
    current_opportunities: List[Dict[str, Any]] = []
    current_first_forecast: Optional[WindForecast] = None

    for score, forecast in favorable_opportunities:
        date_key = forecast["datetime"].date().isoformat()
        opp = build_opportunity_data(score, forecast, segment_deg)

        if date_key != current_date:
            if current_date is not None and current_first_forecast is not None:
                day_groups.append(
                    build_day_group(
                        current_date, current_first_forecast, current_opportunities
                    )
                )
            current_date = date_key
            current_opportunities = [opp]
            current_first_forecast = forecast
        else:
            current_opportunities.append(opp)

    # Append the last group
    if current_date is not None and current_first_forecast is not None:
        day_groups.append(
            build_day_group(current_date, current_first_forecast, current_opportunities)
        )

    return {
        "segment_name": segment.segment_name,
        "distance": segment.distance,
        "direction": segment.direction.strip(),
        "direction_degrees": segment_deg,
        "climb": segment.climb,
        "kom_holder": segment.kom_holder,
        "kom_time": segment.kom_time,
        "kom_speed": f"{kom_speed:.1f}",
        "my_rank": segment.my_rank,
        "my_time": segment.my_time,
        "my_speed": f"{my_speed:.1f}",
        "time_diff": time_diff,
        "speed_diff": f"{speed_diff:.1f}",
        "day_groups": day_groups,
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    """
    Render the main forecast page.

    Fetches wind forecast data and KOM segments, computes favorability scores,
    and renders the full HTML view with all segment opportunities.

    Query parameters (optional, sent from localStorage via JS):
        min_wind_speed: Minimum wind speed threshold (float).
        direction_tolerance: Max degrees off alignment (float).
        quality_percentage: Minimum favorability score (int).
    """
    error_message: Optional[str] = None
    segment_views: List[Dict[str, Any]] = []
    today = datetime.now()
    five_days_out = today + timedelta(days=5)

    # Read config overrides from query params (sent from localStorage via JS)
    min_wind = float(request.query_params.get("min_wind_speed", Config.MIN_WIND_SPEED))
    tolerance = float(
        request.query_params.get("direction_tolerance", Config.DIRECTION_TOLERANCE)
    )
    quality = int(
        request.query_params.get("quality_percentage", Config.QUALITY_PERCENTAGE)
    )

    try:
        forecast_list = get_wind_forecast()
        if forecast_list is None:
            raise RuntimeError("Failed to get wind forecast data")

        segments = read_kom_segments_from_file("kom-list.csv")

        for segment in segments:
            if segment.my_rank.strip() == "1":
                continue

            favorable = find_favorable_wind_conditions_for_a_segment(
                segment.get_direction_degrees(),
                forecast_list,
                min_wind,
                tolerance,
                quality,
            )

            if len(favorable) > 0:
                segment_views.append(build_segment_view(segment, favorable))

    except Exception as e:
        error_message = str(e)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "segment_views": segment_views,
            "date_range_start": today.strftime("%A, %B %d %Y"),
            "date_range_end": five_days_out.strftime("%A, %B %d %Y"),
            "min_wind_speed": min_wind,
            "direction_tolerance": tolerance,
            "quality_percentage": quality,
            "error_message": error_message,
        },
    )


@app.get("/api/config", response_class=JSONResponse)
async def get_config() -> JSONResponse:
    """
    Return default configuration values as JSON.

    Used by the frontend to populate the settings form on first load
    (before any localStorage overrides exist).

    Returns:
        JSON with keys: min_wind_speed, direction_tolerance, quality_percentage.
    """
    return JSONResponse(
        {
            "min_wind_speed": Config.MIN_WIND_SPEED,
            "direction_tolerance": Config.DIRECTION_TOLERANCE,
            "quality_percentage": Config.QUALITY_PERCENTAGE,
        }
    )
