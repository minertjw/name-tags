import math

from .render_config import DEFAULT_SHADOW_OFFSET


def strip_wrapping_quotes(text: str) -> str:
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


def normalize_text(text: str) -> str:
    return strip_wrapping_quotes(text).upper()


def cm_to_pixels(cm_value: float, dpi: float) -> int:
    return max(0, int(round((cm_value / 2.54) * dpi)))


def shadow_offset_from_angle(angle_degrees: float, distance: float) -> tuple[int, int]:
    radians = math.radians(angle_degrees)
    return (
        int(round(math.cos(radians) * distance)),
        int(round(math.sin(radians) * distance)),
    )


def default_shadow_distance() -> float:
    return round(math.hypot(*DEFAULT_SHADOW_OFFSET), 2)