from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from src.models import WeatherAlert, WeatherData
from src.services.alert_service import AlertService
from src.services.weather_service import WeatherService


def _weather(**kwargs) -> WeatherData:
    defaults = {
        "hourly_weather_codes": [],
        "daily_min_temp": 10.0,
        "daily_max_wind_gusts": 20.0,
        "daily_precip_sum": 0.0,
    }
    defaults.update(kwargs)
    return WeatherData(**defaults)


def _history(max_temps, precip_sums):
    n = len(max_temps)
    times = [f"2026-08-{i + 1:02d}" for i in range(n)]
    return times, list(max_temps), list(precip_sums)


class TestGenerate:
    def test_storm_yellow(self):
        alerts = AlertService().generate(_weather(hourly_weather_codes=[0, 95]))
        assert alerts[0].kind == "storm"
        assert alerts[0].category == "yellow"

    def test_storm_orange(self):
        alerts = AlertService().generate(_weather(hourly_weather_codes=[96]))
        assert alerts[0].category == "orange"

    def test_storm_red(self):
        alerts = AlertService().generate(_weather(hourly_weather_codes=[99]))
        assert alerts[0].category == "red"

    def test_frost_levels(self):
        assert AlertService().generate(_weather(daily_min_temp=-15))[0].category == "yellow"
        assert AlertService().generate(_weather(daily_min_temp=-18))[0].category == "orange"
        assert AlertService().generate(_weather(daily_min_temp=-22))[0].category == "red"
        assert AlertService().generate(_weather(daily_min_temp=-5)) == []

    def test_wind_levels(self):
        assert AlertService().generate(_weather(daily_max_wind_gusts=72))[0].category == "yellow"
        assert AlertService().generate(_weather(daily_max_wind_gusts=90))[0].category == "orange"
        assert AlertService().generate(_weather(daily_max_wind_gusts=115))[0].category == "red"
        assert AlertService().generate(_weather(daily_max_wind_gusts=50)) == []

    def test_flood_levels(self):
        assert AlertService().generate(_weather(daily_precip_sum=30))[0].category == "yellow"
        assert AlertService().generate(_weather(daily_precip_sum=50))[0].category == "orange"
        assert AlertService().generate(_weather(daily_precip_sum=80))[0].category == "red"
        assert AlertService().generate(_weather(daily_precip_sum=10)) == []

    def test_generate_sorts_most_severe_first(self):
        alerts = AlertService().generate(
            _weather(daily_min_temp=-15, daily_max_wind_gusts=115)
        )
        assert alerts[0].category == "red"


class TestDrought:
    def test_red_all_dry_hot(self):
        alert = AlertService.drought_alert(*_history([30.0] * 14, [0.0] * 14))
        assert alert is not None
        assert alert.category == "red"
        assert alert.kind == "drought"
        assert "14" in alert.text

    def test_yellow_heat_sum(self):
        max_temps = [30.0, 30.0] + [24.0] * 12
        alert = AlertService.drought_alert(*_history(max_temps, [0.0] * 14))
        assert alert is not None
        assert alert.category == "yellow"

    def test_orange_heat_sum(self):
        max_temps = [31.0] * 3 + [24.0] * 11
        alert = AlertService.drought_alert(*_history(max_temps, [0.0] * 14))
        assert alert is not None
        assert alert.category == "orange"

    def test_recent_rain_blocks_alert(self):
        precip = [0.0] * 13 + [5.0]
        alert = AlertService.drought_alert(*_history([30.0] * 14, precip))
        assert alert is None

    def test_significant_rain_zeroes_contribution(self):
        precip = [5.0] + [0.0] * 13
        alert = AlertService.drought_alert(*_history([40.0] + [24.0] * 13, precip))
        assert alert is None

    def test_small_rain_counts_as_dry(self):
        max_temps = [30.0, 30.0] + [24.0] * 12
        precip = [0.0] * 12 + [0.5, 0.5]
        alert = AlertService.drought_alert(*_history(max_temps, precip))
        assert alert is not None
        assert alert.category == "yellow"

    def test_negative_contributions_skipped(self):
        max_temps = [24.0] * 14
        alert = AlertService.drought_alert(*_history(max_temps, [0.0] * 14))
        assert alert is None

    def test_insufficient_days(self):
        alert = AlertService.drought_alert(*_history([30.0] * 5, [0.0] * 5))
        assert alert is None


_Daily_HISTORY_RESPONSE = {
    "daily": {
        "time": [f"2026-08-{i + 1:02d}" for i in range(14)],
        "temperature_2m_max": [24.0] * 14,
        "precipitation_sum": [0.0] * 14,
    }
}


@pytest.mark.asyncio
async def test_fetch_daily_history(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=_Daily_HISTORY_RESPONSE)
    svc = WeatherService()
    times, max_temps, precip_sums = await svc.fetch_daily_history(
        52.2297, 21.0122, "Europe/Warsaw"
    )
    assert len(times) == 14
    assert len(max_temps) == 14
    assert len(precip_sums) == 14
