# ui/components/pillow_utils.py
"""Pillow helpers for anti-aliased rounded cards and soft shadows."""

from PIL import Image, ImageDraw, ImageFilter


def make_rounded_card(
    width: int,
    height: int,
    radius: int,
    bg: str,
    border_color: str | None,
    shadow: bool = True,
) -> tuple[Image.Image, int]:
    """Render a rounded card and return the image with its content inset."""
    width, height = max(1, width), max(1, height)
    pad = 18 if shadow else 0
    scale = 3
    canvas_size = ((width + 2 * pad) * scale, (height + 2 * pad) * scale)
    if shadow:
        shadow_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_layer)
        shadow_draw.rounded_rectangle(
            (
                pad * scale,
                pad * scale + 4 * scale,
                (pad + width) * scale - 1,
                (pad + height) * scale + 4 * scale - 1,
            ),
            radius=radius * scale,
            fill=(0, 0, 0, 115),
        )
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(16 * scale))
    else:
        shadow_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))

    card_layer = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(card_layer)
    box = (pad * scale, pad * scale, (pad + width) * scale - 1, (pad + height) * scale - 1)
    draw.rounded_rectangle(box, radius=radius * scale, fill=bg)
    if border_color:
        draw.rounded_rectangle(box, radius=radius * scale, outline=border_color, width=scale)
    combined = Image.alpha_composite(shadow_layer, card_layer)
    combined = combined.resize((width + 2 * pad, height + 2 * pad), Image.Resampling.LANCZOS)
    return combined, pad
