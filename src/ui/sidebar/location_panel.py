from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytz
from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.config.settings import DEFAULT_LOCATION
from src.database.repositories import LocationRepository
from src.models import GeocodingResult, Location
from src.services.geolocation_service import GeolocationService


class LocationPanel(QWidget):
    location_changed = Signal(float, float, str, str)

    MONTHS_PL = [
        "stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca",
        "lipca", "sierpnia", "września", "października", "listopada", "grudnia",
    ]
    WEEKDAYS_PL = [
        "Poniedziałek", "Wtorek", "Środa", "Czwartek",
        "Piątek", "Sobota", "Niedziela",
    ]

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("locationPanel")
        self._geo_service = GeolocationService()
        self._location_repo = LocationRepository()
        self._current_location: Optional[Location] = None
        self._setup_ui()
        self._load_default_location()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("Lokalizacja")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        search_layout = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Szukaj miasta...")
        self._search_input.setObjectName("searchInput")
        self._search_input.returnPressed.connect(self._on_search)
        search_layout.addWidget(self._search_input)

        self._search_btn = QPushButton("Szukaj")
        self._search_btn.setObjectName("searchBtn")
        self._search_btn.clicked.connect(self._on_search)
        search_layout.addWidget(self._search_btn)
        layout.addLayout(search_layout)

        self._results_list = QListWidget()
        self._results_list.setObjectName("searchResults")
        self._results_list.setMaximumHeight(120)
        self._results_list.hide()
        self._results_list.itemClicked.connect(self._on_result_selected)
        layout.addWidget(self._results_list)

        self._saved_combo = QComboBox()
        self._saved_combo.setObjectName("savedLocations")
        self._saved_combo.currentIndexChanged.connect(self._on_saved_selected)
        layout.addWidget(self._saved_combo)

        self._timezone_label = QLabel("Strefa: --")
        self._timezone_label.setObjectName("tzLabel")
        layout.addWidget(self._timezone_label)

        self._date_label = QLabel()
        self._date_label.setObjectName("dateLabel")
        self._date_label.setWordWrap(True)
        layout.addWidget(self._date_label)

        self._time_label = QLabel()
        self._time_label.setObjectName("timeLabel")
        layout.addWidget(self._time_label)

        self._clock_timer = QTimer()
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(1000)

        layout.addStretch()

    def _load_default_location(self) -> None:
        saved = self._location_repo.get_all()
        self._saved_combo.clear()
        self._saved_combo.addItem("-- Wybierz lokalizację --", None)
        for loc in saved:
            self._saved_combo.addItem(loc.name, loc)
        default_loc = self._location_repo.get_default()
        if default_loc:
            self._current_location = default_loc
            idx = self._saved_combo.findData(default_loc)
            if idx >= 0:
                self._saved_combo.setCurrentIndex(idx)
        else:
            self._current_location = Location(**DEFAULT_LOCATION)
            self._saved_combo.setCurrentIndex(0)
        self._emit_location_changed()

    def _on_search(self) -> None:
        query = self._search_input.text().strip()
        if len(query) < 2:
            return
        from asyncio import run
        try:
            results = run(self._geo_service.search(query))
        except ConnectionError:
            self._results_list.clear()
            self._results_list.addItem("Błąd połączenia")
            self._results_list.show()
            return
        self._results_list.clear()
        for result in results:
            item = QListWidgetItem(f"{result.name} ({result.timezone})")
            item.setData(1, result)
            self._results_list.addItem(item)
        self._results_list.show()

    def _on_result_selected(self, item: QListWidgetItem) -> None:
        result: GeocodingResult = item.data(1)
        self._results_list.hide()
        location = Location(
            name=result.name,
            latitude=result.latitude,
            longitude=result.longitude,
            timezone=result.timezone,
        )
        loc_id = self._location_repo.upsert(location)
        location.id = loc_id
        self._current_location = location
        self._saved_combo.blockSignals(True)
        idx = self._saved_combo.findData(location)
        if idx < 0:
            self._saved_combo.addItem(location.name, location)
            idx = self._saved_combo.count() - 1
        self._saved_combo.setCurrentIndex(idx)
        self._saved_combo.blockSignals(False)
        self._update_date_time()
        self._emit_location_changed()

    def _on_saved_selected(self, index: int) -> None:
        if index < 0:
            return
        loc = self._saved_combo.itemData(index)
        if loc is None:
            return
        self._current_location = loc
        self._location_repo.upsert(loc)
        self._update_date_time()
        self._emit_location_changed()

    def _update_date_time(self) -> None:
        if self._current_location is None:
            return
        try:
            tz = pytz.timezone(self._current_location.timezone)
        except Exception:
            tz = pytz.UTC
        now = datetime.now(tz)
        weekday = self.WEEKDAYS_PL[now.weekday()]
        date_text = (
            f"{weekday}, {now.day} {self.MONTHS_PL[now.month - 1]} {now.year}"
        )
        self._date_label.setText(date_text)
        self._timezone_label.setText(f"Strefa: {self._current_location.timezone}")
        self._time_label.setText(now.strftime("%H:%M:%S"))

    def _update_clock(self) -> None:
        if self._current_location is None:
            return
        try:
            tz = pytz.timezone(self._current_location.timezone)
        except Exception:
            tz = pytz.UTC
        now = datetime.now(tz)
        weekday = self.WEEKDAYS_PL[now.weekday()]
        date_text = (
            f"{weekday}, {now.day} {self.MONTHS_PL[now.month - 1]} {now.year}"
        )
        self._date_label.setText(date_text)
        self._time_label.setText(now.strftime("%H:%M:%S"))

    def _emit_location_changed(self) -> None:
        if self._current_location is None:
            return
        self.location_changed.emit(
            self._current_location.latitude,
            self._current_location.longitude,
            self._current_location.timezone,
            self._current_location.name,
        )

    @property
    def current_location(self) -> Optional[Location]:
        return self._current_location
