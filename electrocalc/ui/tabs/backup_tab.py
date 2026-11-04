"""تب پشتیبان‌گیری — فقط مدیر."""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, StringVar

from electrocalc.config import constants as C
from electrocalc.core import backup as bk
from electrocalc.ui.scrollable_frame import ScrollableFrame


class BackupTab(ScrollableFrame):
    def __init__(self, parent, app):
        super().__init__(parent, padding=20)
        self.app = app
        self._backups = []
        self.build_ui()
        self.refresh()

    def build_ui(self):
        p = self.inner

        ttk.Label(p, text="💾  پشتیبان و بازیابی",
                  font=C.FONT_TITLE,
                  foreground=C.COLOR_HEADER_BG).pack(anchor="w", pady=(0, 6))
        ttk.Label(p, text="ساخت، بازیابی، حذف و مدیریت پشتیبان‌ها",
                  font=C.FONT_BODY,
                  foreground=C.COLOR_MUTED).pack(anchor="w", pady=(0, 15))

        # ===== ساخت پشتیبان =====
        create_box = ttk.LabelFrame(p, text="📦 ساخت پشتیبان جدید",
                                     padding=15)
        create_box.pack(fill="x", pady=(0, 15))

        ttk.Label(create_box, text="توضیحات (اختیاری):",
                  font=C.FONT_BODY).pack(anchor="w", pady=(0, 5))
        self.desc_var = StringVar()
        ttk.Entry(create_box, textvariable=self.desc_var).pack(
            fill="x", pady=(0, 10))

        btns = ttk.Frame(create_box)
        btns.pack(fill="x")

        ttk.Button(btns, text="💾 ساخت پشتیبان حالا",
                   command=self._create_backup).pack(side="left", ipadx=15)

        ttk.Button(btns, text="📂 باز کردن پوشه",
                   command=self._open_folder).pack(side="left", padx=8)

        ttk.Button(btns, text="📥 بازیابی از فایل...",
                   command=self._restore_from_file).pack(side="left")

        # ===== خلاصه =====
        self.summary_var = StringVar(value="")
        ttk.Label(p, textvariable=self.summary_var,
                  font=C.FONT_HEADER,
                  foreground=C.COLOR_SUCCESS).pack(anchor="w", pady=(0, 10))

        # ===== لیست پشتیبان‌ها =====
        list_box = ttk.LabelFrame(p,
                                   text="📋 پشتیبان‌های موجود   (با Ctrl چند تا رو انتخاب کن)",
                                   padding=10)
        list_box.pack(fill="both", expand=True, pady=(0, 10))

        cols = ("id", "name", "size", "created", "desc")
        self.tree = ttk.Treeview(list_box, columns=cols,
                                  show="headings", height=12,
                                  selectmode="extended")
        self.tree.heading("id", text="#")
        self.tree.heading("name", text="نام فایل")
        self.tree.heading("size", text="حجم")
        self.tree.heading("created", text="تاریخ ساخت")
        self.tree.heading("desc", text="توضیحات")

        self.tree.column("id", width=40, anchor="center")
        self.tree.column("name", width=240)
        self.tree.column("size", width=90, anchor="center")
        self.tree.column("created", width=160, anchor="center")
        self.tree.column("desc", width=250)

        self.tree.pack(fill="both", expand=True)

        # دکمه‌های عملیات
        ops = ttk.Frame(list_box)
        ops.pack(fill="x", pady=(10, 0))

        ttk.Button(ops, text="🔄 بروزرسانی",
                   command=self.refresh).pack(side="left")
        ttk.Button(ops, text="♻️ بازیابی",
                   command=self._restore_selected).pack(side="left", padx=8)

        ttk.Button(ops, text="🗑 حذف انتخاب‌شده‌ها",
                   command=self._delete_selected).pack(side="left", padx=8)

        ttk.Button(ops, text="⚠️ حذف همه",
                   command=self._delete_all).pack(side="left")

        # هشدار
        warn = tk.Label(p,
                        text="⚠️  توجه: هنگام بازیابی، اطلاعات فعلی جایگزین می‌شود. "
                             "قبل از بازیابی، خودکار یه پشتیبان ساخته می‌شود.",
                        font=C.FONT_SMALL, fg=C.COLOR_DANGER,
                        bg=C.COLOR_BG, wraplength=800, justify="right")
        warn.pack(anchor="w", pady=(10, 0))

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        backups = bk.list_backups()

        for idx, b in enumerate(backups, 1):
            created = b["created_at"][:19].replace("T", " ") if b["created_at"] else "-"
            self.tree.insert("", "end", iid=str(idx - 1),
                              values=(idx, b["name"], b["size_str"],
                                       created, b["description"]))

        self._backups = backups
        total_size = bk._format_size(bk.get_backup_size_total())
        self.summary_var.set(
            f"📊  {len(backups)} پشتیبان موجود   |   حجم کل: {total_size}")

    def _create_backup(self):
        try:
            desc = self.desc_var.get().strip()
            path = bk.create_backup(desc)
            messagebox.showinfo(
                "موفق",
                f"پشتیبان ساخته شد:\n\n{path}")
            self.desc_var.set("")
            self.refresh()
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def _open_folder(self):
        try:
            os.startfile(str(bk.BACKUPS_DIR))
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    def _restore_from_file(self):
        path = filedialog.askopenfilename(
            title="انتخاب فایل پشتیبان",
            initialdir=str(bk.BACKUPS_DIR),
            filetypes=[("فایل پشتیبان", "*.zip")])
        if not path:
            return
        self._do_restore(path)

    def _selected_indices(self):
        return [int(x) for x in self.tree.selection()]

    def _restore_selected(self):
        sel = self._selected_indices()
        if not sel:
            messagebox.showwarning("هشدار", "اول یک پشتیبان انتخاب کن.")
            return
        if len(sel) > 1:
            messagebox.showwarning("هشدار",
                                    "برای بازیابی، فقط یک پشتیبان انتخاب کن.")
            return
        b = self._backups[sel[0]]
        self._do_restore(b["path"])

    def _do_restore(self, path):
        if not messagebox.askyesno(
            "تأیید بازیابی",
            "⚠️  همه اطلاعات فعلی با پشتیبان جایگزین می‌شود.\n\n"
            "قبل از بازیابی، یه پشتیبان خودکار گرفته می‌شه.\n\n"
            "ادامه؟"
        ):
            return

        try:
            bk.restore_backup(path, auto_backup=True)
            messagebox.showinfo(
                "موفق",
                "بازیابی انجام شد.\n\n"
                "برای اعمال کامل، برنامه را ببند و دوباره باز کن.")
            self.refresh()
        except Exception as e:
            messagebox.showerror("خطا", str(e))

    # ============ حذف ============
    def _delete_selected(self):
        sel = self._selected_indices()
        if not sel:
            messagebox.showwarning("هشدار",
                                    "اول پشتیبان(ها) رو انتخاب کن.")
            return

        if len(sel) == 1:
            b = self._backups[sel[0]]
            msg = f"پشتیبان «{b['name']}» حذف شود؟"
        else:
            msg = f"{len(sel)} پشتیبان انتخاب‌شده حذف شوند؟"

        if not messagebox.askyesno("تأیید حذف", msg):
            return

        deleted = 0
        errors = []
        for idx in sel:
            try:
                b = self._backups[idx]
                if bk.delete_backup(b["path"]):
                    deleted += 1
            except Exception as e:
                errors.append(str(e))

        if errors:
            messagebox.showwarning(
                "نتیجه",
                f"{deleted} پشتیبان حذف شد.\n"
                f"{len(errors)} خطا رخ داد.")
        else:
            messagebox.showinfo("موفق", f"{deleted} پشتیبان حذف شد.")

        self.refresh()

    def _delete_all(self):
        if not self._backups:
            messagebox.showinfo("اطلاع", "هیچ پشتیبانی برای حذف وجود ندارد.")
            return

        if not messagebox.askyesno(
            "⚠️ حذف همه پشتیبان‌ها",
            f"آیا مطمئنی می‌خواهی همه {len(self._backups)} پشتیبان را حذف کنی؟\n\n"
            "این عمل قابل بازگشت نیست!"
        ):
            return

        if not messagebox.askyesno(
            "⚠️ تأیید نهایی",
            "واقعاً مطمئنی؟ همه پشتیبان‌ها پاک می‌شوند."
        ):
            return

        deleted = 0
        errors = []
        for b in self._backups:
            try:
                if bk.delete_backup(b["path"]):
                    deleted += 1
            except Exception as e:
                errors.append(str(e))

        if errors:
            messagebox.showwarning(
                "نتیجه",
                f"{deleted} پشتیبان حذف شد.\n"
                f"{len(errors)} خطا.")
        else:
            messagebox.showinfo("موفق", f"همه {deleted} پشتیبان حذف شدند.")

        self.refresh()