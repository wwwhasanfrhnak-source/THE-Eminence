"""ساخت پروفایل گرد."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageTk, ImageFont

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
ASSETS_DIR.mkdir(exist_ok=True)

# پالت رنگ برای پروفایل‌های پیش‌فرض
COLORS = [
    (124, 58, 237),   # بنفش
    (6, 182, 212),    # فیروزه‌ای
    (16, 185, 129),   # سبز
    (245, 158, 11),   # نارنجی
    (239, 68, 68),    # قرمز
    (236, 72, 153),   # صورتی
]


def make_circular(image_path, size: int = 50):
    """عکس رو گرد می‌کنه. اگه نشد، None."""
    try:
        img = Image.open(image_path).convert("RGBA")
    except Exception:
        return None
    img = img.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size, size), fill=255)
    img.putalpha(mask)
    return ImageTk.PhotoImage(img)


def make_placeholder(name: str, size: int = 50):
    """دایره رنگی با حرف اول اسم."""
    # رنگ بر اساس hash اسم
    idx = sum(ord(c) for c in (name or "?")) % len(COLORS)
    bg = COLORS[idx]

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, size, size), fill=bg)

    # حرف اول
    letter = (name or "?")[0]
    try:
        font = ImageFont.truetype("arial.ttf", int(size * 0.5))
    except Exception:
        font = ImageFont.load_default()

    try:
        bbox = draw.textbbox((0, 0), letter, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        draw.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1]),
                  letter, fill="white", font=font)
    except Exception:
        draw.text((size * 0.35, size * 0.3), letter, fill="white")

    return ImageTk.PhotoImage(img)


def get_avatar(user, size: int = 50):
    """
    پروفایل کاربر رو برمی‌گردونه (PhotoImage).
    اول تلاش می‌کنه عکس واقعی، اگه نبود placeholder.
    """
    name = ""
    path = None
    if user is not None:
        try:
            name = user["full_name"] or user["username"] or ""
        except Exception:
            pass
        try:
            keys = user.keys()
            if "avatar_path" in keys:
                path = user["avatar_path"]
        except Exception:
            path = None

    if path:
        img = make_circular(path, size)
        if img:
            return img

    return make_placeholder(name or "?", size)