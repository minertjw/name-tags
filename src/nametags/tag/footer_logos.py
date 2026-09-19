from pathlib import Path

from PIL import Image, ImageChops


SOCIETY_LOGO_DIR = Path(__file__).resolve().parent.parent / "assets" / "societies"
SOCIETY_LOGO_FILENAMES = ("UONES.png", "NUWIE.png", "AusIMM.png", "NUChES.png", )
FOOTER_HEIGHT_RATIO = 0.25
FOOTER_SIDE_MARGIN_RATIO = 0.025
FOOTER_GAP_RATIO = 0.015
FOOTER_BOTTOM_MARGIN_RATIO = 0.015
# Per-logo (horizontal, vertical) position adjustments as image-size ratios.
# Positive x moves right; positive y moves down.
FOOTER_LOGO_OFFSETS = {
    "UONES.png": (-0.04, -0.02),
    "NUWIE.png": (-0.05, -0.034),
    "AusIMM.png": (0.0, -0.09),
    "NUChES.png": (0.0, -0.02),
}


def draw_footer_logos(image: Image.Image) -> None:
    logo_paths = [SOCIETY_LOGO_DIR / filename for filename in SOCIETY_LOGO_FILENAMES]
    missing = [path.name for path in logo_paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Footer logo not found: {', '.join(missing)}")

    side_margin = max(1, round(image.width * FOOTER_SIDE_MARGIN_RATIO))
    gap = max(1, round(image.width * FOOTER_GAP_RATIO))
    bottom_margin = max(1, round(image.height * FOOTER_BOTTOM_MARGIN_RATIO))
    max_height = max(1, round(image.height * FOOTER_HEIGHT_RATIO))
    available_width = image.width - (side_margin * 2) - (gap * (len(logo_paths) - 1))
    cell_width = max(1, available_width // len(logo_paths))

    for index, logo_path in enumerate(logo_paths):
        logo = load_trimmed_logo(logo_path)
        logo.thumbnail((cell_width, max_height), Image.Resampling.LANCZOS)
        cell_left = side_margin + index * (cell_width + gap)
        left = cell_left + (cell_width - logo.width) // 2
        top = image.height - bottom_margin - logo.height
        offset_x, offset_y = FOOTER_LOGO_OFFSETS.get(logo_path.name, (0.0, 0.0))
        left += round(image.width * offset_x)
        top += round(image.height * offset_y)
        image.alpha_composite(logo, (left, top))


def load_trimmed_logo(logo_path: Path) -> Image.Image:
    with Image.open(logo_path) as source:
        logo = source.convert("RGBA")

    alpha = logo.getchannel("A")
    corners = (
        logo.getpixel((0, 0)),
        logo.getpixel((logo.width - 1, 0)),
        logo.getpixel((0, logo.height - 1)),
        logo.getpixel((logo.width - 1, logo.height - 1)),
    )
    if alpha.getextrema() == (255, 255) and all(
        min(red, green, blue) >= 250 for red, green, blue, _alpha in corners
    ):
        red, green, blue, _alpha = logo.split()
        lightest_background_distance = ImageChops.invert(
            ImageChops.darker(ImageChops.darker(red, green), blue)
        )
        alpha = lightest_background_distance.point(
            lambda value: min(255, max(0, (value - 2) * 4))
        )
        logo.putalpha(alpha)

    visible_bounds = logo.getchannel("A").getbbox()
    if visible_bounds is None:
        raise ValueError(f"Footer logo has no visible pixels: {logo_path.name}")
    return logo.crop(visible_bounds)