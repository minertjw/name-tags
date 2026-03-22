from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = BASE_DIR / "preview_output.png"
DEFAULT_SHADOW_COLOR = "#c00000"
DEFAULT_TOP_FONT_SIZE = 75
DEFAULT_MIDDLE_FONT_SIZE = 120
DEFAULT_BOTTOM_FONT_SIZE = 75


def get_default_preview_settings() -> dict[str, object]:
    return {
        "template_path": "",
        "output_path": str(DEFAULT_OUTPUT),
        "font_path": "",
        "top_text": "UNDERGRADUATE",
        "middle_text": "JOHN SMITH",
        "bottom_text": "MECHANICAL ENGINEERING",
        "top_font_size": DEFAULT_TOP_FONT_SIZE,
        "middle_font_size": DEFAULT_MIDDLE_FONT_SIZE,
        "bottom_font_size": DEFAULT_BOTTOM_FONT_SIZE,
        "shadow_color": DEFAULT_SHADOW_COLOR,
        "shadow_angle": 45,
        "shadow_distance": 6,
    }