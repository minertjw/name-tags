import sys
from dataclasses import dataclass
from pathlib import Path

from nametags.tag.fonts import FontLike

if getattr(sys, "frozen", False):
    BASE_DIR = Path(__file__).resolve().parent.parent
else:
    BASE_DIR = Path(__file__).resolve().parent

IMAGES_DIR = BASE_DIR / "images"
DEFAULT_TEXT_COLOR = "#000000"
DEFAULT_SHADOW_ANGLE = 45.0
DEFAULT_SHADOW_DISTANCE = 5.66
DEFAULT_MARGIN_CM = 1.0
DEFAULT_DPI = 300
DEFAULT_LINE_SPACING = 12
MIN_FONT_SIZE = 12
DEFAULT_MIDDLE_MAX_FONT_SIZE = 180
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}


# Each tuple is (region name, left edge, top edge, width, height).
# Numeric values are fractions of the template width or height, from 0.0 to 1.0.
TEXT_BOX_SPECS = (
    ("top", 0.15, 0.08, 0.70, 0.12),
    ("middle", 0.06, 0.32, 0.88, 0.30),
    ("bottom", 0.14, 0.75, 0.78, 0.10),
)
TextBoxSpec = tuple[str, float, float, float, float]


@dataclass(frozen=True)
class TextRegion:
    name: str
    left: int
    top: int
    width: int
    height: int
    font: FontLike
    lines: list[str]
