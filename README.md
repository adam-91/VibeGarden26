# VibeGarden26

Biurowo-ogrodniczy kalendarz z pogodą i fazami księżyca — a desktop calendar for office and garden work, with live weather and moon phases.

Built with Python and Qt (PySide6), VibeGarden26 combines a monthly calendar with weather forecasts, moon phase information, and location management in a single window. The UI is in Polish.

## Features

- **Monthly calendar** with a daily event list for the selected day
- **Events** — all-day, timed, and multi-day events with descriptions
- **Recurring events** — daily, weekly, monthly, and yearly repetition with custom intervals and end dates
- **Reminders** — day-before, hour-before, or custom (minutes)
- **Categories & colors** — general, office, and garden categories with distinct colors
- **Weather panel** — current conditions (temperature, humidity, pressure, UV index, sunrise/sunset), wind (speed, direction, gusts) with a 24h chart, and precipitation chart
- **Moon phase panel** — current phase, moonrise/moonset, and full-moon markers on the calendar
- **Location management** — city search (geocoding), saved locations, and a timezone-aware clock
- **Local storage** — events and locations persisted in SQLite

## Tech stack

- **Python** ≥ 3.13
- **PySide6** (Qt 6) — GUI
- **httpx** — asynchronous HTTP client
- **pytz** — timezone handling
- **SQLite** — local database
- **Open-Meteo API** — weather, astronomy, and geocoding data

## Project structure

```
dayApp/
├── src/
│   ├── main.py                     # Entry point
│   ├── app/
│   │   └── application.py          # Application bootstrap, styling
│   ├── config/
│   │   └── settings.py             # Constants, weather codes, defaults
│   ├── database/
│   │   ├── connection.py           # SQLite connection (singleton)
│   │   ├── schema.py               # Schema and migrations
│   │   └── repositories/           # Event and location repositories
│   ├── models/                     # Dataclasses (Event, Location, Weather, Moon…)
│   ├── services/                   # Weather, astronomy, geolocation services
│   └── ui/
│       ├── main_window.py          # Main window and layout
│       ├── calendar/               # Calendar grid, model, event editor
│       ├── sidebar/                # Location panel
│       ├── weather/                # Weather panel and charts
│       └── astronomy/              # Moon panel
├── tests/                          # pytest suite
├── resources/
│   ├── styles/main.qss             # Qt stylesheet
│   └── icons/                      # App icon
├── scripts/
│   ├── build_exe.py                # PyInstaller build
│   └── build_appimage.sh           # AppImage build
├── docker/                         # Dockerfile and compose configuration
├── pyproject.toml
└── requirements.txt
```

## Requirements

- Python 3.13 or newer

## Installation

```bash
git clone <repository-url>
cd dayApp
pip install -r requirements.txt
```

For development (including test dependencies):

```bash
pip install -e ".[dev]"
```

## Running

```bash
python src/main.py
```

## Running in Docker

A Docker setup is provided for GUI (X11) and headless test environments.

```bash
./docker/run.sh
```

This builds and runs the `dev` service, forwarding the X11 display. Alternatively, run it directly:

```bash
docker compose -f docker/docker-compose.yml up --build dev
```

Run the test suite inside Docker:

```bash
docker compose -f docker/docker-compose.yml --profile test up
```

## Building executables

Build a standalone binary with PyInstaller:

```bash
python scripts/build_exe.py
```

Build an AppImage (Linux):

```bash
./scripts/build_appimage.sh
```

## Testing

```bash
pytest tests/ -v
```

## Data location

Events and locations are stored in a local SQLite database at:

```
~/.vibegarden26/vibegarden.db
```
