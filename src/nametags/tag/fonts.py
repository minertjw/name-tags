from pathlib import Path

from PIL import ImageFont

from nametags.__main__ import BASE_DIR

BUNDLED_FONT_DIR = BASE_DIR / "assets" / "fonts"

SYSTEM_FONTS = {
    "arial.ttf": "Arial",
    "segoeui.ttf": "Segoe UI",
    "calibri.ttf": "Calibri",
    "DejaVuSans.ttf": "DejaVu Sans",
}

FontLike = ImageFont.ImageFont | ImageFont.FreeTypeFont


def _is_font_loadable(font_source: str) -> bool:
    try:
        ImageFont.truetype(font_source)
    except OSError:
        return False
    return True


def get_font_options() -> list[tuple[str, str]]:
    options: list[tuple[str, str]] = []
    seen_values = {""}

    # Bundled fonts
    for font_path in BUNDLED_FONT_DIR.iterdir():
        if not font_path.is_file():
            continue

        value = str(font_path)
        if value in seen_values or not _is_font_loadable(value):
            continue

        options.append((font_path.stem.capitalize(), value))
        seen_values.add(value)

    # System fonts
    for font_tuple in SYSTEM_FONTS.items():
        font_name = font_tuple[0]
        if font_name in seen_values or not _is_font_loadable(font_name):
            continue

        options.append((SYSTEM_FONTS[font_name], font_name))
        seen_values.add(font_name)

    return options


def load_font(font_path: str | Path | None, size: int) -> FontLike:
    if font_path is not None:
        normalized_font_path = str(font_path).strip()
        if _is_font_loadable(normalized_font_path):
            return ImageFont.truetype(normalized_font_path, size=size)

    return ImageFont.load_default()
