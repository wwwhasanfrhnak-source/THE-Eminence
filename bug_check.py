"""اسکن باگ‌های رایج پروژه ElectroCalc."""

import re
from pathlib import Path

ROOT = Path(__file__).parent / "electrocalc"

print("=" * 60)
print("🐛 اسکن باگ‌های ElectroCalc")
print("=" * 60)

issues = []
warnings = []

# ۱) fetchone().get
print("\n📌 بررسی fetchone().get ...")
for py_file in ROOT.rglob("*.py"):
    try:
        content = py_file.read_text(encoding="utf-8")
    except Exception:
        continue
    if re.search(r"fetchone\(\)\.get", content):
        issues.append(f"❌ {py_file.relative_to(ROOT)}")

# ۲) try/except خالی
print("📌 بررسی try/except خالی...")
for py_file in ROOT.rglob("*.py"):
    try:
        lines = py_file.read_text(encoding="utf-8").splitlines()
    except Exception:
        continue
    for i, line in enumerate(lines):
        if "except" in line and i + 1 < len(lines):
            if lines[i + 1].strip() == "pass":
                warnings.append(f"⚠️  {py_file.name} خط {i+1}")

# ۳) __pycache__
print("📌 بررسی __pycache__...")
cache_dirs = list(ROOT.rglob("__pycache__"))
if cache_dirs:
    warnings.append(f"⚠️  {len(cache_dirs)} پوشه __pycache__")

# ۴) فایل‌های خالی
print("📌 بررسی فایل‌های خالی...")
for py_file in ROOT.rglob("*.py"):
    if py_file.stat().st_size == 0:
        warnings.append(f"⚠️  فایل خالی: {py_file.relative_to(ROOT)}")

# ۵) import *
print("📌 بررسی import * ...")
for py_file in ROOT.rglob("*.py"):
    try:
        content = py_file.read_text(encoding="utf-8")
    except Exception:
        continue
    if "import *" in content:
        warnings.append(f"⚠️  import * در {py_file.name}")

# ۶) توابع تعریف‌نشده (ساده)
print("📌 بررسی self._methods ...")
for py_file in ROOT.rglob("*.py"):
    try:
        content = py_file.read_text(encoding="utf-8")
    except Exception:
        continue
    # فقط فایل‌های UI
    if "tabs" in str(py_file) or "main_window" in str(py_file):
        called = set(re.findall(r"self\.(_[a-zA-Z_]+)\(", content))
        defined = set(re.findall(r"def (_[a-zA-Z_]+)\(", content))
        missing = called - defined
        if missing:
            warnings.append(
                f"⚠️  {py_file.name}: متدهای تعریف‌نشده: {missing}")

# نتیجه
print("\n" + "=" * 60)
print(f"🎯 نتیجه:")
print(f"   ❌ خطاها: {len(issues)}")
print(f"   ⚠️  هشدارها: {len(warnings)}")
print("=" * 60)

if issues:
    print("\n❌ خطاها:")
    for issue in issues[:40]:
        print("   " + issue)

if warnings:
    print("\n⚠️  هشدارها:")
    for w in warnings[:30]:
        print("   " + w)

if not issues and not warnings:
    print("\n✅ هیچ باگی پیدا نشد!")