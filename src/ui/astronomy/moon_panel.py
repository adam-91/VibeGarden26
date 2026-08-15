from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from src.models import MoonData


class MoonPanel(QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("moonPanel")
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        title = QLabel("Faza Księżyca")
        title.setObjectName("panelTitle")
        layout.addWidget(title)

        self._moon_icon = QLabel("🌕")
        self._moon_icon.setObjectName("moonIcon")
        self._moon_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._moon_icon)

        self._phase_name = QLabel("--")
        self._phase_name.setObjectName("moonPhaseName")
        self._phase_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._phase_name.setWordWrap(True)
        layout.addWidget(self._phase_name)

        self._moonrise_label = QLabel("Wschód K.: --")
        self._moonrise_label.setObjectName("moonDetail")
        layout.addWidget(self._moonrise_label)

        self._moonset_label = QLabel("Zachód K.: --")
        self._moonset_label.setObjectName("moonDetail")
        layout.addWidget(self._moonset_label)

        layout.addStretch()

    def update_moon(self, moon: Optional[MoonData]) -> None:
        if moon is None:
            self._moon_icon.setText("🌕")
            self._phase_name.setText("Brak danych")
            return
        self._moon_icon.setText(moon.moon_phase_icon)
        self._phase_name.setText(moon.moon_phase_name)
        if moon.moonrise:
            moonrise_time = moon.moonrise.split("T")[-1] if "T" in moon.moonrise else moon.moonrise
            self._moonrise_label.setText(f"Wschód K.: {moonrise_time}")
        if moon.moonset:
            moonset_time = moon.moonset.split("T")[-1] if "T" in moon.moonset else moon.moonset
            self._moonset_label.setText(f"Zachód K.: {moonset_time}")

    def clear(self) -> None:
        self._moon_icon.setText("🌕")
        self._phase_name.setText("--")
        self._moonrise_label.setText("Wschód K.: --")
        self._moonset_label.setText("Zachód K.: --")
