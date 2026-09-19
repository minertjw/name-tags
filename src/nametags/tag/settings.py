from dataclasses import dataclass
import json
import re
from typing import Mapping

from nametags.tag.realms import REALM_COLORS
from nametags.tag.render_config import DEFAULT_MIDDLE_MAX_FONT_SIZE, TEXT_BOX_SPECS, TextBoxSpec

MIN_BOX_SIZE = 0.03




@dataclass(frozen=True)
class RenderSettings:
    shadow_angle: float
    shadow_distance: float
    middle_max_font_size: int
    text_boxes: tuple[TextBoxSpec, ...]
    realm_colors: dict[str, str]

    def create_tag_kwargs(self) -> dict[str, object]:
        return {
            "shadow_angle": self.shadow_angle,
            "shadow_distance": self.shadow_distance,
            "middle_max_font_size": self.middle_max_font_size,
            "text_boxes": self.text_boxes,
            "realm_colors": self.realm_colors,
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

    text_boxes = _parse_text_boxes(values.get("text_boxes"))
    realm_colors = {
        realm: _parse_color(values.get(f"realm_color_{realm}"), default, realm)
        for realm, default in REALM_COLORS.items()
    }

    return RenderSettings(
        shadow_angle=parse_float("shadow_angle", -180, 180),
        shadow_distance=parse_float("shadow_distance", 0, 50),
        middle_max_font_size=parse_int("middle_max_font_size", 12, 500),
        text_boxes=text_boxes,
        realm_colors=realm_colors,
    )


def _parse_color(raw_value: str | None, default: str, realm: str) -> str:
    color = default if raw_value is None else raw_value
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", color):
        raise ValueError(f"{realm.title()} color must use the format #RRGGBB.")
    return color.lower()


def _parse_text_boxes(raw_value: str | None) -> tuple[TextBoxSpec, ...]:
    if raw_value is None or not raw_value.strip():
        return TEXT_BOX_SPECS
    try:
        raw_boxes = json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise ValueError("Text box settings are invalid.") from exc
    if not isinstance(raw_boxes, list) or len(raw_boxes) != len(TEXT_BOX_SPECS):
        raise ValueError("Text box settings must define top, middle, and bottom boxes.")

    boxes: list[TextBoxSpec] = []
    expected_names = [box[0] for box in TEXT_BOX_SPECS]
    for raw_box, expected_name in zip(raw_boxes, expected_names):
        if not isinstance(raw_box, dict) or raw_box.get("name") != expected_name:
            raise ValueError("Text boxes must be ordered top, middle, and bottom.")
        try:
            left = float(raw_box["left"])
            top = float(raw_box["top"])
            width = float(raw_box["width"])
            height = float(raw_box["height"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Text box coordinates must be numbers.") from exc
        if width < MIN_BOX_SIZE or height < MIN_BOX_SIZE:
            raise ValueError("Text boxes must be at least 3% wide and high.")
        if left < 0 or top < 0 or left + width > 1 or top + height > 1:
            raise ValueError("Text boxes must stay within the template.")
        boxes.append((expected_name, left, top, width, height))
    return tuple(boxes)


def get_default_preview_settings() -> dict[str, object]:
    return {
        "shadow_angle": 45,
        "shadow_distance": 6,
        "middle_max_font_size": DEFAULT_MIDDLE_MAX_FONT_SIZE,
        "realm_colors": REALM_COLORS,
    }