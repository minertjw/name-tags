from dataclasses import dataclass
import re
from typing import Mapping

DEFAULT_SHADOW_COLOR = "#c00000"
DEFAULT_TOP_FONT_SIZE = 75
DEFAULT_MIDDLE_FONT_SIZE = 120
DEFAULT_BOTTOM_FONT_SIZE = 75
DEFAULT_BOTTOM_HORIZONTAL_MARGIN_CM = 3.0


@dataclass(frozen=True)
class RenderSettings:
    top_text: str
    middle_text: str
    bottom_text: str
    top_font_size: int
    middle_font_size: int
    bottom_font_size: int
    bottom_horizontal_margin_cm: float
    shadow_color: str
    shadow_angle: float
    shadow_distance: float

    def create_tag_kwargs(self) -> dict[str, object]:
        return {
            "top_text": self.top_text,
            "middle_text": self.middle_text,
            "bottom_text": self.bottom_text,
            "top_font_size": self.top_font_size,
            "middle_font_size": self.middle_font_size,
            "bottom_font_size": self.bottom_font_size,
            "bottom_horizontal_margin_cm": self.bottom_horizontal_margin_cm,
            "shadow_color": self.shadow_color,
            "shadow_angle": self.shadow_angle,
            "shadow_distance": self.shadow_distance,
        }


def parse_render_settings(values: Mapping[str, str]) -> RenderSettings:
    defaults = get_default_preview_settings()

    def parse_int(name: str, minimum: int, maximum: int) -> int:
        raw_value = values.get(name, str(defaults[name]))
        try:
            value = int(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name.replace('_', ' ').title()} must be a whole number.") from exc
        if not minimum <= value <= maximum:
            raise ValueError(
                f"{name.replace('_', ' ').title()} must be between {minimum} and {maximum}."
            )
        return value

    def parse_float(name: str, minimum: float, maximum: float) -> float:
        raw_value = values.get(name, str(defaults[name]))
        try:
            value = float(raw_value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name.replace('_', ' ').title()} must be a number.") from exc
        if not minimum <= value <= maximum:
            raise ValueError(
                f"{name.replace('_', ' ').title()} must be between {minimum:g} and {maximum:g}."
            )
        return value

    shadow_color = values.get("shadow_color", str(defaults["shadow_color"]))
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", shadow_color):
        raise ValueError("Shadow color must use the format #RRGGBB.")

    return RenderSettings(
        top_text=values.get("top_text", str(defaults["top_text"]))[:500],
        middle_text=values.get("middle_text", str(defaults["middle_text"]))[:500],
        bottom_text=values.get("bottom_text", str(defaults["bottom_text"]))[:500],
        top_font_size=parse_int("top_font_size", 12, 180),
        middle_font_size=parse_int("middle_font_size", 12, 180),
        bottom_font_size=parse_int("bottom_font_size", 12, 180),
        bottom_horizontal_margin_cm=parse_float(
            "bottom_horizontal_margin_cm", 0, 10
        ),
        shadow_color=shadow_color,
        shadow_angle=parse_float("shadow_angle", -180, 180),
        shadow_distance=parse_float("shadow_distance", 0, 50),
    )


def get_default_preview_settings() -> dict[str, object]:
    return {
        "top_text": "UNDERGRADUATE",
        "middle_text": "JOHN SMITH",
        "bottom_text": "MECHANICAL ENGINEERING",
        "top_font_size": DEFAULT_TOP_FONT_SIZE,
        "middle_font_size": DEFAULT_MIDDLE_FONT_SIZE,
        "bottom_font_size": DEFAULT_BOTTOM_FONT_SIZE,
        "bottom_horizontal_margin_cm": DEFAULT_BOTTOM_HORIZONTAL_MARGIN_CM,
        "shadow_color": DEFAULT_SHADOW_COLOR,
        "shadow_angle": 45,
        "shadow_distance": 6,
    }