from pathlib import Path

from PIL import Image, ImageDraw

from nametags.tag.fonts import load_font
from nametags.tag.footer_logos import load_trimmed_logo
from nametags.tag.render_config import MIN_FONT_SIZE, FontLike, TextBoxSpec, TextRegion


def measure_text(
    draw: ImageDraw.ImageDraw, text: str, font: FontLike
) -> tuple[int, int]:
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


def text_block_bounds(
    draw: ImageDraw.ImageDraw,
    lines: list[str],
    font: FontLike,
    line_spacing: int,
) -> tuple[int, int, int, int]:
    return draw.multiline_textbbox(
        (0, 0),
        "\n".join(lines),
        font=font,
        spacing=line_spacing,
        align="center",
    )


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
        raise ValueError(
            "Text is too wide to fit on the tag at the configured font size."
        )

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
    line_spacing: int,
    max_text_width: int,
    max_text_height: int,
    max_font_size: int | None = None,
) -> tuple[FontLike, list[str]]:
    smallest_font = load_font(font_path, MIN_FONT_SIZE)
    try:
        smallest_lines = split_text_lines(
            draw,
            text,
            smallest_font,
            line_spacing,
            max_text_width,
            max_text_height,
        )
    except ValueError as exc:
        raise ValueError("Text is too wide to fit in its template box.") from exc

    best_font = smallest_font
    best_lines = smallest_lines
    lower_size = MIN_FONT_SIZE + 1
    upper_size = max(MIN_FONT_SIZE, max_text_height * 2)
    if max_font_size is not None:
        upper_size = min(upper_size, max_font_size)
    while lower_size <= upper_size:
        candidate_size = (lower_size + upper_size) // 2
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
            upper_size = candidate_size - 1
            continue
        best_font = font
        best_lines = lines
        lower_size = candidate_size + 1

    return best_font, best_lines


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    box_left: int,
    box_top: int,
    box_width: int,
    box_height: int,
    lines: list[str],
    font: FontLike,
    text_color: str,
    shadow_color: str,
    shadow_offset: tuple[int, int],
    line_spacing: int,
) -> None:
    text = "\n".join(lines)
    left, top, right, bottom = text_block_bounds(draw, lines, font, line_spacing)
    combined_left = min(left, left + shadow_offset[0])
    combined_top = min(top, top + shadow_offset[1])
    combined_right = max(right, right + shadow_offset[0])
    combined_bottom = max(bottom, bottom + shadow_offset[1])
    x = box_left + ((box_width - (combined_right - combined_left)) / 2) - combined_left
    y = box_top + ((box_height - (combined_bottom - combined_top)) / 2) - combined_top
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


def draw_text_block_with_logo(
    image: Image.Image,
    region: TextRegion,
    logo_path: Path,
    text_color: str,
    shadow_color: str,
    shadow_offset: tuple[int, int],
    line_spacing: int,
) -> None:
    draw = ImageDraw.Draw(image)
    text = "\n".join(region.lines)
    left, top, right, bottom = text_block_bounds(
        draw, region.lines, region.font, line_spacing
    )
    text_width = right - left
    text_height = bottom - top
    logo = load_trimmed_logo(logo_path)
    logo.thumbnail(
        (max(1, region.width // 3), max(1, int(region.height * 1.2))),
        Image.Resampling.LANCZOS,
    )
    gap = max(1, region.width // 40)
    group_width = logo.width + gap + text_width + abs(shadow_offset[0])
    group_left = round(region.left + (region.width - group_width) / 2)
    logo_top = round(region.top + (region.height - logo.height) / 2)
    image.alpha_composite(logo, (group_left, logo_top))
    text_left = group_left + logo.width + gap
    text_top = region.top + (region.height - text_height) // 2 - top
    draw.multiline_text(
        (text_left + shadow_offset[0], text_top + shadow_offset[1]),
        text,
        fill=shadow_color,
        font=region.font,
        spacing=line_spacing,
        align="center",
    )
    draw.multiline_text(
        (text_left, text_top),
        text,
        fill=text_color,
        font=region.font,
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
    line_spacing: int,
    shadow_offset: tuple[int, int],
    text_boxes: tuple[TextBoxSpec, ...],
    middle_max_font_size: int,
    top_logo_path: Path | None = None,
) -> list[TextRegion]:
    image_width, image_height = image_size
    text_values = {
        "top": top_text,
        "middle": middle_text,
        "bottom": bottom_text,
    }
    regions: list[TextRegion] = []

    for name, left_ratio, top_ratio, width_ratio, height_ratio in text_boxes:
        text_value = text_values[name]
        if not text_value:
            continue

        box_left = round(image_width * left_ratio)
        box_top = round(image_height * top_ratio)
        box_width = max(1, (round(image_width * width_ratio)))
        box_height = max(1, (round(image_height * height_ratio)))
        text_width = max(1, box_width - abs(shadow_offset[0]))
        if name == "top" and top_logo_path is not None:
            logo = load_trimmed_logo(top_logo_path)
            logo.thumbnail(
                (max(1, box_width // 3), max(1, int(box_height * 0.8))),
                Image.Resampling.LANCZOS,
            )
            text_width = max(1, text_width - logo.width - max(1, box_width // 40))
        text_height = max(1, box_height - abs(shadow_offset[1]))
        region_font, lines = fit_text_region(
            draw,
            text_value,
            font_path,
            line_spacing,
            text_width,
            text_height,
            middle_max_font_size if name == "middle" else None,
        )
        regions.append(
            TextRegion(
                name=name,
                left=box_left,
                top=box_top,
                width=box_width,
                height=box_height,
                font=region_font,
                lines=lines,
            )
        )

    return regions
