from __future__ import annotations

import pytest

from src.database.repositories import EventRepository, LocationRepository
from src.models import CalendarEvent, Location


def test_create_and_get_event(memory_db):
    repo = EventRepository()
    event = CalendarEvent(
        title="Testowe wydarzenie",
        description="Opis testowy",
        category="office",
        start_date="2026-08-15",
        color="#2196F3",
    )
    event_id = repo.create(event)
    assert event_id > 0

    fetched = repo.get_by_id(event_id)
    assert fetched is not None
    assert fetched.title == "Testowe wydarzenie"
    assert fetched.category == "office"
    assert fetched.color == "#2196F3"


def test_update_event(memory_db):
    repo = EventRepository()
    event = CalendarEvent(
        title="Przed edycją",
        category="general",
        start_date="2026-08-10",
    )
    event_id = repo.create(event)

    event.id = event_id
    event.title = "Po edycji"
    event.category = "garden"
    repo.update(event)

    updated = repo.get_by_id(event_id)
    assert updated.title == "Po edycji"
    assert updated.category == "garden"


def test_delete_event(memory_db):
    repo = EventRepository()
    event = CalendarEvent(title="Do usunięcia", start_date="2026-08-10")
    event_id = repo.create(event)

    repo.delete(event_id)
    assert repo.get_by_id(event_id) is None


def test_get_by_date_range(memory_db):
    repo = EventRepository()
    e1 = CalendarEvent(title="Event 1", start_date="2026-08-01")
    e2 = CalendarEvent(title="Event 2", start_date="2026-08-15")
    e3 = CalendarEvent(title="Event 3", start_date="2026-09-01")
    repo.create(e1)
    repo.create(e2)
    repo.create(e3)

    events = repo.get_by_date_range("2026-08-01", "2026-08-31")
    assert len(events) == 2
    titles = {e.title for e in events}
    assert titles == {"Event 1", "Event 2"}


def test_multi_day_event(memory_db):
    repo = EventRepository()
    event = CalendarEvent(
        title="Wydarzenie wielodniowe",
        start_date="2026-08-10",
        end_date="2026-08-15",
    )
    repo.create(event)

    events = repo.get_by_date("2026-08-12")
    assert len(events) == 1
    assert events[0].title == "Wydarzenie wielodniowe"


def test_location_upsert(memory_db):
    repo = LocationRepository()
    loc = Location(
        name="Warszawa", latitude=52.2297, longitude=21.0122, timezone="Europe/Warsaw"
    )
    loc_id = repo.upsert(loc)
    assert loc_id > 0

    loc2 = Location(
        name="Warszawa, PL", latitude=52.2297, longitude=21.0122, timezone="Europe/Warsaw"
    )
    loc_id2 = repo.upsert(loc2)
    assert loc_id == loc_id2

    all_locs = repo.get_all()
    assert len(all_locs) == 1
    assert all_locs[0].name == "Warszawa, PL"


def test_location_set_default(memory_db):
    repo = LocationRepository()
    loc1 = Location(name="A", latitude=1.0, longitude=1.0, timezone="UTC")
    loc2 = Location(name="B", latitude=2.0, longitude=2.0, timezone="UTC")
    id1 = repo.upsert(loc1)
    id2 = repo.upsert(loc2)
    repo.set_default(id1)
    assert repo.get_default().id == id1
    repo.set_default(id2)
    assert repo.get_default().id == id2
