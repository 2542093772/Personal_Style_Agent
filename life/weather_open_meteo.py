import json
import urllib.parse
import urllib.request


def _get_json(url: str):
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_today_weather(location: str):
    location = (location or "").strip()
    if not location:
        return None

    geo_q = urllib.parse.urlencode({
        "name": location,
        "count": 1,
        "language": "zh",
        "format": "json",
    })
    geo = _get_json(f"https://geocoding-api.open-meteo.com/v1/search?{geo_q}")
    results = geo.get("results") or []
    if not results:
        return {"ok": False, "location": location, "error": "location_not_found"}

    place = results[0]
    lat = place["latitude"]
    lon = place["longitude"]

    forecast_q = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "timezone": "auto",
        "current": "temperature_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "forecast_days": 1,
    })
    wx = _get_json(f"https://api.open-meteo.com/v1/forecast?{forecast_q}")

    current = wx.get("current", {})
    daily = wx.get("daily", {})

    return {
        "ok": True,
        "location": place.get("name", location),
        "admin1": place.get("admin1"),
        "country": place.get("country"),
        "temperature_c": current.get("temperature_2m"),
        "apparent_temperature_c": current.get("apparent_temperature"),
        "precipitation_mm": current.get("precipitation"),
        "wind_kmh": current.get("wind_speed_10m"),
        "weather_code": current.get("weather_code"),
        "temp_max_c": (daily.get("temperature_2m_max") or [None])[0],
        "temp_min_c": (daily.get("temperature_2m_min") or [None])[0],
        "precipitation_probability_max": (daily.get("precipitation_probability_max") or [None])[0],
    }


def get_today_weather_by_coordinates(latitude, longitude, location="", admin1=None, country="中国"):
    forecast_q = urllib.parse.urlencode({
        "latitude": latitude,
        "longitude": longitude,
        "timezone": "auto",
        "current": "temperature_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
        "forecast_days": 1,
    })
    wx = _get_json(f"https://api.open-meteo.com/v1/forecast?{forecast_q}")

    current = wx.get("current", {})
    daily = wx.get("daily", {})

    return {
        "ok": True,
        "location": location or "",
        "admin1": admin1,
        "country": country,
        "latitude": latitude,
        "longitude": longitude,
        "temperature_c": current.get("temperature_2m"),
        "apparent_temperature_c": current.get("apparent_temperature"),
        "precipitation_mm": current.get("precipitation"),
        "wind_kmh": current.get("wind_speed_10m"),
        "weather_code": current.get("weather_code"),
        "temp_max_c": (daily.get("temperature_2m_max") or [None])[0],
        "temp_min_c": (daily.get("temperature_2m_min") or [None])[0],
        "precipitation_probability_max": (daily.get("precipitation_probability_max") or [None])[0],
    }
