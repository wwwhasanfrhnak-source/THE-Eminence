"""تب همگام‌سازی — ارسال داده + دریافت + بروزرسانی."""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

from electrocalc.core import sync


class SyncTab(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#f8fafc")
        self.app = app
        self.current_user = dict(app.current_user) if app.current_user else {}
        self.username = self.current_user.get("username", "")
        self.role = self.current_user.get("role", "engineer")
        self.is_admin = (self.role == "admin")

        self._build_ui()
        self._load_settings()

    # ========================================================
    # UI
    # ========================================================
    def _build_ui(self):
        # هدر
        header = tk.Frame(self, bg="#7c3aed", height=60)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="🔄  همگام‌سازی با دفتر",
            bg="#7c3aed", fg="white",
            font=("Segoe UI", 16, "bold"),
        ).pack(side="right", padx=20, pady=15)

        # محتوا
        content = tk.Frame(self, bg="#f8fafc")
        content.pack(fill="both", expand=True, padx=20, pady=15)

        # ============ کارت مسیر Share ============
        path_card = tk.LabelFrame(
            content, text=" 📁 مسیر پوشه Share ",
            bg="#f8fafc", font=("Segoe UI", 11, "bold"),
            fg="#7c3aed", padx=15, pady=10,
        )
        path_card.pack(fill="x", pady=8)

        row = tk.Frame(path_card, bg="#f8fafc")
        row.pack(fill="x")

        tk.Label(row, text="مسیر:", bg="#f8fafc",
                 font=("Segoe UI", 10)).pack(side="right", padx=5)

        self.path_var = tk.StringVar()
        tk.Entry(row, textvariable=self.path_var,
                 font=("Segoe UI", 10)).pack(
            side="right", padx=5, fill="x", expand=True)

        tk.Button(row, text="📂 انتخاب",
                  bg="#06b6d4", fg="white",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=10, pady=4, cursor="hand2",
                  command=self._browse).pack(side="right", padx=3)

        tk.Button(row, text="💾 ذخیره",
                  bg="#10b981", fg="white",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=10, pady=4, cursor="hand2",
                  command=self._save_path).pack(side="right", padx=3)

        tk.Button(row, text="🔌 تست",
                  bg="#f59e0b", fg="white",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=10, pady=4, cursor="hand2",
                  command=self._test).pack(side="right", padx=3)

        # ============ کارت وضعیت ============
        status_card = tk.LabelFrame(
            content, text=" 📊 وضعیت ",
            bg="#f8fafc", font=("Segoe UI", 11, "bold"),
            fg="#7c3aed", padx=15, pady=10,
        )
        status_card.pack(fill="x", pady=8)

        self.status_lbl = tk.Label(
            status_card, text="⏳ در حال چک...",
            bg="#f8fafc", fg="#6b7280",
            font=("Segoe UI", 11), justify="right", anchor="e")
        self.status_lbl.pack(fill="x")

        # ============ کارت ارسال (مهندس) ============
        if not self.is_admin:
            send_card = tk.LabelFrame(
                content, text=" 📤 ارسال داده به دفتر ",
                bg="#f8fafc", font=("Segoe UI", 11, "bold"),
                fg="#10b981", padx=15, pady=10,
            )
            send_card.pack(fill="x", pady=8)

            tk.Label(
                send_card,
                text="داده‌های جدیدت (گزارش، ساعت کار، هزینه) رو به دفتر می‌فرسته.",
                bg="#f8fafc", fg="#6b7280",
                font=("Segoe UI", 10), anchor="e",
            ).pack(anchor="e", pady=(0, 8))

            self.send_btn = tk.Button(
                send_card, text="📤 ارسال به دفتر",
                bg="#10b981", fg="white",
                font=("Segoe UI", 12, "bold"),
                relief="flat", padx=25, pady=10, cursor="hand2",
                command=self._send_data,
            )
            self.send_btn.pack(side="right", padx=5)

            self.last_sync_lbl = tk.Label(
                send_card, text="",
                bg="#f8fafc", fg="#6b7280",
                font=("Segoe UI", 9), anchor="e")
            self.last_sync_lbl.pack(side="right", padx=10)

        # ============ کارت دریافت (مدیر) ============
        if self.is_admin:
            recv_card = tk.LabelFrame(
                content, text=" 📥 دریافت از مهندسین ",
                bg="#f8fafc", font=("Segoe UI", 11, "bold"),
                fg="#f59e0b", padx=15, pady=10,
            )
            recv_card.pack(fill="x", pady=8)

            tk.Label(
                recv_card,
                text="همه فایل‌های sync مهندسین رو می‌خونه و تو دیتابیس ادغام می‌کنه.",
                bg="#f8fafc", fg="#6b7280",
                font=("Segoe UI", 10), anchor="e",
            ).pack(anchor="e", pady=(0, 8))

            self.recv_btn = tk.Button(
                recv_card, text="📥 دریافت از مهندسین",
                bg="#f59e0b", fg="white",
                font=("Segoe UI", 12, "bold"),
                relief="flat", padx=25, pady=10, cursor="hand2",
                command=self._recv_data,
            )
            self.recv_btn.pack(side="right", padx=5)

            self.pending_lbl = tk.Label(
                recv_card, text="",
                bg="#f8fafc", fg="#6b7280",
                font=("Segoe UI", 9), anchor="e")
            self.pending_lbl.pack(side="right", padx=10)

        # ============ کارت بروزرسانی ============
        update_card = tk.LabelFrame(
            content, text=" 📦 بروزرسانی برنامه ",
            bg="#f8fafc", font=("Segoe UI", 11, "bold"),
            fg="#ef4444", padx=15, pady=10,
        )
        update_card.pack(fill="x", pady=8)

        self.update_lbl = tk.Label(
            update_card, text="",
            bg="#f8fafc", fg="#1f2937",
            font=("Segoe UI", 10), justify="right", anchor="e")
        self.update_lbl.pack(fill="x")

        self.changelog_lbl = tk.Label(
            update_card, text="",
            bg="#f8fafc", fg="#6b7280",
            font=("Segoe UI", 9), justify="right", anchor="e",
            wraplength=700)
        self.changelog_lbl.pack(fill="x", pady=(5, 8))

        self.install_btn = tk.Button(
            update_card, text="📥 دانلود و نصب بروزرسانی",
            bg="#ef4444", fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat", padx=25, pady=8, cursor="hand2",
            command=self._install_update, state="disabled",
        )
        self.install_btn.pack(side="right", padx=5)

        # Progress
        self.progress = ttk.Progressbar(
            content, orient="horizontal", length=600, mode="determinate")
        self.progress.pack(fill="x", pady=8)

        # دکمه چک مجدد
        tk.Button(
            content, text="🔄 چک مجدد",
            bg="#06b6d4", fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat", padx=20, pady=8, cursor="hand2",
            command=self._refresh_all,
        ).pack(side="right", padx=5, pady=5)

    # ========================================================
    # Events
    # ========================================================
    def _load_settings(self):
        path = sync.get_share_path()
        if path:
            self.path_var.set(str(path))
        self._refresh_all()

    def _browse(self):
        folder = filedialog.askdirectory(
            title="انتخاب پوشه Share",
            initialdir=str(sync.get_share_path() or Path.home()),
        )
        if folder:
            self.path_var.set(folder)

    def _save_path(self):
        path = self.path_var.get().strip()
        if not path:
            messagebox.showwarning("هشدار", "مسیر رو وارد کن")
            return

        sync.set_share_path(path)
        messagebox.showinfo("موفق", "مسیر ذخیره شد")
        self._refresh_all()

    def _test(self):
        ok, msg = sync.test_connection()
        if ok:
            messagebox.showinfo("موفق", f"✅ {msg}")
        else:
            messagebox.showerror("خطا", f"❌ {msg}")

    def _refresh_all(self):
        self.progress["value"] = 0

        share = sync.get_share_path()

        # وضعیت
        if not share:
            self.status_lbl.config(
                text="⚠️ مسیر Share تنظیم نشده",
                fg="#f59e0b")
            self._clear_update_card()
            return

        if not share.exists():
            self.status_lbl.config(
                text=f"❌ پوشه Share پیدا نشد:\n{share}",
                fg="#ef4444")
            self._clear_update_card()
            return

        self.status_lbl.config(
            text=f"✅ پوشه Share پیدا شد\n{share}",
            fg="#10b981")

        # برای مهندس: آخرین sync
        if not self.is_admin:
            last = sync.get_last_sync(self.username)
            if last:
                self.last_sync_lbl.config(
                    text=f"آخرین ارسال: {last[:16]}")
            else:
                self.last_sync_lbl.config(
                    text="هنوز چیزی ارسال نکردی")

        # برای مدیر: تعداد فایل‌های در انتظار
        if self.is_admin:
            pending = sync.get_pending_syncs()
            if pending:
                self.pending_lbl.config(
                    text=f"{len(pending)} فایل در انتظار دریافت",
                    fg="#f59e0b")
            else:
                self.pending_lbl.config(
                    text="فایل جدیدی نیست", fg="#10b981")

        # چک بروزرسانی
        self._check_update()

    def _clear_update_card(self):
        self.update_lbl.config(text="")
        self.changelog_lbl.config(text="")
        self.install_btn.config(state="disabled")

    # ========================================================
    # ارسال (مهندس)
    # ========================================================
    def _send_data(self):
        if not messagebox.askyesno(
            "تأیید",
            "داده‌های جدیدت به دفتر ارسال بشه؟",
        ):
            return

        self.send_btn.config(state="disabled", text="⏳ در حال ارسال...")
        self.update()

        ok, msg, count = sync.export_my_data(self.username)

        self.send_btn.config(state="normal", text="📤 ارسال به دفتر")

        if ok:
            if count > 0:
                messagebox.showinfo("موفق", f"✅ {msg}")
            else:
                messagebox.showinfo("اطلاع", msg)
            self._refresh_all()
        else:
            messagebox.showerror("خطا", f"❌ {msg}")

    # ========================================================
    # دریافت (مدیر)
    # ========================================================
    def _recv_data(self):
        pending = sync.get_pending_syncs()
        if not pending:
            messagebox.showinfo("اطلاع", "فایل جدیدی برای دریافت نیست")
            return

        if not messagebox.askyesno(
            "تأیید",
            f"{len(pending)} فایل دریافت و ادغام بشه؟",
        ):
            return

        self.recv_btn.config(state="disabled", text="⏳ در حال دریافت...")
        self.update()

        ok, msg, count = sync.import_all_from_engineers()

        self.recv_btn.config(state="normal", text="📥 دریافت از مهندسین")

        if ok:
            messagebox.showinfo("موفق", f"✅ {msg}")
        else:
            messagebox.showwarning("هشدار", msg)

        self._refresh_all()

    # ========================================================
    # بروزرسانی
    # ========================================================
    def _check_update(self):
        # نسخه فعلی
        from electrocalc.config import constants as C
        current = C.APP_VERSION

        # نسخه سرور (اگه version.json باشه)
        share = sync.get_share_path()
        if not share:
            return

        version_file = share / "updates" / "version.json"
        if not version_file.exists():
            self.update_lbl.config(
                text=f"نسخه فعلی: {current}  —  فایل version.json نیست",
                fg="#6b7280")
            self.install_btn.config(state="disabled")
            return

        try:
            import json
            with open(version_file, encoding="utf-8") as f:
                info = json.load(f)

            remote_v = info.get("version", "?")
            changelog = info.get("changelog", [])
            cl_text = "\n".join(f"• {c}" for c in changelog)

            if remote_v > current:
                self.update_lbl.config(
                    text=f"🆕 نسخه جدید موجوده!\n"
                         f"فعلی: {current}  →  جدید: {remote_v}",
                    fg="#f59e0b")
                self.changelog_lbl.config(text=cl_text)
                self.install_btn.config(state="normal")
            else:
                self.update_lbl.config(
                    text=f"✅ به‌روز هستی — {current}",
                    fg="#10b981")
                self.changelog_lbl.config(text="")
                self.install_btn.config(state="disabled")

        except Exception as e:
            self.update_lbl.config(
                text=f"خطا در خواندن version.json: {e}",
                fg="#ef4444")
            self.install_btn.config(state="disabled")

    def _install_update(self):
        messagebox.showinfo(
            "به‌زودی",
            "نصب خودکار بروزرسانی فعلاً فعال نیست.\n"
            "به‌زودی اضافه می‌شه.")