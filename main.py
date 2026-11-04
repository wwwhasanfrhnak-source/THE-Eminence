"""نقطه ورود برنامه THE Eminence."""

import sys
import traceback
from pathlib import Path
from datetime import datetime
import ctypes
import tkinter as tk
from tkinter import messagebox


# ========================================================
# Import همه ماژول‌ها (برای pyinstaller — هیچوقت اجرا نمیشه)
# ========================================================
if False:
    # تب‌های اصلی
    from electrocalc.ui.tabs import home_tab
    from electrocalc.ui.tabs import calendar_tab
    from electrocalc.ui.tabs import projects_tab
    from electrocalc.ui.tabs import reports_tab
    from electrocalc.ui.tabs import timesheet_tab
    from electrocalc.ui.tabs import materials_tab
    from electrocalc.ui.tabs import expenses_tab
    from electrocalc.ui.tabs import files_tab
    from electrocalc.ui.tabs import requests_tab
    from electrocalc.ui.tabs import calculator_tab
    from electrocalc.ui.tabs import scientific_tab
    from electrocalc.ui.tabs import dashboard_tab
    from electrocalc.ui.tabs import performance_tab
    from electrocalc.ui.tabs import finance_tab
    from electrocalc.ui.tabs import invoices_tab
    from electrocalc.ui.tabs import warehouse_tab
    from electrocalc.ui.tabs import approvals_tab
    from electrocalc.ui.tabs import customers_tab
    from electrocalc.ui.tabs import users_tab
    from electrocalc.ui.tabs import company_tab
    from electrocalc.ui.tabs import backup_tab
    from electrocalc.ui.tabs import audit_tab
    from electrocalc.ui.tabs import health_tab
    from electrocalc.ui.tabs import settings_tab
    from electrocalc.ui.tabs import sync_tab

    # ماشین حساب‌های ویژه
    from electrocalc.ui.tabs import ohm_tab
    from electrocalc.ui.tabs import power_tab
    from electrocalc.ui.tabs import voltage_drop_tab
    from electrocalc.ui.tabs import ampacity_tab
    from electrocalc.ui.tabs import fuse_tab
    from electrocalc.ui.tabs import motor_tab
    from electrocalc.ui.tabs import motor_advanced_tab
    from electrocalc.ui.tabs import star_delta_tab
    from electrocalc.ui.tabs import rlc_tab
    from electrocalc.ui.tabs import units_tab

    # مدیریت
    from electrocalc.ui.tabs import management_tabs

    # هسته
    from electrocalc.core import ohm
    from electrocalc.core import power
    from electrocalc.core import voltage_drop
    from electrocalc.core import ampacity
    from electrocalc.core import fuse
    from electrocalc.core import motor
    from electrocalc.core import motor_advanced
    from electrocalc.core import star_delta
    from electrocalc.core import rlc
    from electrocalc.core import units


# ========================================================
# Error Logging
# ========================================================
def _log_error(exc_type, exc_value, exc_tb):
    try:
        if getattr(sys, "frozen", False):
            base = Path(sys.executable).parent
        else:
            base = Path(__file__).parent

        err_file = base / "error.log"

        with open(err_file, "a", encoding="utf-8") as f:
            f.write("=" * 60 + "\n")
            f.write(f"Time: {datetime.now()}\n")
            f.write(f"Type: {exc_type.__name__}\n")
            f.write(f"Value: {exc_value}\n")
            f.write("-" * 60 + "\n")
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
            f.write("\n\n")
    except Exception:
        pass

    traceback.print_exception(exc_type, exc_value, exc_tb)


sys.excepthook = _log_error


# ========================================================
# App ID
# ========================================================
try:
    myappid = 'theeminence.electrocalc.0.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


# ========================================================
# Splash
# ========================================================
def show_splash():
    base = get_base_dir()

    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.attributes("-topmost", True)

    try:
        ico = base / "assets" / "icon.ico"
        if ico.exists():
            splash.iconbitmap(str(ico))
    except Exception:
        pass

    splash_img = base / "assets" / "splash.png"

    if splash_img.exists():
        try:
            from PIL import Image, ImageTk
            img = Image.open(splash_img).convert("RGBA")

            max_w = 600
            if img.width > max_w:
                ratio = max_w / img.width
                new_w = max_w
                new_h = int(img.height * ratio)
                img = img.resize((new_w, new_h), Image.LANCZOS)
            else:
                new_w, new_h = img.size

            photo = ImageTk.PhotoImage(img)

            sw = splash.winfo_screenwidth()
            sh = splash.winfo_screenheight()
            x = (sw - new_w) // 2
            y = (sh - new_h) // 2
            splash.geometry(f"{new_w}x{new_h}+{x}+{y}")

            label = tk.Label(splash, image=photo,
                             borderwidth=0, highlightthickness=0,
                             bg="#0a1628")
            label.image = photo
            label.pack(fill="both", expand=True)

            splash.after(1800, splash.destroy)
            splash.mainloop()
            return
        except Exception as e:
            print(f"خطا در splash: {e}")

    w, h = 500, 380
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    x = (sw - w) // 2
    y = (sh - h) // 2
    splash.geometry(f"{w}x{h}+{x}+{y}")

    canvas = tk.Canvas(splash, width=w, height=h,
                       highlightthickness=0, bg="#7c3aed")
    canvas.pack(fill="both", expand=True)

    for i in range(h):
        r = int(124 + (6 - 124) * i / h)
        g = int(58 + (182 - 58) * i / h)
        b = int(237 + (212 - 237) * i / h)
        canvas.create_line(0, i, w, i, fill=f"#{r:02x}{g:02x}{b:02x}")

    canvas.create_text(w // 2, 105, text="⚡",
                       fill="white", font=("Segoe UI", 72))
    canvas.create_text(w // 2, 210, text="THE Eminence",
                       fill="white", font=("Segoe UI", 26, "bold"))
    canvas.create_text(w // 2, 240,
                       text="Professional Electrical Calculator",
                       fill="#e0e7ff", font=("Segoe UI", 10))

    splash.after(1800, splash.destroy)
    splash.mainloop()


# ========================================================
# Main
# ========================================================
def main():
    try:
        show_splash()
    except Exception as e:
        _log_error(type(e), e, e.__traceback__)

    try:
        from electrocalc.data.database import init_db
        init_db()
    except Exception as e:
        _log_error(type(e), e, e.__traceback__)
        messagebox.showerror("خطا", f"دیتابیس:\n{e}")
        return

    try:
        from electrocalc.ui.login_window import LoginWindow
        login = LoginWindow()
        user = login.run()
    except Exception as e:
        _log_error(type(e), e, e.__traceback__)
        messagebox.showerror("خطا", f"Login:\n{e}")
        return

    if not user:
        return

    try:
        from electrocalc.ui.main_window import MainWindow
        app = MainWindow(current_user=user)
        app.run()
    except Exception as e:
        _log_error(type(e), e, e.__traceback__)
        messagebox.showerror("خطا", f"اجرا:\n{e}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        _log_error(type(e), e, e.__traceback__)