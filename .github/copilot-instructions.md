# Copilot Instructions for KOM-Forecast

## Project Overview

KOM-Forecast is a Python web application (with CLI fallback) that identifies optimal times to attempt Strava cycling KOM (King of the Mountain) segments based on wind conditions. It correlates segment directions with 5-day wind forecasts to find tailwind opportunities during daylight hours.

## Architecture

```
app.py               → FastAPI web application, routes, template data builders
server.py            → Uvicorn entry point (uv run server.py)
main.py              → CLI entry point, orchestration, favorability scoring algorithms
config.py            → Location, thresholds (MIN_WIND_SPEED, DIRECTION_TOLERANCE), API key
get_wind_forecast.py → OpenWeatherMap + SunriseSunset.io API integration
kom_reader.py        → CSV parser for KOM segment data (KOMSegment dataclass)
templates/           → Jinja2 HTML templates (base.html, index.html)
static/              → CSS (style.css) and JS (app.js) assets
```

**Data Flow**: `kom-list.csv` → `kom_reader.py` → `app.py` ← `get_wind_forecast.py` (APIs) → Jinja2 templates → Browser

## Development Commands

```bash
uv run server.py                  # Run the web app (http://127.0.0.1:8000)
uv run main.py                    # Run the CLI forecast tool
uv add <package>                  # Add dependency
uv self update                    # Update uv itself
```

**Required**: Set `OPENWEATHER_API_KEY` environment variable before running.

## Key Patterns

### Web Application
- FastAPI with Jinja2 templates and Bootstrap 5
- Dark/light theme toggle via CSS custom properties (`data-bs-theme`) and localStorage
- Configuration saved to localStorage, passed as query parameters to server on reload
- `/api/config` endpoint returns server defaults for reset functionality
- All colors and typography use CSS custom properties (prefixed `--kom-`) for theming

### Wind Favorability Calculation
The scoring algorithm in `main.py` weights wind conditions: **30% direction alignment + 70% wind speed**. Direction uses cosine decay within tolerance. See `calculate_wind_alignment_score()` and `find_favorable_wind_conditions_for_a_segment()`.

### Forecast Caching
`get_wind_forecast.py` persists API responses to `forecast_cache.json`. Uncomment `reload_forecast()` call in `get_wind_forecast()` to test without API calls.

### Segment Data
KOM segments are stored in `kom-list.csv` with columns: `Segment name, Distance, Climb, Direction, KOM holder, KOM Time, Speed, My Rank, My Time, My Speed`. Segments where `my_rank == "1"` are skipped (already hold KOM).

### Cardinal Direction Conversion
`KOMSegment.get_direction_degrees()` and `degrees_to_cardinal()` handle 16-point compass conversions. Wind direction from API is "coming from" - converted to "going to" for alignment calculation.

## Configuration (`config.py`)

- `MIN_WIND_SPEED`: Minimum tailwind mph to consider (15.0 default)
- `DIRECTION_TOLERANCE`: Max degrees off perfect alignment (15° default)
- `QUALITY_PERCENTAGE`: Minimum favorability score to display (75% default)
- `LAT/LON`: Charlotte, MI coordinates (42.5702, -84.8352)

## External APIs

1. **OpenWeatherMap** (`/data/2.5/forecast`): 5-day/3-hour forecast, imperial units
2. **SunriseSunset.io**: Daylight hours per day - filters forecasts to rideable times

## Code Style

- Use type hints with `TypeAlias` for complex types (see `WindForecast` in `get_wind_forecast.py`)
- Dataclasses for structured data (`KOMSegment`)
- Explicit state passing, no globals
- Functions should be regenerable in isolation - avoid tight coupling
- All CSS colors and typography use CSS custom properties for theming
- Document all functions with docstrings
