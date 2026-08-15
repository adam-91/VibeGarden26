import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))


def run_pyinstaller():
    import PyInstaller.__main__

    args = [
        "src/main.py",
        "--name=VibeGarden26",
        "--onefile",
        "--windowed",
        "--clean",
        "--add-data=resources:resources",
    ]

    if sys.platform == "win32":
        args.append("--icon=resources/icons/app.ico")
    elif sys.platform == "linux":
        args.append("--icon=resources/icons/app.png")

    PyInstaller.__main__.run(args)


if __name__ == "__main__":
    run_pyinstaller()
