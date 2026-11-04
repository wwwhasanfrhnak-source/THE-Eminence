"""ساخت icon.png از splash.png یا مستقیم."""
from pathlib import Path
from PIL import Image, ImageDraw

ASSETS = Path(__file__).parent / "assets"
ICON_PNG = ASSETS / "icon.png"


def make_simple_icon():
    """ساخت آیکون ⚡ ساده."""
    size = 512
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # دایره بنفش
    margin = 40
    draw.ellipse(
        (margin, margin, size - margin, size - margin),
        fill=(124, 58, 237, 255),
        outline=(6, 182, 212, 255),
        width=8,
    )

    # رعد ⚡ سفید
    bolt = [
        (290, 120),
        (180, 280),
        (240, 280),
        (190, 400),
        (320, 240),
        (260, 240),
        (310, 120),
    ]
    draw.polygon(bolt, fill=(255, 255, 255, 255))

    img.save(ICON_PNG, "PNG")
    print(f"✅ icon.png ساخته شد: {ICON_PNG}")


if __name__ == "__main__":
    make_simple_icon()