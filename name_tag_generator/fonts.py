from pathlib import Path

from PIL import ImageFont

from .render_config import DEFAULT_FONT_PATHS, FALLBACK_FONT_NAMES, FontLike


FONT_LABELS = {
    "Norwester": "Norwester",
    "norwester": "Norwester",
    "Norwester.otf": "Norwester",
    "Norwester.ttf": "Norwester",
    "norwester.otf": "Norwester",
    "norwester.ttf": "Norwester",
    "arial.ttf": "Arial",
    "segoeui.ttf": "Segoe UI",
    "calibri.ttf": "Calibri",
    "DejaVuSans.ttf": "DejaVu Sans",
}


def _is_font_loadable(font_source: str | Path) -> bool:
    try:
        ImageFont.truetype(str(font_source), size=12)
    except OSError:
        return False
    return True


def get_font_options() -> list[tuple[str, str]]:
    options: list[tuple[str, str]] = [("Default (Norwester fallback)", "")]
    seen_values = {""}

    for font_path in DEFAULT_FONT_PATHS:
        if not font_path.is_file():
            continue

        value = str(font_path)
        if value in seen_values or not _is_font_loadable(value):
            continue

        options.append((font_path.stem, value))
        seen_values.add(value)

    for font_name in FALLBACK_FONT_NAMES:
        if font_name in seen_values or not _is_font_loadable(font_name):
            continue

        options.append((FONT_LABELS.get(font_name, font_name), font_name))
        seen_values.add(font_name)

    return options


def load_font(font_path: str | Path | None, size: int) -> FontLike:
    if font_path is not None:
        normalized_font_path = str(font_path).strip()
        if normalized_font_path:
            return ImageFont.truetype(normalized_font_path, size=size)

    for default_font_path in DEFAULT_FONT_PATHS:
        if default_font_path.is_file():
            return ImageFont.truetype(str(default_font_path), size=size)

    for font_name in FALLBACK_FONT_NAMES:
        try:
            return ImageFont.truetype(font_name, size=size)
        except OSError:
            continue

    return ImageFont.load_default()