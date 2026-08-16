from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "VibeGarden26"
APP_VERSION = "0.1.0"

DATA_DIR = Path.home() / f".{APP_NAME.lower()}"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = DATA_DIR / "vibegarden.db"

OPEN_METEO_WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
OPEN_METEO_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

WEATHER_CACHE_SECONDS = 1800
MOON_PHASE_NAMES = {
    0: "Nów",
    1: "Sierp przybywający",
    2: "Pierwsza kwadra",
    3: "Księżyc garbaty przybywający",
    4: "Pełnia",
    5: "Księżyc garbaty ubywający",
    6: "Trzecia kwadra",
    7: "Sierp ubywający",
}

WEATHER_CODES: dict[int, str] = {
    0: "Czyste niebo",
    1: "Przeważnie bezchmurnie",
    2: "Częściowe zachmurzenie",
    3: "Pochmurno",
    45: "Mgła",
    48: "Szadź",
    51: "Lekka mżawka",
    53: "Umiarkowana mżawka",
    55: "Gęsta mżawka",
    56: "Marznąca mżawka",
    57: "Marznąca gęsta mżawka",
    61: "Lekki deszcz",
    63: "Umiarkowany deszcz",
    65: "Intensywny deszcz",
    66: "Marznący deszcz",
    67: "Marznący intensywny deszcz",
    71: "Lekki śnieg",
    73: "Umiarkowany śnieg",
    75: "Intensywny śnieg",
    77: "Ziarna śnieżne",
    80: "Lekkie przelotne opady",
    81: "Umiarkowane przelotne opady",
    82: "Gwałtowne przelotne opady",
    85: "Lekkie opady śniegu",
    86: "Intensywne opady śniegu",
    95: "Burza",
    96: "Burza z lekkim gradem",
    99: "Burza z intensywnym gradem",
}

DEFAULT_LOCATION = {
    "name": "Warszawa",
    "latitude": 52.2297,
    "longitude": 21.0122,
    "timezone": "Europe/Warsaw",
}

CATEGORY_COLORS = {
    "general": "#4CAF50",
    "office": "#2196F3",
    "garden": "#FF9800",
}

ALERT_COLORS = {
    "yellow": "#FFC107",
    "orange": "#FF9800",
    "red": "#F44336",
}

ALERT_TEXT_COLORS = {
    "yellow": "#1a1a1a",
    "orange": "#ffffff",
    "red": "#ffffff",
}

ALERT_WIND_THRESHOLDS = {"yellow": 72, "orange": 90, "red": 115}
ALERT_FROST_THRESHOLDS = {"yellow": -15, "orange": -18, "red": -22}
ALERT_FLOOD_THRESHOLDS = {"yellow": 30, "orange": 50, "red": 80}
ALERT_DROUGHT_THRESHOLDS = {"yellow": 10, "orange": 18, "red": 26}

DROUGHT_WINDOW_DAYS = 14
DROUGHT_MIN_DRY_DAYS = 8
