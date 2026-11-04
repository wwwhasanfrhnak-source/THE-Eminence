"""تبدیل PNG به ICO برای ویندوز."""
from pathlib import Path
from PIL import Image

ASSETS = Path(__file__).parent / "assets"
ASSETS.mkdir(exist_ok=True)

PNG_PATH = ASSETS / "icon.png"
ICO_PATH = ASSETS / "icon.ico"


def convert():
    if not PNG_PATH.exists():
        print(f"❌ فایل پیدا نشد: {PNG_PATH}")
        print("   اول icon.png رو بساز یا کپی کن")
        return

    img = Image.open(PNG_PATH).convert("RGBA")

    size = max(img.size)
    square = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    square.paste(img, ((size - img.width) // 2,
                        (size - img.height) // 2))
    square = square.resize((256, 256), Image.LANCZOS)

    square.save(
        ICO_PATH, format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48),
               (64, 64), (128, 128), (256, 256)],
    )
    print(f"✅ ICO ساخته شد: {ICO_PATH}")
    print(f"   حجم: {ICO_PATH.stat().st_size} بایت")


if __name__ == "__main__":
    convert()