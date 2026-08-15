from __future__ import annotations

import pytest
from pytest_httpx import HTTPXMock

from src.services.weather_service import WeatherService
from src.services.astronomy_service import AstronomyService
from src.services.geolocation_service import GeolocationService


_WEATHER_RESPONSE = {
    "latitude": 52.23,
    "longitude": 21.01,
    "current": {
        "temperature_2m": 22.5,
        "relative_humidity_2m": 65,
        "weather_code": 1,
        "wind_speed_10m": 12.3,
        "wind_direction_10m": 270.0,
        "wind_gusts_10m": 25.0,
        "surface_pressure": 1013.2,
        "uv_index": 4.5,
    },
    "daily": {
        "sunrise": ["2026-08-03T05:00"],
        "sunset": ["2026-08-03T20:30"],
    },
    "hourly": {
        "time": ["2026-08-03T00:00", "2026-08-03T01:00", "2026-08-03T02:00"],
        "wind_speed_10m": [5.0, 6.2, 7.1],
        "wind_direction_10m": [180.0, 190.0, 200.0],
        "wind_gusts_10m": [10.0, 12.0, 14.0],
        "precipitation": [0.0, 0.0, 1.2],
    },
}

_ASTRO_RESPONSE = {
    "daily": {
        "moon_phase": [0.75],
        "moonrise": ["2026-08-03T18:30"],
        "moonset": ["2026-08-03T04:15"],
        "time": ["2026-08-03"],
    },
}

_GEOCODING_RESPONSE = {
    "results": [
        {
            "name": "Warszawa",
            "latitude": 52.2297,
            "longitude": 21.0122,
            "timezone": "Europe/Warsaw",
            "country": "Polska",
            "admin1": "Mazowieckie",
        }
    ]
}


@pytest.mark.asyncio
async def test_weather_service(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=_WEATHER_RESPONSE)
    svc = WeatherService()
    result = await svc.fetch_current(52.2297, 21.0122, "Europe/Warsaw", "Warszawa")
    assert result is not None
    assert result.temperature == 22.5
    assert result.humidity == 65
    assert result.weather_description == "Przeważnie bezchmurnie"
    assert result.wind_speed == 12.3
    assert result.sunrise == "2026-08-03T05:00"
    assert result.sunset == "2026-08-03T20:30"
    assert result.wind_direction == 270.0
    assert result.wind_gusts == 25.0
    assert result.pressure == 1013.2
    assert result.uv_index == 4.5
    assert len(result.hourly_times) == 3
    assert result.hourly_precipitation == [0.0, 0.0, 1.2]


@pytest.mark.asyncio
async def test_weather_service_cache(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=_WEATHER_RESPONSE)
    svc = WeatherService()
    result1 = await svc.fetch_current(52.2297, 21.0122)
    result2 = await svc.fetch_current(52.2297, 21.0122)
    assert result2 is result1
    assert len(httpx_mock.get_requests()) == 1


@pytest.mark.asyncio
async def test_astronomy_service(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=_ASTRO_RESPONSE)
    svc = AstronomyService()
    result = await svc.fetch_moon_data(52.2297, 21.0122, "Europe/Warsaw")
    assert result is not None
    assert result.moonrise == "2026-08-03T18:30"
    assert result.moonset == "2026-08-03T04:15"
    assert result.moon_phase_icon == "🌗"


@pytest.mark.asyncio
async def test_geolocation_service(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json=_GEOCODING_RESPONSE)
    svc = GeolocationService()
    results = await svc.search("Warszawa")
    assert len(results) == 1
    assert results[0].name == "Warszawa, Mazowieckie, Polska"
    assert results[0].latitude == 52.2297
    assert results[0].longitude == 21.0122
