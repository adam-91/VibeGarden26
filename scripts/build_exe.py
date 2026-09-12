import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT / "src"))


def run_pyinstaller():
    import PyInstaller.__main__

    add_data = f"resources{os.pathsep}resources"

    args = [
        "src/main.py",
        "--name=VibeGarden26",
        "--onefile",
        "--windowed",
        "--clean",
        f"--add-data={add_data}",
    ]

    if sys.platform == "win32":
        args.append("--icon=resources/icons/app.ico")
    elif sys.platform == "linux":
        args.append("--icon=resources/icons/app.png")

    PyInstaller.__main__.run(args)


if __name__ == "__main__":
    run_pyinstaller()
