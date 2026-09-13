from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon, QPixmap

MOON_PHASE_ICONS: dict[int, str] = {
    0: "none_moon.png",
    1: "moon_croissant.png",
    2: "moon_croissant.png",
    3: "full_moon.png",
    4: "full_moon.png",
    5: "full_moon.png",
    6: "moon_croissant.png",
    7: "moon_croissant.png",
}


def _resources_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "resources"
    return Path(__file__).parent.parent.parent / "resources"


ICONS_DIR = _resources_dir() / "icons"


def icon_path(name: str) -> str:
    return str(ICONS_DIR / name)


def app_icon() -> QIcon:
    return QIcon(icon_path("app.png"))


def weather_icon(code: int) -> str:
    if code in (0, 1):
        return "sun.png"
    if code == 2:
        return "sun_cloud.png"
    if code == 3:
        return "cloud.png"
    if code in (45, 48):
        return "fog.png"
    if 51 <= code <= 57:
        return "rain.png"
    if 61 <= code <= 65:
        return "rain.png"
    if code in (66, 67):
        return "snow_and_rain.png"
    if 71 <= code <= 77:
        return "snow.png"
    if code in (80, 81):
        return "sun_rain.png"
    if code == 82:
        return "rain.png"
    if code in (85, 86):
        return "snow.png"
    if code >= 95:
        return "thunder_storm.png"
    return "sun.png"


_pixmap_cache: dict[tuple[str, int], QPixmap] = {}


def load_icon_pixmap(name: str, size: int) -> QPixmap:
    key = (name, size)
    cached = _pixmap_cache.get(key)
    if cached is not None:
        return cached
    pixmap = QPixmap(icon_path(name))
    if pixmap.isNull():
        pixmap = QPixmap(icon_path("sun.png"))
    pixmap = pixmap.scaled(
        QSize(size, size),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    _pixmap_cache[key] = pixmap
    return pixmap
