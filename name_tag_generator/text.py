from pathlib import Path

from PIL import Image, ImageDraw

from .normalization import cm_to_pixels, normalize_text, shadow_offset_from_angle
from .render_config import (
	DEFAULT_DPI,
	DEFAULT_LINE_SPACING,
	DEFAULT_MARGIN_CM,
	DEFAULT_MIDDLE_MAX_FONT_SIZE,
	DEFAULT_SHADOW_ANGLE,
	DEFAULT_SHADOW_COLOR,
	DEFAULT_SHADOW_DISTANCE,
	DEFAULT_TEXT_COLOR,
	MIN_FONT_SIZE,
	TEXT_BOX_SPECS,
	TextBoxSpec,
)
from .text_layout import build_text_regions, draw_text_block
from .top_image import draw_top_image, resolve_image_filename

def create_tag(
	template_path: str | Path,
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
	line_spacing: int = DEFAULT_LINE_SPACING,
	text_boxes: tuple[TextBoxSpec, ...] = TEXT_BOX_SPECS,
	middle_max_font_size: int = DEFAULT_MIDDLE_MAX_FONT_SIZE,
) -> Path:
	top_image_path = resolve_image_filename(top_text)
	top_text = "" if top_image_path is not None else normalize_text(top_text)
	middle_text = normalize_text(middle_text)
	bottom_text = normalize_text(bottom_text)
	template = Path(template_path)
	output = Path(output_path)

	if not template.is_file():
		raise FileNotFoundError(f"Template image not found: {template}")
	if top_image_path is None and not any((top_text, middle_text, bottom_text)):
		raise ValueError("At least one text field must not be empty.")
	if margin_cm < 0:
		raise ValueError("Margin must not be negative.")
	if line_spacing < 0:
		raise ValueError("Line spacing must not be negative.")
	if shadow_distance < 0:
		raise ValueError("Shadow distance must not be negative.")
	if middle_max_font_size < MIN_FONT_SIZE:
		raise ValueError(f"Middle maximum font size must be at least {MIN_FONT_SIZE}.")

	with Image.open(template) as source_image:
		dpi_info = source_image.info.get("dpi", (DEFAULT_DPI, DEFAULT_DPI))
		image = source_image.convert("RGBA")

	dpi_x = float(dpi_info[0]) if dpi_info else float(DEFAULT_DPI)
	dpi_y = float(dpi_info[1]) if len(dpi_info) > 1 else dpi_x
	margin_x = cm_to_pixels(margin_cm, dpi_x)
	margin_y = cm_to_pixels(margin_cm, dpi_y)
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
		line_spacing,
		shadow_offset,
		text_boxes,
		middle_max_font_size,
	)
	for region in regions:
		draw_text_block(
			draw,
			region.left,
			region.top,
			region.width,
			region.height,
			region.lines,
			region.font,
			text_color,
			shadow_color,
			shadow_offset,
			line_spacing,
		)

	output.parent.mkdir(parents=True, exist_ok=True)
	image.save(output)
	return output
