from __future__ import annotations

from typing import Optional

from src.config.settings import (
    ALERT_DROUGHT_THRESHOLDS,
    ALERT_FLOOD_THRESHOLDS,
    ALERT_FROST_THRESHOLDS,
    ALERT_WIND_THRESHOLDS,
    DROUGHT_MIN_DRY_DAYS,
    DROUGHT_WINDOW_DAYS,
)
from src.models import WeatherAlert, WeatherData


def _severity_for(thresholds: dict[str, float], value: float) -> Optional[str]:
    if value >= thresholds.get("red", float("inf")):
        return "red"
    if value >= thresholds.get("orange", float("inf")):
        return "orange"
    if value >= thresholds.get("yellow", float("inf")):
        return "yellow"
    return None


def _severity_below(thresholds: dict[str, float], value: float) -> Optional[str]:
    if value <= thresholds.get("red", float("-inf")):
        return "red"
    if value <= thresholds.get("orange", float("inf")):
        return "orange"
    if value <= thresholds.get("yellow", float("inf")):
        return "yellow"
    return None


class AlertService:
    STORM_CODES = {
        95: ("yellow", "Burza"),
        96: ("orange", "Burza z gradem"),
        99: ("red", "Burza z intensywnym gradem"),
    }

    def generate(self, weather: Optional[WeatherData]) -> list[WeatherAlert]:
        if weather is None:
            return []
        alerts: list[WeatherAlert] = []
        alerts.extend(self._storm_alerts(weather))
        alerts.extend(self._frost_alerts(weather))
        alerts.extend(self._wind_alerts(weather))
        alerts.extend(self._flood_alerts(weather))
        alerts.sort(key=lambda a: a.severity, reverse=True)
        return alerts

    def _storm_alerts(self, weather: WeatherData) -> list[WeatherAlert]:
        codes = set(weather.hourly_weather_codes)
        for code in (99, 96, 95):
            if code in codes:
                category, text = self.STORM_CODES[code]
                return [WeatherAlert(category=category, kind="storm", text=text)]
        return []

    def _frost_alerts(self, weather: WeatherData) -> list[WeatherAlert]:
        tmin = weather.daily_min_temp
        category = _severity_below(ALERT_FROST_THRESHOLDS, tmin)
        if category is None:
            return []
        return [WeatherAlert(category=category, kind="frost", text=f"Mr\u00F3z (min {tmin:.0f}\u00B0C)")]

    def _wind_alerts(self, weather: WeatherData) -> list[WeatherAlert]:
        gusts = weather.daily_max_wind_gusts
        category = _severity_for(ALERT_WIND_THRESHOLDS, gusts)
        if category is None:
            return []
        return [WeatherAlert(category=category, kind="wind", text=f"Silny wiatr (porywy {gusts:.0f} km/h)")]

    def _flood_alerts(self, weather: WeatherData) -> list[WeatherAlert]:
        precip = weather.daily_precip_sum
        category = _severity_for(ALERT_FLOOD_THRESHOLDS, precip)
        if category is None:
            return []
        return [WeatherAlert(category=category, kind="flood", text=f"Intensywne opady (doba {precip:.0f} mm)")]

    @classmethod
    def drought_alert(
        cls,
        times: list[str],
        max_temps: list[float],
        precip_sums: list[float],
    ) -> Optional[WeatherAlert]:
        n = min(len(times), len(max_temps), len(precip_sums))
        if n < DROUGHT_WINDOW_DAYS:
            return None

        heat_sum = 0.0
        no_rain_days = 0
        days_since_rain = DROUGHT_WINDOW_DAYS

        for i in range(n):
            precip = precip_sums[i] if i < len(precip_sums) else 0.0
            tmax = max_temps[i] if i < len(max_temps) else 0.0
            if precip > 1.0:
                heat_sum_contribution = 0.0
                days_since_rain = n - 1 - i
            else:
                if precip == 0.0:
                    no_rain_days += 1
                heat_sum_contribution = max(0.0, tmax - 24.0)
            heat_sum += heat_sum_contribution

        if days_since_rain < DROUGHT_MIN_DRY_DAYS:
            return None

        category: Optional[str] = None
        if heat_sum > ALERT_DROUGHT_THRESHOLDS.get("red", float("inf")):
            category = "red"
        elif heat_sum > ALERT_DROUGHT_THRESHOLDS.get("orange", float("inf")):
            category = "orange"
        elif heat_sum > ALERT_DROUGHT_THRESHOLDS.get("yellow", float("inf")):
            category = "yellow"

        if category is None:
            return None

        return WeatherAlert(
            category=category,
            kind="drought",
            text=f"Susza \u2014 {no_rain_days} dni bez deszczu",
        )
