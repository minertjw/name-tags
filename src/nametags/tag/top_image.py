from collections.abc import Mapping
from pathlib import Path

from PIL import Image

from nametags.tag.normalization import strip_wrapping_quotes
from nametags.tag.render_config import (
    IMAGE_SUFFIXES,
    IMAGES_DIR,
    TextBoxSpec,
)


def image_filename_from_text(text: str) -> str | None:
    candidate_name = Path(strip_wrapping_quotes(text)).name
    if not candidate_name:
        return None
    if Path(candidate_name).suffix.lower() not in IMAGE_SUFFIXES:
        return None
    return candidate_name


def resolve_image_filename(
    text: str,
    image_files: Mapping[str, Path] | None = None,
) -> Path | None:
    candidate_name = image_filename_from_text(text)
    if candidate_name is None:
        return None
    if image_files is not None:
        return image_files.get(candidate_name.casefold())
    if not IMAGES_DIR.is_dir():
        return None
    for image_path in IMAGES_DIR.iterdir():
        if (
            image_path.is_file()
            and image_path.name.casefold() == candidate_name.casefold()
        ):
            return image_path
    return None


def draw_top_image(
    image: Image.Image,
    image_path: Path,
    top_text_box: TextBoxSpec,
    middle_text_box: TextBoxSpec,
) -> None:
    _, left_ratio, top_ratio, width_ratio, _height_ratio = top_text_box
    _, _, middle_top_ratio, _, _ = middle_text_box
    box_left = round(image.width * left_ratio)
    box_top = round(image.height * top_ratio)
    middle_top = round(image.height * middle_top_ratio)
    max_width = max(1, (round(image.width * width_ratio)))
    max_height = middle_top - box_top - 2
    if max_height < 1:
        raise ValueError(
            "The top and middle boxes must leave room for the requested top image."
        )

    with Image.open(image_path) as source_image:
        overlay = source_image.convert("RGBA")

    if overlay.width > 0 and overlay.height > 0:
        scale = min(max_width / overlay.width, max_height / overlay.height)
        overlay = overlay.resize(
            (
                max(1, round(overlay.width * scale)),
                max(1, round(overlay.height * scale)),
            ),
            Image.Resampling.LANCZOS,
        )

    left = box_left + (round((max_width - overlay.width) / 2))
    image.alpha_composite(overlay, (left, box_top))
