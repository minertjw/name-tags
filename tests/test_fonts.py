from nametags.tag.fonts import get_font_options


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
