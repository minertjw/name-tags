from pathlib import Path

from PIL import ImageDraw

from .fonts import load_font
from .render_config import FontLike, MIN_FONT_SIZE, TEXT_REGION_SPECS, TextRegion


def measure_text(draw: ImageDraw.ImageDraw, text: str, font: FontLike) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return int(right - left), int(bottom - top)


def measure_text_block(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: FontLike,
    line_spacing: int,
) -> tuple[int, int]:
    text = "\n".join(lines)
    left, top, right, bottom = draw.multiline_textbbox(
        (0, 0),
        text,
        font=font,
        spacing=line_spacing,
        align="center",
    )
    return int(right - left), int(bottom - top)


def split_text_lines(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: FontLike,
    line_spacing: int,
    max_text_width: int,
    max_text_height: int,
    max_lines: int = 2,
) -> list[str]:
    text_width, text_height = measure_text(draw, text, font)
    if text_width <= max_text_width and text_height <= max_text_height:
        return [text]

    words = text.split()
    if max_lines < 2 or len(words) < 2:
        raise ValueError("Text is too wide to fit on the tag at the configured font size.")

    best_lines: list[str] | None = None
    best_width: int | None = None
    for index in range(1, len(words)):
        candidate_lines = [" ".join(words[:index]), " ".join(words[index:])]
        block_width, block_height = measure_text_block(
            draw,
            candidate_lines,
            font,
            line_spacing,
        )
        if block_width > max_text_width or block_height > max_text_height:
            continue
        if best_width is None or block_width < best_width:
            best_lines = candidate_lines
            best_width = block_width

    if best_lines is None:
        raise ValueError(
            "Text is too wide to fit on the tag at the configured font size, even across two lines."
        )

    return best_lines


def fit_text_region(
    draw: ImageDraw.ImageDraw,
    text: str,
    font_path: str | Path | None,
    starting_font_size: int,
    line_spacing: int,
    max_text_width: int,
    max_text_height: int,
) -> tuple[FontLike, list[str]]:
    for candidate_size in range(starting_font_size, MIN_FONT_SIZE - 1, -2):
        font = load_font(font_path, candidate_size)
        try:
            lines = split_text_lines(
                draw,
                text,
                font,
                line_spacing,
                max_text_width,
                max_text_height,
            )
        except ValueError:
            continue
        return font, lines

    raise ValueError("Text is too wide to fit on the tag, even after reducing the font size.")


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    image_width: int,
    center_y: float,
    lines: list[str],
    font: FontLike,
    text_color: str,
    shadow_color: str,
    shadow_offset: tuple[int, int],
    margin_x: int,
    line_spacing: int,
) -> None:
    text = "\n".join(lines)
    text_width, text_height = measure_text_block(draw, lines, font, line_spacing)
    x = max(margin_x, (image_width - text_width) / 2)
    y = center_y - (text_height / 2)
    shadow_x = x + shadow_offset[0]
    shadow_y = y + shadow_offset[1]
    draw.multiline_text(
        (shadow_x, shadow_y),
        text,
        fill=shadow_color,
        font=font,
        spacing=line_spacing,
        align="center",
    )
    draw.multiline_text(
        (x, y),
        text,
        fill=text_color,
        font=font,
        spacing=line_spacing,
        align="center",
    )


def build_text_regions(
    draw: ImageDraw.ImageDraw,
    image_size: tuple[int, int],
    font_path: str | Path | None,
    top_text: str,
    middle_text: str,
    bottom_text: str,
    top_font_size: int,
    middle_font_size: int,
    bottom_font_size: int,
    line_spacing: int,
    margin_x: int,
    margin_y: int,
) -> list[TextRegion]:
    image_width, image_height = image_size
    max_text_width = max(1, image_width - (margin_x * 2))
    available_height = max(1, image_height - (margin_y * 2))
    text_values = {
        "top": top_text,
        "middle": middle_text,
        "bottom": bottom_text,
    }
    font_sizes = {
        "top": top_font_size,
        "middle": middle_font_size,
        "bottom": bottom_font_size,
    }
    regions: list[TextRegion] = []

    for name, center_ratio, height_ratio in TEXT_REGION_SPECS:
        text_value = text_values[name]
        if not text_value:
            continue

        region_font_size = max(MIN_FONT_SIZE, font_sizes[name])
        region_max_height = max(1, int(round(available_height * height_ratio)))
        region_font, lines = fit_text_region(
            draw,
            text_value,
            font_path,
            region_font_size,
            line_spacing,
            max_text_width,
            region_max_height,
        )
        regions.append(
            TextRegion(
                center_y=margin_y + (available_height * center_ratio),
                font=region_font,
                lines=lines,
            )
        )

    return regions