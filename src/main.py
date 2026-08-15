from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.app.application import Application


def main() -> None:
    app = Application()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
