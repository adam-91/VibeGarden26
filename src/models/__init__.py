from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Optional
from uuid import uuid4


@dataclass
class Location:
    id: Optional[int] = None
    name: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: str = "UTC"
    is_default: bool = False
    last_used: str = ""


@dataclass
class CalendarEvent:
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    category: str = "general"
    start_date: str = ""
    end_date: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    is_all_day: bool = False
    color: str = "#4CAF50"
    location_id: Optional[int] = None
    recurrence_type: str = "none"
    recurrence_interval: int = 1
    recurrence_end_date: Optional[str] = None
    reminder_enabled: bool = False
    reminder_value: int = 1
    reminder_unit: str = "day"
    created_at: str = ""


@dataclass
class WeatherData:
    temperature: float = 0.0
    humidity: int = 0
    weather_code: int = 0
    weather_description: str = ""
    wind_speed: float = 0.0
    wind_direction: float = 0.0
    wind_gusts: float = 0.0
    pressure: float = 0.0
    uv_index: float = 0.0
    sunrise: str = ""
    sunset: str = ""
    location_name: str = ""
    hourly_times: list[str] = field(default_factory=list)
    hourly_wind_speeds: list[float] = field(default_factory=list)
    hourly_wind_directions: list[float] = field(default_factory=list)
    hourly_wind_gusts: list[float] = field(default_factory=list)
    hourly_precipitation: list[float] = field(default_factory=list)
    hourly_temperatures: list[float] = field(default_factory=list)
    hourly_rain: list[float] = field(default_factory=list)
    hourly_snowfall: list[float] = field(default_factory=list)
    hourly_hail: list[float] = field(default_factory=list)
    hourly_weather_codes: list[int] = field(default_factory=list)
    daily_max_temp: float = 0.0
    daily_min_temp: float = 0.0
    daily_precip_sum: float = 0.0
    daily_max_wind_speed: float = 0.0
    daily_max_wind_gusts: float = 0.0
    timezone: str = ""


@dataclass
class MoonData:
    moon_phase: float = 0.0
    moon_phase_name: str = ""
    moon_phase_icon: str = "●"
    moonrise: str = ""
    moonset: str = ""
    date: str = ""


@dataclass
class GeocodingResult:
    name: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: str = "UTC"
    country: str = ""
    admin1: str = ""
