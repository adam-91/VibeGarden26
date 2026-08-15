from __future__ import annotations

from asyncio import run
from datetime import date
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QMainWindow,
    QSplitter,
    QStatusBar,
    QWidget,
)

from src.config.settings import APP_NAME, APP_VERSION
from src.ui.calendar.calendar_widget import CalendarWidget
from src.ui.calendar.event_editor import EventEditorDialog
from src.ui.sidebar.location_panel import LocationPanel
from src.ui.weather.weather_panel import WeatherPanel
from src.ui.astronomy.moon_panel import MoonPanel


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 800)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("mainSplitter")

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setMinimumWidth(260)
        sidebar.setMaximumWidth(350)
        sidebar_layout = self._build_sidebar()
        sidebar.setLayout(sidebar_layout)
        splitter.addWidget(sidebar)

        self._calendar = CalendarWidget()
        splitter.addWidget(self._calendar)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 920])

        from PySide6.QtWidgets import QHBoxLayout
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        self._status_bar = QStatusBar()
        self.setStatusBar(self._status_bar)
        self._status_bar.showMessage("Gotowy")

    def _build_sidebar(self) -> "QVBoxLayout":
        from PySide6.QtWidgets import QVBoxLayout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._location_panel = LocationPanel()
        layout.addWidget(self._location_panel, 2)

        line1 = self._make_separator()
        layout.addWidget(line1)

        self._weather_panel = WeatherPanel()
        layout.addWidget(self._weather_panel, 5)

        line2 = self._make_separator()
        layout.addWidget(line2)

        self._moon_panel = MoonPanel()
        layout.addWidget(self._moon_panel, 1)

        return layout

    @staticmethod
    def _make_separator() -> "QFrame":
        from PySide6.QtWidgets import QFrame
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("sidebarSeparator")
        line.setFixedHeight(1)
        return line

    def _connect_signals(self) -> None:
        self._location_panel.location_changed.connect(self._on_location_changed)
        self._calendar._daily_list.add_event.connect(self._on_add_event)
        self._calendar._daily_list.edit_event.connect(self._on_edit_event)
        self._calendar._daily_list.delete_event.connect(self._on_delete_event)

        QTimer.singleShot(100, self._initial_location_refresh)

    def _initial_location_refresh(self) -> None:
        loc = self._location_panel.current_location
        if loc:
            self._on_location_changed(loc.latitude, loc.longitude, loc.timezone, loc.name)

    def _on_location_changed(
        self, latitude: float, longitude: float, timezone: str, name: str
    ) -> None:
        async def refresh() -> None:
            await self._calendar.model.refresh_weather_and_moon(
                latitude, longitude, timezone, name
            )
            self._weather_panel.update_weather(self._calendar.model.weather)
            self._moon_panel.update_moon(self._calendar.model.moon)
        try:
            run(refresh())
        except Exception:
            self._weather_panel.clear()
            self._moon_panel.clear()

    def _on_add_event(self, dt: date) -> None:
        dialog = EventEditorDialog(self, default_date=dt)
        if dialog.exec() == EventEditorDialog.DialogCode.Accepted:
            event = dialog.result_event
            if event:
                self._calendar.model.add_event(event)
                self._calendar.refresh()
                self._status_bar.showMessage(
                    f"Dodano wydarzenie: {event.title}", 3000
                )

    def _on_edit_event(self, event) -> None:
        dialog = EventEditorDialog(self, event=event)
        if dialog.exec() == EventEditorDialog.DialogCode.Accepted:
            updated = dialog.result_event
            if updated:
                self._calendar.model.update_event(updated)
                self._calendar.refresh()
                self._status_bar.showMessage(
                    f"Zaktualizowano wydarzenie: {updated.title}", 3000
                )

    def _on_delete_event(self, event_id: int) -> None:
        self._calendar.model.delete_event(event_id)
        self._calendar.refresh()
        self._status_bar.showMessage("Usunięto wydarzenie", 3000)
