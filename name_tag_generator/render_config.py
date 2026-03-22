from dataclasses import dataclass
from pathlib import Path

from PIL import ImageFont


BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"
ASPECT_RATIO = 19 / 12
DEFAULT_TEXT_COLOR = "#000000"
DEFAULT_SHADOW_COLOR = "#c00000"
DEFAULT_SHADOW_OFFSET = (4, 4)
DEFAULT_SHADOW_ANGLE = 45.0
DEFAULT_MARGIN_CM = 1.0
DEFAULT_FONT_SIZE = 120
DEFAULT_SECONDARY_FONT_SCALE = 0.65
DEFAULT_DPI = 300
DEFAULT_LINE_SPACING = 12
MIN_FONT_SIZE = 12
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff"}
TOP_IMAGE_MAX_WIDTH_RATIO = 0.5
TOP_IMAGE_MAX_HEIGHT_RATIO = 0.25
TOP_IMAGE_VERTICAL_OFFSET_RATIO = 0.12
DEFAULT_FONT_PATHS = (
    BASE_DIR / "assets" / "norwester.otf",
    BASE_DIR / "assets" / "norwester.ttf",
    BASE_DIR / "assets" / "Norwester.otf",
    BASE_DIR / "assets" / "Norwester.ttf",
)
FALLBACK_FONT_NAMES = (
    "Norwester",
    "norwester",
    "Norwester.otf",
    "Norwester.ttf",
    "norwester.otf",
    "norwester.ttf",
    "arial.ttf",
    "segoeui.ttf",
    "calibri.ttf",
    "DejaVuSans.ttf",
)
TEXT_REGION_SPECS = (
    ("top", 0.075, 0.16),
    ("middle", 0.45, 0.26),
    ("bottom", 0.9, 0.16),
)
FontLike = ImageFont.ImageFont | ImageFont.FreeTypeFont


@dataclass(frozen=True)
class TextRegion:
    center_y: float
    font: FontLike
    lines: list[str]