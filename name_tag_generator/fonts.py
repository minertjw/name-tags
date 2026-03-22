from pathlib import Path

from PIL import ImageFont

from .render_config import DEFAULT_FONT_PATHS, FALLBACK_FONT_NAMES, FontLike


def load_font(font_path: str | Path | None, size: int) -> FontLike:
    if font_path is not None:
        return ImageFont.truetype(str(font_path), size=size)

    for default_font_path in DEFAULT_FONT_PATHS:
        if default_font_path.is_file():
            return ImageFont.truetype(str(default_font_path), size=size)

    for font_name in FALLBACK_FONT_NAMES:
        try:
            return ImageFont.truetype(font_name, size=size)
        except OSError:
            continue

    return ImageFont.load_default()