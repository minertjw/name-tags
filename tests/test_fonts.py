from PIL import ImageFont

from nametags.paths import BASE_DIR
from nametags.tag.fonts import get_font_options, load_font


def test_font_discovery():
    fonts = get_font_options()

    expected_bundled_fonts = ["Norwester"]
    expected_system_fonts = ["Calibri", "Arial", "Segoe UI"]

    all_fonts = expected_bundled_fonts + expected_system_fonts

    for font in all_fonts:
        font_path = next(
            (path for label, path in fonts if label.lower() == font.lower())
        )
        assert font_path is not None


def test_load_font():
    # Good font
    norwester_path = BASE_DIR / "assets" / "fonts" / "norwester.otf"

    font = load_font(norwester_path, 12)

    assert isinstance(font, ImageFont.FreeTypeFont)

    # Bad font
    bad_path = BASE_DIR / "assets" / "fonts" / "noexistent.ttf"

    font = load_font(bad_path, 12)
    pil_default = ImageFont.load_default()

    assert isinstance(font, ImageFont.FreeTypeFont)
    assert isinstance(pil_default, ImageFont.FreeTypeFont)
    assert font.font_bytes == pil_default.font_bytes
