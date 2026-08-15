from __future__ import annotations

from datetime import date
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from src.config.settings import CATEGORY_COLORS
from src.models import CalendarEvent
from src.ui.calendar.clock_picker import ClockTimeField


class EventEditorDialog(QDialog):
    def __init__(
        self,
        parent: Optional[QWidget] = None,
        event: Optional[CalendarEvent] = None,
        default_date: Optional[date] = None,
    ) -> None:
        super().__init__(parent)
        self._event = event
        self._default_date = default_date or date.today()
        self._result_event: Optional[CalendarEvent] = None
        self._setup_ui()
        self._populate()
        self.setMinimumWidth(460)

    def _setup_ui(self) -> None:
        self.setWindowTitle(
            "Edytuj wydarzenie" if self._event else "Nowe wydarzenie"
        )
        self.setObjectName("eventEditor")

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(8)

        self._title_edit = QLineEdit()
        self._title_edit.setPlaceholderText("Nazwa wydarzenia")
        form.addRow("Tytuł:", self._title_edit)

        self._desc_edit = QTextEdit()
        self._desc_edit.setPlaceholderText("Opis...")
        self._desc_edit.setMaximumHeight(80)
        form.addRow("Opis:", self._desc_edit)

        self._category_combo = QComboBox()
        self._category_combo.addItem("Ogólne", "general")
        self._category_combo.addItem("Biurowe", "office")
        self._category_combo.addItem("Ogrodnicze", "garden")
        form.addRow("Kategoria:", self._category_combo)

        self._start_date = QDateEdit()
        self._start_date.setCalendarPopup(True)
        self._start_date.setDisplayFormat("yyyy-MM-dd")
        form.addRow("Data startu:", self._start_date)

        self._end_date = QDateEdit()
        self._end_date.setCalendarPopup(True)
        self._end_date.setDisplayFormat("yyyy-MM-dd")
        self._end_date.setDate(self._start_date.date())
        form.addRow("Data końca:", self._end_date)

        self._all_day_check = QCheckBox("Całodniowe")
        self._all_day_check.setChecked(True)
        form.addRow("", self._all_day_check)

        self._start_time = ClockTimeField()
        form.addRow("Godz. startu:", self._start_time)

        self._end_time = ClockTimeField()
        form.addRow("Godz. końca:", self._end_time)

        self._color_btn = QPushButton()
        self._color_btn.setFixedSize(32, 32)
        self._color_btn.setStyleSheet("border: 2px solid #555; border-radius: 16px;")
        form.addRow("Kolor:", self._color_btn)

        layout.addLayout(form)

        rec_label = QLabel("Powtarzanie")
        rec_label.setObjectName("sectionLabel")
        layout.addWidget(rec_label)

        rec_form = QFormLayout()
        rec_form.setSpacing(6)

        self._recurrence_combo = QComboBox()
        self._recurrence_combo.addItem("Bez powtarzania", "none")
        self._recurrence_combo.addItem("Codziennie", "daily")
        self._recurrence_combo.addItem("Co tydzień", "weekly")
        self._recurrence_combo.addItem("Co miesiąc", "monthly")
        self._recurrence_combo.addItem("Co rok", "yearly")
        rec_form.addRow("Typ:", self._recurrence_combo)

        self._recurrence_interval = QSpinBox()
        self._recurrence_interval.setMinimum(1)
        self._recurrence_interval.setMaximum(999)
        self._recurrence_interval.setValue(1)
        rec_form.addRow("Co ile:", self._recurrence_interval)

        self._recurrence_end = QDateEdit()
        self._recurrence_end.setCalendarPopup(True)
        self._recurrence_end.setDisplayFormat("yyyy-MM-dd")
        self._recurrence_end.setSpecialValueText("Bez końca")
        self._recurrence_end.setDate(date(2099, 12, 31))
        rec_form.addRow("Koniec:", self._recurrence_end)

        layout.addLayout(rec_form)

        rem_label = QLabel("Przypomnienie")
        rem_label.setObjectName("sectionLabel")
        layout.addWidget(rem_label)

        rem_form = QFormLayout()
        rem_form.setSpacing(6)

        self._reminder_check = QCheckBox("Włączone")
        rem_form.addRow("", self._reminder_check)

        self._reminder_combo = QComboBox()
        self._reminder_combo.addItem("Dzień wcześniej", "day")
        self._reminder_combo.addItem("Godzinę wcześniej", "hour")
        self._reminder_combo.addItem("Własny czas (min)", "custom")
        rem_form.addRow("Kiedy:", self._reminder_combo)

        self._reminder_custom = QSpinBox()
        self._reminder_custom.setMinimum(5)
        self._reminder_custom.setMaximum(10080)
        self._reminder_custom.setValue(30)
        self._reminder_custom.setSuffix(" min")
        self._reminder_custom.setEnabled(False)
        rem_form.addRow("Wartość:", self._reminder_custom)

        layout.addLayout(rem_form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._all_day_check.toggled.connect(self._on_all_day_toggled)
        self._color_btn.clicked.connect(self._on_color_pick)
        self._category_combo.currentIndexChanged.connect(self._on_category_changed)
        self._reminder_combo.currentIndexChanged.connect(self._on_reminder_type_changed)
        self._reminder_check.toggled.connect(lambda c: self._reminder_combo.setEnabled(c))
        self._reminder_combo.setEnabled(False)
        self._title_edit.textChanged.connect(lambda _: self._set_field_error(self._title_edit, False))

    def _set_field_error(self, widget, error: bool) -> None:
        widget.setProperty("error", error)
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        widget.update()

    def _on_all_day_toggled(self, checked: bool) -> None:
        self._start_time.setEnabled(True)
        self._end_time.setEnabled(True)

    def _on_category_changed(self, idx: int) -> None:
        category = self._category_combo.itemData(idx)
        if category in CATEGORY_COLORS:
            self._current_color = CATEGORY_COLORS[category]
            self._color_btn.setStyleSheet(
                f"background-color: {self._current_color};"
                " border: 2px solid #555; border-radius: 16px;"
            )

    def _on_reminder_type_changed(self, idx: int) -> None:
        self._reminder_custom.setEnabled(
            self._reminder_combo.currentData() == "custom"
        )

    def _on_color_pick(self) -> None:
        color = QColorDialog.getColor()
        if color.isValid():
            self._current_color = color.name()
            self._color_btn.setStyleSheet(
                f"background-color: {color.name()}; border: 2px solid #555; border-radius: 16px;"
            )

    def _populate(self) -> None:
        self._current_color = "#4CAF50"
        if self._event:
            self._title_edit.setText(self._event.title)
            self._desc_edit.setPlainText(self._event.description)
            idx = self._category_combo.findData(self._event.category)
            if idx >= 0:
                self._category_combo.setCurrentIndex(idx)
            self._start_date.setDate(date.fromisoformat(self._event.start_date))
            if self._event.end_date:
                self._end_date.setDate(date.fromisoformat(self._event.end_date))
            if self._event.start_time:
                h, m = map(int, self._event.start_time.split(":"))
                self._start_time.set_time(h, m)
            if self._event.end_time:
                h, m = map(int, self._event.end_time.split(":"))
                self._end_time.set_time(h, m)
            self._all_day_check.setChecked(self._event.is_all_day)
            self._current_color = self._event.color
            ridx = self._recurrence_combo.findData(self._event.recurrence_type)
            if ridx >= 0:
                self._recurrence_combo.setCurrentIndex(ridx)
            self._recurrence_interval.setValue(self._event.recurrence_interval)
            if self._event.recurrence_end_date:
                self._recurrence_end.setDate(date.fromisoformat(self._event.recurrence_end_date))
            self._reminder_check.setChecked(self._event.reminder_enabled)
            self._reminder_combo.setEnabled(self._event.reminder_enabled)
            if self._event.reminder_unit == "custom":
                self._reminder_custom.setValue(self._event.reminder_value)
            ridx2 = self._reminder_combo.findData(self._event.reminder_unit)
            if ridx2 >= 0:
                self._reminder_combo.setCurrentIndex(ridx2)
        else:
            self._start_date.setDate(self._default_date)
            self._end_date.setDate(self._default_date)

        self._color_btn.setStyleSheet(
            f"background-color: {self._current_color}; border: 2px solid #555; border-radius: 16px;"
        )

    def _on_accept(self) -> None:
        title = self._title_edit.text().strip()
        if not title:
            self._set_field_error(self._title_edit, True)
            self._title_edit.setFocus()
            return
        reminder_unit = self._reminder_combo.currentData()
        reminder_value = (
            self._reminder_custom.value()
            if reminder_unit == "custom"
            else 1
        )
        start_h, start_m = self._start_time.time_parts()
        end_h, end_m = self._end_time.time_parts()
        self._result_event = CalendarEvent(
            id=self._event.id if self._event else None,
            title=title,
            description=self._desc_edit.toPlainText().strip(),
            category=self._category_combo.currentData(),
            start_date=self._start_date.date().toString("yyyy-MM-dd"),
            end_date=self._end_date.date().toString("yyyy-MM-dd"),
            start_time=(
                f"{start_h:02d}:{start_m:02d}"
                if not self._all_day_check.isChecked()
                else None
            ),
            end_time=(
                f"{end_h:02d}:{end_m:02d}"
                if not self._all_day_check.isChecked()
                else None
            ),
            is_all_day=self._all_day_check.isChecked(),
            color=self._current_color,
            location_id=self._event.location_id if self._event else None,
            recurrence_type=self._recurrence_combo.currentData(),
            recurrence_interval=self._recurrence_interval.value(),
            recurrence_end_date=(
                self._recurrence_end.date().toString("yyyy-MM-dd")
                if self._recurrence_combo.currentData() != "none"
                else None
            ),
            reminder_enabled=self._reminder_check.isChecked(),
            reminder_value=reminder_value,
            reminder_unit=reminder_unit,
        )
        self.accept()

    @property
    def result_event(self) -> Optional[CalendarEvent]:
        return self._result_event
