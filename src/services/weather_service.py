from __future__ import annotations

from typing import Optional

import httpx

from src.config.settings import OPEN_METEO_WEATHER_URL, WEATHER_CACHE_SECONDS, WEATHER_CODES
from src.models import WeatherData


class WeatherService:
    def __init__(self) -> None:
        self._cache: dict[str, tuple[float, WeatherData]] = {}

    async def fetch_current(
        self, latitude: float, longitude: float, timezone: str = "auto",
        location_name: str = ""
    ) -> Optional[WeatherData]:
        import time
        cache_key = f"{latitude:.4f}_{longitude:.4f}"
        cached = self._cache.get(cache_key)
        if cached and time.monotonic() - cached[0] < WEATHER_CACHE_SECONDS:
            return cached[1]

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,relative_humidity_2m,weather_code,"
                "wind_speed_10m,wind_direction_10m,wind_gusts_10m,"
                "surface_pressure,uv_index"
            ),
            "daily": "sunrise,sunset",
            "hourly": (
                "wind_speed_10m,wind_direction_10m,wind_gusts_10m,precipitation"
            ),
            "timezone": timezone,
            "forecast_days": 1,
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    OPEN_METEO_WEATHER_URL, params=params, timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError as exc:
                raise ConnectionError(f"Weather API error: {exc}") from exc

        current = data.get("current", {})
        daily = data.get("daily", {})
        hourly = data.get("hourly", {})

        weather = WeatherData(
            temperature=current.get("temperature_2m", 0.0),
            humidity=current.get("relative_humidity_2m", 0),
            weather_code=current.get("weather_code", 0),
            weather_description=WEATHER_CODES.get(
                current.get("weather_code", 0), "Nieznane"
            ),
            wind_speed=current.get("wind_speed_10m", 0.0),
            wind_direction=current.get("wind_direction_10m", 0.0),
            wind_gusts=current.get("wind_gusts_10m", 0.0),
            pressure=current.get("surface_pressure", 0.0),
            uv_index=current.get("uv_index", 0.0),
            sunrise=str(daily.get("sunrise", [""])[0]) if daily.get("sunrise") else "",
            sunset=str(daily.get("sunset", [""])[0]) if daily.get("sunset") else "",
            location_name=location_name,
            hourly_times=hourly.get("time", []),
            hourly_wind_speeds=hourly.get("wind_speed_10m", []),
            hourly_wind_directions=hourly.get("wind_direction_10m", []),
            hourly_wind_gusts=hourly.get("wind_gusts_10m", []),
            hourly_precipitation=hourly.get("precipitation", []),
        )
        self._cache[cache_key] = (time.monotonic(), weather)
        return weather
