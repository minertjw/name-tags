from dataclasses import dataclass
from pathlib import Path

from PIL import ImageFont


BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"
DEFAULT_TEXT_COLOR = "#000000"
DEFAULT_SHADOW_COLOR = "#c00000"
DEFAULT_SHADOW_ANGLE = 45.0
DEFAULT_SHADOW_DISTANCE = 5.66
DEFAULT_MARGIN_CM = 1.0
DEFAULT_DPI = 300
DEFAULT_LINE_SPACING = 12
MIN_FONT_SIZE = 12
DEFAULT_MIDDLE_MAX_FONT_SIZE = 120
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
TEXT_BOX_SPECS = (
    ("top", 0.08, 0.02, 0.84, 0.14),
    ("middle", 0.06, 0.30, 0.88, 0.30),
    ("bottom", 0.08, 0.78, 0.84, 0.18),
)
TextBoxSpec = tuple[str, float, float, float, float]
FontLike = ImageFont.ImageFont | ImageFont.FreeTypeFont


@dataclass(frozen=True)
class TextRegion:
    left: int
    top: int
    width: int
    height: int
    font: FontLike
    lines: list[str]