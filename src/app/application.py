from __future__ import annotations

import logging
import sys
from typing import Optional

from PySide6.QtCore import QTimer, Signal, QObject
from PySide6.QtWidgets import QApplication

from src.config.settings import APP_NAME
from src.database.connection import db

logger = logging.getLogger(__name__)


class Application:
    _instance: Optional["Application"] = None

    def __init__(self) -> None:
        self._qt_app: Optional[QApplication] = None
        self._main_window = None
        Application._instance = self

    @classmethod
    def instance(cls) -> "Application":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @property
    def qt_app(self) -> QApplication:
        if self._qt_app is None:
            self._qt_app = QApplication(sys.argv)
            self._qt_app.setApplicationName(APP_NAME)
            self._qt_app.setOrganizationName("VibeGarden26")
        return self._qt_app

    def run(self) -> int:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        logger.info("Starting %s v0.1.0", APP_NAME)

        db.init_schema()

        app = self.qt_app
        self._apply_stylesheet(app)

        from src.ui.main_window import MainWindow
        self._main_window = MainWindow()
        self._main_window.show()

        return app.exec()

    def quit(self) -> None:
        db.close()
        if self._qt_app:
            self._qt_app.quit()

    @staticmethod
    def _apply_stylesheet(app: QApplication) -> None:
        from pathlib import Path
        qss_path = (
            Path(__file__).parent.parent.parent / "resources" / "styles" / "main.qss"
        )
        if qss_path.exists():
            with open(qss_path, encoding="utf-8") as f:
                app.setStyleSheet(f.read())
