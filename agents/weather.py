"""
WeatherAgent — Open-Meteo (free, no API key required).
Geocoding: Open-Meteo geocoding API (also free).
"""
import asyncio
import logging
from datetime import datetime

import requests

from agents.base import BaseAgent
from core.config import env
from core.memory import Memory

log = logging.getLogger("jarvis.weather")
mem = Memory()

GEO_URL     = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

WMO_CODES = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog",
    51: "Light drizzle", 53: "Drizzle", 55: "Heavy drizzle",
    61: "Light rain", 63: "Rain", 65: "Heavy rain",
    71: "Light snow", 73: "Snow", 75: "Heavy snow",
    80: "Rain showers", 81: "Rain showers", 82: "Violent rain showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


def _geocode(city: str) -> tuple[float, float, str]:
    """Returns (lat, lon, resolved_name)."""
    cached = mem.get_fact(f"geo_{city}")
    if cached:
        return cached["lat"], cached["lon"], cached["name"]
    r = requests.get(GEO_URL, params={"name": city, "count": 1, "language": "en"}, timeout=8)
    r.raise_for_status()
    results = r.json().get("results")
    if not results:
        raise ValueError(f"City not found: {city}")
    loc = results[0]
    lat, lon, name = loc["latitude"], loc["longitude"], f"{loc['name']}, {loc.get('country','')}"
    mem.set_fact(f"geo_{city}", {"lat": lat, "lon": lon, "name": name})
    return lat, lon, name


def _fetch_current(city: str, units: str) -> dict:
    lat, lon, name = _geocode(city)
    temp_unit = "fahrenheit" if units == "imperial" else "celsius"
    wind_unit = "mph" if units == "imperial" else "kmh"

    r = requests.get(WEATHER_URL, params={
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,apparent_temperature,weather_code,relative_humidity_2m,wind_speed_10m,precipitation",
        "temperature_unit": temp_unit,
        "wind_speed_unit": wind_unit,
        "timezone": "auto",
    }, timeout=8)
    r.raise_for_status()
    c = r.json()["current"]
    result = {
        "city": name,
        "temp": round(c["temperature_2m"], 1),
        "feels_like": round(c["apparent_temperature"], 1),
        "condition": WMO_CODES.get(c["weather_code"], "Unknown"),
        "humidity": c["relative_humidity_2m"],
        "wind": round(c["wind_speed_10m"], 1),
        "precipitation": c["precipitation"],
        "units": units,
    }
    mem.set_fact("weather_current", result)
    return result


def _fetch_forecast(city: str, units: str) -> dict:
    lat, lon, name = _geocode(city)
    temp_unit = "fahrenheit" if units == "imperial" else "celsius"

    r = requests.get(WEATHER_URL, params={
        "latitude": lat, "longitude": lon,
        "hourly": "temperature_2m,weather_code,precipitation_probability",
        "forecast_days": 3,
        "temperature_unit": temp_unit,
        "timezone": "auto",
    }, timeout=8)
    r.raise_for_status()
    h = r.json()["hourly"]
    forecast = []
    for i in range(0, 24, 6):  # every 6 hours for 3 days
        forecast.append({
            "time": h["time"][i],
            "temp": round(h["temperature_2m"][i], 1),
            "condition": WMO_CODES.get(h["weather_code"][i], "Unknown"),
            "rain_chance": h["precipitation_probability"][i],
        })
    return {"city": name, "forecast": forecast}


class WeatherAgent(BaseAgent):
    name = "weather"

    def tools(self):
        return [
            self._tool(
                "get_current",
                "Get current weather conditions. No API key needed.",
                {"city": {"type": "string", "description": "City name (uses user default if omitted)"}},
            ),
            self._tool(
                "get_forecast",
                "Get 3-day weather forecast.",
                {"city": {"type": "string"}},
            ),
        ]

    async def execute(self, method: str, params: dict):
        city  = params.get("city") or env("WEATHER_CITY", "New York")
        units = env("WEATHER_UNITS", "imperial")
        if method == "get_current":
            return await asyncio.to_thread(_fetch_current, city, units)
        if method == "get_forecast":
            return await asyncio.to_thread(_fetch_forecast, city, units)
        return {"error": f"Unknown method: {method}"}

    async def tick(self):
        city  = env("WEATHER_CITY", "New York")
        units = env("WEATHER_UNITS", "imperial")
        try:
            data = await asyncio.to_thread(_fetch_current, city, units)
            cond = data.get("condition", "").lower()
            severe = any(w in cond for w in ["thunderstorm", "tornado", "blizzard", "hurricane", "heavy rain"])
            if severe:
                from core.bus import bus
                await bus.publish("jarvis.alert", {
                    "source": "weather",
                    "message": f"Severe weather alert: {data['condition']} in {data['city']}.",
                })
        except Exception as e:
            log.warning(f"Weather tick: {e}")
