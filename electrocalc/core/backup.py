"""پشتیبان‌گیری و بازیابی."""

import json
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

from electrocalc.utils.logger import log

# مسیرهای پروژه
PROJECT_DIR = Path(__file__).resolve().parents[2]
DB_FILE = PROJECT_DIR / "electrocalc.db"
UPLOADS_DIR = PROJECT_DIR / "uploads"
ASSETS_DIR = PROJECT_DIR / "assets"
BACKUPS_DIR = PROJECT_DIR / "backups"
BACKUPS_DIR.mkdir(exist_ok=True)


def _timestamp():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def create_backup(description=""):
    """
    ساخت پشتیبان کامل.
    خروجی: مسیر فایل ZIP
    """
    name = f"backup_{_timestamp()}.zip"
    dest = BACKUPS_DIR / name

    metadata = {
        "created_at": datetime.now().isoformat(),
        "description": description,
        "has_db": DB_FILE.exists(),
        "has_uploads": UPLOADS_DIR.exists(),
        "has_assets": ASSETS_DIR.exists(),
    }

    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        # دیتابیس
        if DB_FILE.exists():
            zf.write(DB_FILE, "electrocalc.db")

        # پوشه uploads
        if UPLOADS_DIR.exists():
            for f in UPLOADS_DIR.rglob("*"):
                if f.is_file():
                    arcname = f.relative_to(PROJECT_DIR)
                    zf.write(f, str(arcname))

        # پوشه assets
        if ASSETS_DIR.exists():
            for f in ASSETS_DIR.rglob("*"):
                if f.is_file():
                    arcname = f.relative_to(PROJECT_DIR)
                    zf.write(f, str(arcname))

        # metadata
        zf.writestr("metadata.json",
                     json.dumps(metadata, ensure_ascii=False, indent=2))

    log.info(f"پشتیبان ساخته شد: {dest}")
    return str(dest)


def list_backups():
    """لیست همه پشتیبان‌ها."""
    result = []
    for f in sorted(BACKUPS_DIR.glob("backup_*.zip"), reverse=True):
        try:
            size = f.stat().st_size
            # خواندن metadata
            with zipfile.ZipFile(f, "r") as zf:
                if "metadata.json" in zf.namelist():
                    meta = json.loads(zf.read("metadata.json").decode("utf-8"))
                else:
                    meta = {}
            result.append({
                "path": str(f),
                "name": f.name,
                "size": size,
                "size_str": _format_size(size),
                "created_at": meta.get("created_at", ""),
                "description": meta.get("description", ""),
            })
        except Exception as e:
            log.error(f"خطا در خواندن {f}: {e}")
    return result


def _format_size(size):
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f} KB"
    elif size < 1024 * 1024 * 1024:
        return f"{size/(1024*1024):.1f} MB"
    return f"{size/(1024*1024*1024):.2f} GB"


def restore_backup(backup_path, auto_backup=True):
    """
    بازیابی از فایل پشتیبان.
    قبل از بازیابی، یه پشتیبان از وضعیت فعلی می‌گیره.
    """
    src = Path(backup_path)
    if not src.exists():
        raise ValueError("فایل پشتیبان پیدا نشد.")

    # پشتیبان از وضعیت فعلی
    if auto_backup:
        create_backup(description="auto-backup قبل از بازیابی")

    # استخراج
    with zipfile.ZipFile(src, "r") as zf:
        # دیتابیس
        if "electrocalc.db" in zf.namelist():
            # بستن اتصال‌ها (مهم)
            import gc
            gc.collect()
            zf.extract("electrocalc.db", PROJECT_DIR)

        # uploads
        for name in zf.namelist():
            if name.startswith("uploads/") or name.startswith("assets/"):
                zf.extract(name, PROJECT_DIR)

    log.info(f"بازیابی انجام شد از: {src}")
    return True


def delete_backup(backup_path):
    """حذف فایل پشتیبان."""
    p = Path(backup_path)
    if p.exists():
        p.unlink()
        return True
    return False


def get_backup_size_total():
    """مجموع حجم همه پشتیبان‌ها."""
    total = 0
    for f in BACKUPS_DIR.glob("backup_*.zip"):
        total += f.stat().st_size
    return total