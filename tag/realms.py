from __future__ import annotations

import colorsys
import re
from collections.abc import Mapping

from PIL import Image

from .top_image import image_filename_from_text


REALM_COLORS = {
    "civil": "#751fbb",
    "computer": "#c99525",
    "renewable": "#27ae60",
    "software": "#ce3737",
    "mechanical": "#2a6cce",
    "other": "#28C2B5",
    "industry": "#FFD700",
    "uones": "#D62828",
    "nuches": "#2E8B57",
    "nuwie": "#7B2CBF",
    "ausimm": "#1666B1",
}

REALM_TYPES = {
    "uones": "uones",
    "nuches": "nuches",
    "nuwie": "nuwie",
    "ausimm": "ausimm",
    "industry": "industry",
}

_REALM_KEYWORDS = (
    ("software", ("software",)),
    ("civil", ("civil", "environmental", "surveying")),
    ("computer", ("computer", "electrical", "medical")),
    ("renewable", ("renewable", "chemical")),
    ("mechanical", ("mechanical", "mechatronics", "aerospace")),
)


def classify_realm(
    top_text: str,
    bottom_text: str,
    realm_type: str | None = None,
) -> str:
    if realm_type in REALM_TYPES:
        return REALM_TYPES[realm_type]
    if image_filename_from_text(top_text) is not None:
        return "industry"

    classification_text = bottom_text or top_text
    normalized_text = " ".join(classification_text.casefold().split())
    computer_science_matches = list(
        re.finditer(r"\bcomputer\s+science\b", normalized_text)
    )
    matches = [(match.start(), "other") for match in computer_science_matches]
    for realm, keywords in _REALM_KEYWORDS:
        for keyword in keywords:
            for match in re.finditer(rf"\b{re.escape(keyword)}\b", normalized_text):
                if keyword == "computer" and any(
                    phrase.start() <= match.start() < phrase.end()
                    for phrase in computer_science_matches
                ):
                    continue
                matches.append((match.start(), realm))
    return min(matches, default=(0, "other"), key=lambda match: match[0])[1]


def apply_realm_hue(image: Image.Image, color: str) -> None:
    split_y = image.height // 2
    if split_y == 0:
        return

    red, green, blue = (int(color[index : index + 2], 16) / 255 for index in (1, 3, 5))
    target_hue, _saturation, _value = colorsys.rgb_to_hsv(red, green, blue)
    upper_half = image.crop((0, 0, image.width, split_y))
    alpha = upper_half.getchannel("A")
    hue, saturation, value = upper_half.convert("RGB").convert("HSV").split()
    hue = Image.new("L", hue.size, round(target_hue * 255))
    recolored = Image.merge("HSV", (hue, saturation, value)).convert("RGBA")
    recolored.putalpha(alpha)
    image.alpha_composite(recolored, (0, 0))


def realm_color(
    top_text: str,
    bottom_text: str,
    colors: Mapping[str, str] = REALM_COLORS,
    realm_type: str | None = None,
) -> str:
    return colors[classify_realm(top_text, bottom_text, realm_type)]
