from __future__ import annotations

import calendar as cal_module
from datetime import date, timedelta
from typing import Optional

from src.config.settings import DEFAULT_LOCATION, MOON_PHASE_NAMES
from src.database.repositories import EventRepository, LocationRepository
from src.models import CalendarEvent, Location, MoonData, WeatherData
from src.services import AstronomyService, GeolocationService, WeatherService


def _expand_recurring_event(event: CalendarEvent, range_start: date, range_end: date) -> list[tuple[str, CalendarEvent]]:
    instances: list[tuple[str, CalendarEvent]] = []
    start = date.fromisoformat(event.start_date)
    if event.end_date:
        duration_days = (date.fromisoformat(event.end_date) - start).days
    else:
        duration_days = 0

    limit_date = range_end
    if event.recurrence_end_date:
        limit_end = date.fromisoformat(event.recurrence_end_date)
        if limit_end < limit_date:
            limit_date = limit_end

    current = start
    while current <= limit_date:
        current_str = current.isoformat()
        if current <= range_end and (
            current >= range_start
            or (event.end_date and date.fromisoformat(event.end_date) >= range_start)
        ):
            ce = CalendarEvent(
                id=event.id,
                title=event.title,
                description=event.description,
                category=event.category,
                start_date=current_str,
                end_date=(
                    (current + timedelta(days=duration_days)).isoformat()
                    if duration_days > 0
                    else None
                ),
                start_time=event.start_time,
                end_time=event.end_time,
                is_all_day=event.is_all_day,
                color=event.color,
                recurrence_type=event.recurrence_type,
                recurrence_interval=event.recurrence_interval,
                recurrence_end_date=event.recurrence_end_date,
                reminder_enabled=event.reminder_enabled,
                reminder_value=event.reminder_value,
                reminder_unit=event.reminder_unit,
            )
            instances.append((current_str, ce))

        if event.recurrence_type == "daily":
            current += timedelta(days=event.recurrence_interval)
        elif event.recurrence_type == "weekly":
            current += timedelta(weeks=event.recurrence_interval)
        elif event.recurrence_type == "monthly":
            for _ in range(event.recurrence_interval):
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
        elif event.recurrence_type == "yearly":
            current = current.replace(year=current.year + event.recurrence_interval)
        else:
            break

    return instances


class CalendarModel:
    MAX_WEEKS = 6

    def __init__(self) -> None:
        self._selected_date: date = date.today()
        self._events: dict[str, list[CalendarEvent]] = {}
        self._event_repository = EventRepository()
        self._weather: Optional[WeatherData] = None
        self._moon: Optional[MoonData] = None
        self._moon_phase_days: dict[int, float] = {}
        self._today: date = date.today()
        self._lat: Optional[float] = None
        self._lon: Optional[float] = None
        self._tz: str = "Europe/Warsaw"

    @property
    def selected_date(self) -> date:
        return self._selected_date

    @selected_date.setter
    def selected_date(self, value: date) -> None:
        self._selected_date = value

    @property
    def today(self) -> date:
        return self._today

    @property
    def year(self) -> int:
        return self._selected_date.year

    @property
    def month(self) -> int:
        return self._selected_date.month

    @property
    def weather(self) -> Optional[WeatherData]:
        return self._weather

    @property
    def moon(self) -> Optional[MoonData]:
        return self._moon

    def go_to_prev_month(self) -> None:
        if self._selected_date.month == 1:
            self._selected_date = self._selected_date.replace(
                year=self._selected_date.year - 1, month=12
            )
        else:
            self._selected_date = self._selected_date.replace(
                month=self._selected_date.month - 1
            )
        self._refresh_moon_phases_sync()

    def go_to_next_month(self) -> None:
        if self._selected_date.month == 12:
            self._selected_date = self._selected_date.replace(
                year=self._selected_date.year + 1, month=1
            )
        else:
            self._selected_date = self._selected_date.replace(
                month=self._selected_date.month + 1
            )
        self._refresh_moon_phases_sync()

    def go_to_today(self) -> None:
        self._selected_date = date.today()
        self._today = date.today()
        self._refresh_moon_phases_sync()

    def get_calendar_days(self) -> list[Optional[date]]:
        first_day = date(self.year, self.month, 1)
        _, last_day_num = cal_module.monthrange(self.year, self.month)
        last_day = date(self.year, self.month, last_day_num)

        start_padding = first_day.weekday()
        days: list[Optional[date]] = [None] * start_padding

        for day_num in range(1, last_day_num + 1):
            days.append(date(self.year, self.month, day_num))

        remaining = self.MAX_WEEKS * 7 - len(days)
        days.extend([None] * remaining)

        return days

    def load_events(self) -> None:
        _, last_day = cal_module.monthrange(self.year, self.month)
        start_str = f"{self.year}-{self.month:02d}-01"
        end_str = f"{self.year}-{self.month:02d}-{last_day:02d}"

        range_start = date(self.year, self.month, 1)
        range_end = date(self.year, self.month, last_day)

        events = self._event_repository.get_by_date_range(start_str, end_str)
        recurring_events = self._event_repository.get_recurring()

        self._events.clear()
        for event in events:
            if event.recurrence_type != "none":
                continue
            self._events.setdefault(event.start_date, []).append(event)

        for rec_event in recurring_events:
            instances = _expand_recurring_event(rec_event, range_start, range_end)
            for date_str, instance in instances:
                self._events.setdefault(date_str, []).append(instance)

    def get_events_for_date(self, dt: date) -> list[CalendarEvent]:
        return self._events.get(dt.isoformat(), [])

    def event_count_for_date(self, dt: date) -> int:
        return len(self.get_events_for_date(dt))

    def add_event(self, event: CalendarEvent) -> int:
        event_id = self._event_repository.create(event)
        self.load_events()
        return event_id

    def update_event(self, event: CalendarEvent) -> None:
        self._event_repository.update(event)
        self.load_events()

    def delete_event(self, event_id: int) -> None:
        self._event_repository.delete(event_id)
        self.load_events()

    def is_full_moon_day(self, dt: date) -> bool:
        phase = self._moon_phase_days.get(dt.day)
        if phase is None:
            return False
        idx = int(round((phase % 1) * 8)) % 8
        return idx == 4

    async def refresh_weather_and_moon(
        self, latitude: float, longitude: float,
        timezone: str = "Europe/Warsaw", location_name: str = ""
    ) -> None:
        try:
            self._lat = latitude
            self._lon = longitude
            self._tz = timezone
            weather_svc = WeatherService()
            astronomy_svc = AstronomyService()
            self._weather = await weather_svc.fetch_current(
                latitude, longitude, timezone, location_name
            )
            self._moon = await astronomy_svc.fetch_moon_data(
                latitude, longitude, timezone
            )
            self._moon_phase_days = await astronomy_svc.fetch_month_moon_phases(
                latitude, longitude,
                self._selected_date.year, self._selected_date.month,
                timezone,
            )
        except ConnectionError:
            self._weather = None
            self._moon = None
            self._moon_phase_days.clear()

    def _refresh_moon_phases_sync(self) -> None:
        if self._lat is None or self._lon is None:
            return
        import asyncio
        try:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            else:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            svc = AstronomyService()
            self._moon_phase_days = loop.run_until_complete(
                svc.fetch_month_moon_phases(
                    self._lat, self._lon,
                    self._selected_date.year, self._selected_date.month,
                    self._tz,
                )
            )
        except Exception:
            pass
