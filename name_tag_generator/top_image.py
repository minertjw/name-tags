from pathlib import Path

from PIL import Image

from .normalization import strip_wrapping_quotes
from .render_config import (
    IMAGE_SUFFIXES,
    IMAGES_DIR,
    TEXT_REGION_SPECS,
    TOP_IMAGE_MAX_HEIGHT_RATIO,
    TOP_IMAGE_MAX_WIDTH_RATIO,
    TOP_IMAGE_VERTICAL_OFFSET_RATIO,
)


def resolve_image_filename(text: str) -> Path | None:
    candidate_name = Path(strip_wrapping_quotes(text)).name
    if not candidate_name:
        return None
    if Path(candidate_name).suffix.lower() not in IMAGE_SUFFIXES:
        return None
    if not IMAGES_DIR.is_dir():
        return None
    for image_path in IMAGES_DIR.iterdir():
        if image_path.is_file() and image_path.name.lower() == candidate_name.lower():
            return image_path
    return None


def draw_top_image(
    image: Image.Image,
    image_path: Path,
    margin_x: int,
    margin_y: int,
) -> None:
    available_width = max(1, image.width - (margin_x * 2))
    available_height = max(1, image.height - (margin_y * 2))
    _, center_ratio, _ = TEXT_REGION_SPECS[0]
    max_width = max(1, int(round(available_width * TOP_IMAGE_MAX_WIDTH_RATIO)))
    max_height = max(1, int(round(available_height * TOP_IMAGE_MAX_HEIGHT_RATIO)))
    region_center_y = margin_y + (available_height * center_ratio)

    with Image.open(image_path) as source_image:
        overlay = source_image.convert("RGBA")

    if overlay.width > 0 and overlay.height > 0:
        overlay.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

    vertical_offset = int(round(overlay.height * TOP_IMAGE_VERTICAL_OFFSET_RATIO))
    left = int(round((image.width - overlay.width) / 2))
    top = int(round(region_center_y - (overlay.height / 2) + vertical_offset))
    image.alpha_composite(overlay, (left, top))