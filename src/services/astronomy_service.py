from __future__ import annotations

from typing import Optional

import httpx

from src.config.settings import MOON_PHASE_NAMES, OPEN_METEO_WEATHER_URL
from src.models import MoonData


class AstronomyService:
    MOON_PHASE_ICONS = {
        0: "🌑", 1: "🌒", 2: "🌓", 3: "🌔",
        4: "🌕", 5: "🌖", 6: "🌗", 7: "🌘",
    }

    async def fetch_moon_data(
        self, latitude: float, longitude: float,
        timezone: str = "auto"
    ) -> Optional[MoonData]:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "moon_phase,moonrise,moonset",
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
                raise ConnectionError(f"Astronomy API error: {exc}") from exc

        daily = data.get("daily", {})
        moon_phase_raw = (daily.get("moon_phase") or [0.0])[0]
        phase_index = int(round((moon_phase_raw % 1) * 8)) % 8

        moonrise_raw = daily.get("moonrise")
        moonset_raw = daily.get("moonset")
        moonrise = str(moonrise_raw[0]) if moonrise_raw else ""
        moonset = str(moonset_raw[0]) if moonset_raw else ""
        date_val = str(daily.get("time", [""])[0]) if daily.get("time") else ""

        return MoonData(
            moon_phase=moon_phase_raw,
            moon_phase_name=MOON_PHASE_NAMES[phase_index],
            moon_phase_icon=self.MOON_PHASE_ICONS[phase_index],
            moonrise=moonrise,
            moonset=moonset,
            date=date_val,
        )

    async def fetch_month_moon_phases(
        self, latitude: float, longitude: float,
        year: int, month: int, timezone: str = "auto"
    ) -> dict[int, float]:
        import calendar
        _, last_day = calendar.monthrange(year, month)

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "moon_phase",
            "timezone": timezone,
            "forecast_days": 16,
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    OPEN_METEO_WEATHER_URL, params=params, timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPError as exc:
                raise ConnectionError(f"Moon phase API error: {exc}") from exc

        phases: dict[int, float] = {}
        daily = data.get("daily", {})
        times = daily.get("time", [])
        raw_phases = daily.get("moon_phase", [])
        for time_str, phase in zip(times, raw_phases):
            from datetime import date
            try:
                d = date.fromisoformat(time_str)
                if d.month == month and d.year == year:
                    phases[d.day] = phase
            except (ValueError, TypeError):
                pass
        return phases
