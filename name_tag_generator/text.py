from pathlib import Path
from dataclasses import dataclass
import math

from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parent.parent
IMAGES_DIR = BASE_DIR / "images"
ASPECT_RATIO = 19 / 12
DEFAULT_TEXT_COLOR = "#000000"
DEFAULT_SHADOW_COLOR = "#c00000"
DEFAULT_SHADOW_OFFSET = (4, 4)
DEFAULT_SHADOW_ANGLE = 45.0
DEFAULT_SHADOW_DISTANCE = round(math.hypot(*DEFAULT_SHADOW_OFFSET), 2)
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
FontLike = ImageFont.ImageFont | ImageFont.FreeTypeFont


@dataclass(frozen=True)
class TextRegion:
	center_y: float
	font: FontLike
	lines: list[str]


TEXT_REGION_SPECS = (
	("top", 0.075, 0.16),
	("middle", 0.45, 0.26),
	("bottom", 0.9, 0.16),
)


def _load_font(font_path: str | Path | None, size: int) -> FontLike:
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


def _measure_text(draw: ImageDraw.ImageDraw, text: str, font: FontLike) -> tuple[int, int]:
	left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
	return int(right - left), int(bottom - top)


def _measure_text_block(
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


def _cm_to_pixels(cm_value: float, dpi: float) -> int:
	return max(0, int(round((cm_value / 2.54) * dpi)))


def _strip_wrapping_quotes(text: str) -> str:
	normalized = " ".join(text.split())
	quote_pairs = {
		'"': '"',
		"'": "'",
		"“": "”",
		"‘": "’",
	}
	while len(normalized) >= 2:
		opening_quote = normalized[0]
		closing_quote = normalized[-1]
		expected_closing_quote = quote_pairs.get(opening_quote)
		if expected_closing_quote != closing_quote:
			break
		normalized = normalized[1:-1].strip()
	return normalized


def _normalize_text(text: str) -> str:
	return _strip_wrapping_quotes(text).upper()


def _resolve_image_filename(text: str) -> Path | None:
	candidate_name = Path(_strip_wrapping_quotes(text)).name
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


def _shadow_offset_from_angle(angle_degrees: float, distance: float) -> tuple[int, int]:
	radians = math.radians(angle_degrees)
	return (
		int(round(math.cos(radians) * distance)),
		int(round(math.sin(radians) * distance)),
	)


def _split_text_lines(
	draw: ImageDraw.ImageDraw,
	text: str,
	font: FontLike,
	line_spacing: int,
	max_text_width: int,
	max_text_height: int,
	max_lines: int = 2,
	) -> list[str]:
	text_width, text_height = _measure_text(draw, text, font)
	if text_width <= max_text_width and text_height <= max_text_height:
		return [text]

	words = text.split()
	if max_lines < 2 or len(words) < 2:
		raise ValueError("Text is too wide to fit on the tag at the configured font size.")

	best_lines: list[str] | None = None
	best_width: int | None = None
	for index in range(1, len(words)):
		candidate_lines = [" ".join(words[:index]), " ".join(words[index:])]
		block_width, block_height = _measure_text_block(
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


def _fit_text_region(
	draw: ImageDraw.ImageDraw,
	text: str,
	font_path: str | Path | None,
	starting_font_size: int,
	line_spacing: int,
	max_text_width: int,
	max_text_height: int,
) -> tuple[FontLike, list[str]]:
	for candidate_size in range(starting_font_size, MIN_FONT_SIZE - 1, -2):
		font = _load_font(font_path, candidate_size)
		try:
			lines = _split_text_lines(
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


def _draw_text_block(
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
	text_width, text_height = _measure_text_block(draw, lines, font, line_spacing)
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


def _draw_top_image(
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


def _build_text_regions(
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
		region_font, lines = _fit_text_region(
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
	font_size: int = DEFAULT_FONT_SIZE,
	top_font_size: int | None = None,
	middle_font_size: int | None = None,
	bottom_font_size: int | None = None,
	secondary_font_scale: float = DEFAULT_SECONDARY_FONT_SCALE,
	line_spacing: int = DEFAULT_LINE_SPACING,
) -> Path:
	top_image_path = _resolve_image_filename(top_text)
	top_text = "" if top_image_path is not None else _normalize_text(top_text)
	middle_text = _normalize_text(middle_text or text)
	bottom_text = _normalize_text(bottom_text)
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
	if margin_cm < 0:
		raise ValueError("Margin must not be negative.")
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
	margin_x = _cm_to_pixels(margin_cm, dpi_x)
	margin_y = _cm_to_pixels(margin_cm, dpi_y)
	shadow_offset = _shadow_offset_from_angle(shadow_angle, shadow_distance)

	draw = ImageDraw.Draw(image)
	if top_image_path is not None:
		_draw_top_image(image, top_image_path, margin_x, margin_y)
	regions = _build_text_regions(
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
	)
	for region in regions:
		_draw_text_block(
			draw,
			image.width,
			region.center_y,
			region.lines,
			region.font,
			text_color,
			shadow_color,
			shadow_offset,
			margin_x,
			line_spacing,
		)

	output.parent.mkdir(parents=True, exist_ok=True)
	image.save(output)
	return output
