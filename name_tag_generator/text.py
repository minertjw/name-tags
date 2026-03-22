from pathlib import Path

from PIL import Image, ImageDraw

from .normalization import cm_to_pixels, default_shadow_distance, normalize_text, shadow_offset_from_angle
from .render_config import (
	DEFAULT_DPI,
	DEFAULT_FONT_SIZE,
	DEFAULT_LINE_SPACING,
	DEFAULT_MARGIN_CM,
	DEFAULT_SECONDARY_FONT_SCALE,
	DEFAULT_SHADOW_ANGLE,
	DEFAULT_SHADOW_COLOR,
	DEFAULT_TEXT_COLOR,
	MIN_FONT_SIZE,
)
from .text_layout import build_text_regions, draw_text_block
from .top_image import draw_top_image, resolve_image_filename


DEFAULT_SHADOW_DISTANCE = default_shadow_distance()


def create_tag(
	template_path: str | Path,
	text: str = "",
	output_path: str | Path = "./unknown.png",
	*,
	top_text: str = "",
	middle_text: str = "",
	bottom_text: str = "",
	font_path: str | Path | None = None,
	text_color: str = DEFAULT_TEXT_COLOR,
	shadow_color: str = DEFAULT_SHADOW_COLOR,
	shadow_angle: float = DEFAULT_SHADOW_ANGLE,
	shadow_distance: float = DEFAULT_SHADOW_DISTANCE,
	margin_cm: float = DEFAULT_MARGIN_CM,
	bottom_horizontal_margin_cm: float | None = None,
	font_size: int = DEFAULT_FONT_SIZE,
	top_font_size: int | None = None,
	middle_font_size: int | None = None,
	bottom_font_size: int | None = None,
	secondary_font_scale: float = DEFAULT_SECONDARY_FONT_SCALE,
	line_spacing: int = DEFAULT_LINE_SPACING,
) -> Path:
	top_image_path = resolve_image_filename(top_text)
	top_text = "" if top_image_path is not None else normalize_text(top_text)
	middle_text = normalize_text(middle_text or text)
	bottom_text = normalize_text(bottom_text)
	template = Path(template_path)
	output = Path(output_path)

	if not template.is_file():
		raise FileNotFoundError(f"Template image not found: {template}")
	if top_image_path is None and not any((top_text, middle_text, bottom_text)):
		raise ValueError("At least one text field must not be empty.")
	resolved_top_font_size = top_font_size or max(
		MIN_FONT_SIZE,
		int(round(font_size * DEFAULT_SECONDARY_FONT_SCALE)),
	)
	resolved_middle_font_size = middle_font_size or font_size
	resolved_bottom_font_size = bottom_font_size or max(
		MIN_FONT_SIZE,
		int(round(font_size * DEFAULT_SECONDARY_FONT_SCALE)),
	)
	resolved_bottom_horizontal_margin_cm = (
		margin_cm if bottom_horizontal_margin_cm is None else bottom_horizontal_margin_cm
	)
	if margin_cm < 0:
		raise ValueError("Margin must not be negative.")
	if resolved_bottom_horizontal_margin_cm < 0:
		raise ValueError("Bottom horizontal margin must not be negative.")
	if resolved_top_font_size <= 0 or resolved_middle_font_size <= 0 or resolved_bottom_font_size <= 0:
		raise ValueError("Font sizes must be greater than zero.")
	if secondary_font_scale <= 0:
		raise ValueError("Secondary font scale must be greater than zero.")
	if line_spacing < 0:
		raise ValueError("Line spacing must not be negative.")
	if shadow_distance < 0:
		raise ValueError("Shadow distance must not be negative.")

	with Image.open(template) as source_image:
		dpi_info = source_image.info.get("dpi", (DEFAULT_DPI, DEFAULT_DPI))
		image = source_image.convert("RGBA")

	dpi_x = float(dpi_info[0]) if dpi_info else float(DEFAULT_DPI)
	dpi_y = float(dpi_info[1]) if len(dpi_info) > 1 else dpi_x
	margin_x = cm_to_pixels(margin_cm, dpi_x)
	margin_y = cm_to_pixels(margin_cm, dpi_y)
	bottom_margin_x = cm_to_pixels(resolved_bottom_horizontal_margin_cm, dpi_x)
	shadow_offset = shadow_offset_from_angle(shadow_angle, shadow_distance)

	draw = ImageDraw.Draw(image)
	if top_image_path is not None:
		draw_top_image(image, top_image_path, margin_x, margin_y)
	regions = build_text_regions(
		draw,
		image.size,
		font_path,
		top_text,
		middle_text,
		bottom_text,
		resolved_top_font_size,
		resolved_middle_font_size,
		resolved_bottom_font_size,
		line_spacing,
		margin_x,
		margin_y,
		bottom_margin_x,
	)
	for region in regions:
		draw_text_block(
			draw,
			image.width,
			region.center_y,
			region.lines,
			region.font,
			text_color,
			shadow_color,
			shadow_offset,
			region.margin_x,
			line_spacing,
		)

	output.parent.mkdir(parents=True, exist_ok=True)
	image.save(output)
	return output
