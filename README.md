# KOM-Forecast

Finds the most favorable day and time to attempt a Strava KOM. Shows the time and speed needed to take the KOM.

### Example Output

```
$ uv run main.py

5-day KOM Segment Forecast
Tuesday, November 04 2025 - Sunday, November 09 2025
[Config: winds 15.0+ mph, tolerance 30°, 70%+ favorability]


Climb From Creep Swamp 1.43 km E

  KOM  : Crank Burner 2:33 min 20.9 mph
  Me   : rank 3 2:38 min 20.2 mph
  Need : -0:05 min +0.7 mph

  Wednesday 2025-11-05 (07:19 AM - 05:28 PM)
  ☁️ | 10:00 AM |  56° | 19.9 mph from W   |  11° off |  95% favorable
  ☁️ | 01:00 PM |  56° | 23.8 mph from WNW |  27° off |  75% favorable

  Friday 2025-11-07 (07:22 AM - 05:26 PM)
  ☁️ | 01:00 PM |  57° | 16.4 mph from WSW |  15° off |  79% favorable


Kalamo to Battle Creek 12.97 km E

  KOM  : Sue Speedly 22:21 min 21.6 mph
  Me   : rank 99 24:20 min 19.9 mph
  Need : -1:59 min +1.8 mph

  Wednesday 2025-11-05 (07:19 AM - 05:28 PM)
  ☁️ | 10:00 AM |  56° | 19.9 mph from W   |  11° off |  95% favorable
  ☁️ | 01:00 PM |  56° | 23.8 mph from WNW |  27° off |  75% favorable

  Friday 2025-11-07 (07:22 AM - 05:26 PM)
  ☁️ | 01:00 PM |  57° | 16.4 mph from WSW |  15° off |  79% favorable

  ```

## Future work
- Currently uses a CSV file for KOM stats. Need to read data from Strava API.
- Scale wind angle contribution from 0° to 90°
- Turn this into a web page?

