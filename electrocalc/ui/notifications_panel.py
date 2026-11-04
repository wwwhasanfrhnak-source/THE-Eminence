"""پنل اعلان‌ها — dropdown بالای صفحه."""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from electrocalc.core import notifications as notif_module


class NotificationsPanel:
    """پنل کشویی اعلان‌ها."""

    def __init__(self, parent, username, palette, app):
        self.parent = parent
        self.username = username
        self.palette = palette
        self.app = app
        self.win = None
        self._busy = False  # جلوگیری از بستن موقع دیالوگ

    def show(self, x=None, y=None):
        """نمایش پنل."""
        if self.win and self.win.winfo_exists():
            self.win.destroy()

        p = self.palette
        self.win = tk.Toplevel(self.parent)
        self.win.overrideredirect(True)
        self.win.configure(bg=p["border"])

        w, h = 400, 500
        if x is None:
            x = self.parent.winfo_pointerx() - w + 20
        if y is None:
            y = self.parent.winfo_pointery() + 5
        self.win.geometry(f"{w}x{h}+{x}+{y}")

        main = tk.Frame(self.win, bg=p["card"], padx=2, pady=2)
        main.pack(fill="both", expand=True)

        # ===== هدر =====
        header = tk.Frame(main, bg=p["h_start"], height=42)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(header, text="🔔  اعلان‌ها",
                 font=("Segoe UI", 12, "bold"),
                 bg=p["h_start"], fg="white",
                 anchor="e").pack(side="right", padx=15, pady=10)

        unread = notif_module.count_unread(self.username)
        if unread > 0:
            tk.Label(header, text=f"{unread} نخوانده",
                     font=("Segoe UI", 9),
                     bg=p["h_start"], fg="#ffdd00",
                     anchor="w").pack(side="left", padx=15)

        # ===== دکمه‌ها =====
        btns = tk.Frame(main, bg=p["card"])
        btns.pack(fill="x", padx=10, pady=8)

        tk.Button(btns, text="✅ خواندن همه",
                  command=self._mark_all_read,
                  bg=p["accent"], fg="white",
                  activebackground=p["accent"],
                  font=("Segoe UI", 9), relief="flat",
                  cursor="hand2", padx=10).pack(side="right", padx=2)

        tk.Button(btns, text="🗑 پاک کردن همه",
                  command=self._clear_all,
                  bg=p["danger"], fg="white",
                  activebackground=p["danger"],
                  font=("Segoe UI", 9), relief="flat",
                  cursor="hand2", padx=10).pack(side="right", padx=2)

        # ===== لیست =====
        self.list_container = tk.Frame(main, bg=p["card"])
        self.list_container.pack(fill="both", expand=True, padx=6, pady=4)

        self._render_list()

        # بستن با Escape
        self.win.bind("<Escape>", lambda e: self._close())
        self.win.focus_set()

    def _render_list(self):
        """رندر مجدد لیست اعلان‌ها."""
        p = self.palette

        # پاک‌سازی
        for w in self.list_container.winfo_children():
            w.destroy()

        canvas = tk.Canvas(self.list_container, bg=p["card"],
                            highlightthickness=0, borderwidth=0)
        sb = ttk.Scrollbar(self.list_container, orient="vertical",
                            command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)

        sb.pack(side="left", fill="y")
        canvas.pack(side="right", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=p["card"])
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_inner_config(e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_config(e):
            canvas.itemconfig(win_id, width=e.width)

        inner.bind("<Configure>", on_inner_config)
        canvas.bind("<Configure>", on_canvas_config)

        def on_wheel(e):
            try:
                canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            except Exception:
                pass

        canvas.bind("<MouseWheel>", on_wheel)

        notifs = notif_module.list_notifications(self.username, limit=50)
        if not notifs:
            tk.Label(inner, text="📭 هیچ اعلانی وجود ندارد",
                     font=("Segoe UI", 10),
                     bg=p["card"], fg=p["muted"],
                     pady=40).pack()
        else:
            for n in notifs:
                self._add_row(inner, n, p)

    def _add_row(self, parent, notif, p):
        """یه ردیف اعلان."""
        is_unread = not notif["is_read"]
        bg_color = p["bg"] if is_unread else p["card"]

        row = tk.Frame(parent, bg=bg_color, cursor="hand2",
                        highlightbackground=p["border"],
                        highlightthickness=1)
        row.pack(fill="x", padx=4, pady=3)

        cat_colors = {
            "info": p["accent"], "success": "#10b981",
            "warning": "#f59e0b", "danger": p["danger"],
            "report": "#7c3aed", "expense": "#ef4444",
            "approval": "#10b981", "message": "#06b6d4",
            "project": "#f59e0b", "stock": "#8b5cf6",
        }
        cat = notif["category"] or "info"
        color = cat_colors.get(cat, p["accent"])

        # نوار رنگی
        tk.Frame(row, bg=color, width=4).pack(side="right", fill="y")

        body = tk.Frame(row, bg=bg_color)
        body.pack(side="right", fill="both", expand=True,
                  padx=10, pady=8)

        title_font = ("Segoe UI", 10, "bold" if is_unread else "normal")
        tk.Label(body, text=notif["title"],
                 font=title_font, bg=bg_color,
                 fg=p["text"], anchor="e",
                 wraplength=320, justify="right").pack(
            anchor="e", fill="x")

        if notif["message"]:
            tk.Label(body, text=notif["message"][:120],
                     font=("Segoe UI", 9),
                     bg=bg_color, fg=p["muted"],
                     anchor="e", wraplength=320,
                     justify="right").pack(anchor="e", fill="x")

        try:
            dt = datetime.fromisoformat(notif["created_at"])
            time_str = dt.strftime("%m/%d  %H:%M")
        except Exception:
            time_str = ""

        foot = tk.Frame(body, bg=bg_color)
        foot.pack(fill="x")

        tk.Label(foot, text=time_str,
                 font=("Segoe UI", 8),
                 bg=bg_color, fg=p["muted"],
                 anchor="w").pack(side="left")

        # دکمه حذف
        del_btn = tk.Label(foot, text="🗑",
                            font=("Segoe UI", 10),
                            bg=bg_color, fg=p["muted"],
                            cursor="hand2", padx=4)
        del_btn.pack(side="left", padx=4)
        del_btn.bind("<Button-1>",
                      lambda e, nid=notif["id"]: self._delete_one(nid))

        # کلیک روی ردیف = خوانده شدن
        def on_click(e, nid=notif["id"]):
            notif_module.mark_read(nid)
            self.app._update_bell_badge()
            self._render_list()

        for w in (row, body):
            w.bind("<Button-1>", on_click)

    def _mark_all_read(self):
        notif_module.mark_all_read(self.username)
        self.app._update_bell_badge()
        self._render_list()
        # رفرش header هم لازمه
        self._refresh_header()

    def _refresh_header(self):
        """به‌روزرسانی هدر بدون بستن پنل."""
        # ساده‌ترین راه: بستن و باز کردن
        if self.win and self.win.winfo_exists():
            x = self.win.winfo_x()
            y = self.win.winfo_y()
            self.win.destroy()
            self.show(x, y)

    def _clear_all(self):
        """پاک کردن همه اعلان‌ها."""
        self._busy = True
        try:
            if not messagebox.askyesno(
                "تأیید",
                "همه اعلان‌ها پاک شوند؟",
                parent=self.parent,
            ):
                return

            notif_module.clear_all(self.username)
            self.app._update_bell_badge()
            self._render_list()
            self._refresh_header()
        finally:
            self._busy = False

    def _delete_one(self, notif_id):
        """حذف یه اعلان."""
        notif_module.delete_notification(notif_id)
        self.app._update_bell_badge()
        self._render_list()
        self._refresh_header()

    def _close(self):
        try:
            if self.win:
                self.win.destroy()
        except Exception:
            pass