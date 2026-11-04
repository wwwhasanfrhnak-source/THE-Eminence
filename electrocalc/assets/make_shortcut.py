"""ساخت Shortcut با آیکون برای ویندوز."""
import os
import sys
from pathlib import Path


def make_shortcut():
    """Shortcut تو دسکتاپ با آیکون ⚡."""
    try:
        import win32com.client
    except ImportError:
        print("❌ pywin32 نصب نیست. اجرا کن:")
        print("   pip install pywin32")
        return

    desktop = Path(os.path.expanduser("~")) / "Desktop"
    shortcut_path = desktop / "The Eminence.lnk"

    project_dir = Path(__file__).parent
    python_exe = Path(sys.executable).parent / "pythonw.exe"
    icon_path = project_dir / "assets" / "icon.ico"
    main_py = project_dir / "main.py"

    if not icon_path.exists():
        print(f"❌ آیکون پیدا نشد: {icon_path}")
        return

    if not python_exe.exists():
        print(f"❌ pythonw.exe پیدا نشد: {python_exe}")
        return

    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(str(shortcut_path))

    shortcut.TargetPath = str(python_exe)
    shortcut.Arguments = f'"{main_py}"'
    shortcut.WorkingDirectory = str(project_dir)
    shortcut.IconLocation = str(icon_path)
    shortcut.Description = "THE Eminence — Professional Electrical Calculator"
    shortcut.save()

    print(f"✅ Shortcut ساخته شد: {shortcut_path}")
    print("")
    print("🎯 الان:")
    print("   1. برو دسکتاپ")
    print("   2. فایل 'The Eminence' رو ببین (با آیکون ⚡)")
    print("   3. روش راستکلیک کن → Pin to taskbar")
    print("   4. تمام!")


if __name__ == "__main__":
    make_shortcut()