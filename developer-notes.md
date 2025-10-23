# Developer notes for segment-notifier

uv self update
uv init segment-notifier
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


