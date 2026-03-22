from pathlib import Path

from PySide6.QtGui import QIcon


BASE_DIR = Path(__file__).resolve().parent.parent
ICON_PATHS = (
    BASE_DIR / "assets" / "app_icon.ico",
    BASE_DIR / "assets" / "app_icon.png",
)
HEADER_GIF_PATH = BASE_DIR / "assets" / "header_animation.gif"


def load_app_icon() -> QIcon | None:
    for icon_path in ICON_PATHS:
        if icon_path.is_file():
            icon = QIcon(str(icon_path))
            if not icon.isNull():
                return icon
    return None