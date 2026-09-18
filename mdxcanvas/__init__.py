from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent

__version__ = (_PACKAGE_DIR / "VERSION").read_text().strip()
skilldir = _PACKAGE_DIR / "skills"