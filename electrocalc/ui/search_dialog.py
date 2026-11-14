"""پنجره جستجوی سراسری — Ctrl+K."""

import os
import tkinter as tk
from tkinter import ttk
from tkinter import StringVar
from PIL import Image, ImageTk, ImageSequence

from electrocalc.core import search as search_module


class SearchDialog:
    """پنجره جستجو با نتایج زنده."""

    def __init__(self, parent, palette, app):
        self.parent = parent
        self.palette = palette
        self.app = app
        self.win = None
        self._job = None
        self._icon_frames = []
        self._icon_index = 0
        self._anim_job = None

    def show(self):
        if self.win and self.win.winfo_exists():
            self.win.lift()
            self.win.focus_set()
            return

        p = self.palette
        self.win = tk.Toplevel(self.parent)
        self.win.title("جستجوی سراسری")
        self.win.configure(bg=p["bg"])
        self.win.transient(self.parent)
        self.win.grab_set()

        w, h = 700, 600
        self.win.update_idletasks()
        px = self.parent.winfo_rootx() + self.parent.winfo_width() // 2 - w // 2
        py = self.parent.winfo_rooty() + self.parent.winfo_height() // 2 - h // 2
        self.win.geometry(f"{w}x{h}+{px}+{py}")

        # ===== هدر =====
        tk.Label(self.win, text="🔎  جستجوی سراسری",
                 font=("Segoe UI", 16, "bold"),
                 bg=p["bg"], fg=p["h_start"]).pack(pady=(20, 5))

        tk.Label(self.win,
                 text="در پروژه‌ها، کاربران، گزارش‌ها، هزینه‌ها، پیام‌ها و همه جا",
                 font=("Segoe UI", 9),
                 bg=p["bg"], fg=p["muted"]).pack(pady=(0, 15))

        # ===== کادر جستجو =====
        search_frame = tk.Frame(self.win, bg=p["bg"])
        search_frame.pack(fill="x", padx=30, pady=(0, 15))

        entry_frame = tk.Frame(search_frame, bg=p["border"], padx=2, pady=2)
        entry_frame.pack(fill="x")

        self.query_var = StringVar()
        self.entry = tk.Entry(entry_frame, textvariable=self.query_var,
                                font=("Segoe UI", 13),
                                bg=p["card"], fg=p["text"],
                                insertbackground=p["text"],
                                relief="flat", bd=0)
        self.entry.pack(side="right", fill="x", expand=True,
                         padx=12, pady=10)
        self.entry.focus_set()

        self.query_var.trace_add("write", lambda *a: self._schedule_search())

        # ===== نتایج =====
        results_frame = tk.Frame(self.win, bg=p["bg"])
        results_frame.pack(fill="both", expand=True, padx=30, pady=(0, 15))

        self.canvas = tk.Canvas(results_frame, bg=p["bg"],
                                  highlightthickness=0)
        sb = ttk.Scrollbar(results_frame, orient="vertical",
                            command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="left", fill="y")
        self.canvas.pack(side="right", fill="both", expand=True)

        self.results_inner = tk.Frame(self.canvas, bg=p["bg"])
        win_id = self.canvas.create_window((0, 0), window=self.results_inner,
                                             anchor="nw")

        def on_config(e):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        def on_canvas_config(e):
            self.canvas.itemconfig(win_id, width=e.width)

        self.results_inner.bind("<Configure>", on_config)
        self.canvas.bind("<Configure>", on_canvas_config)

        def on_wheel(e):
            try:
                self.canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
            except Exception:
                pass

        self.canvas.bind("<MouseWheel>", on_wheel)

        # ===== راهنما پایین =====
        tk.Label(self.win,
                 text="💡 حداقل ۲ کاراکتر بنویس  |  Enter روی نتیجه = رفتن به تب  |  Esc = بستن",
                 font=("Segoe UI", 8),
                 bg=p["bg"], fg=p["muted"]).pack(pady=(0, 10))

        self.win.bind("<Escape>", lambda e: self.win.destroy())
        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

        # نمایش اولیه
        self._show_hint()

    def _on_close(self):
        if self._anim_job:
            try:
                self.win.after_cancel(self._anim_job)
            except Exception:
                pass
        self.win.destroy()

    def _show_hint(self):
        p = self.palette
        for w in self.results_inner.winfo_children():
            w.destroy()
        
        hint_frame = tk.Frame(self.results_inner, bg=p["bg"])
        hint_frame.pack(pady=40)

        # ۱. لود کردن عکس متحرک بزرگ‌تر (48x48)
        try:
            base_dir = os.getcwd()
            icon_path = os.path.join(base_dir, "assets", "Searching_20261113211851.gif")
            img = Image.open(icon_path)
            self._icon_frames = []
            for frame in ImageSequence.Iterator(img):
                frame_img = frame.convert("RGBA").resize((48, 48), Image.LANCZOS) # سایز بزرگتر
                self._icon_frames.append(ImageTk.PhotoImage(frame_img))
            
            if self._icon_frames:
                self.hint_icon = tk.Label(hint_frame, bg=p["bg"])
                self.hint_icon.pack(side="right", padx=(10, 0))
                self._icon_index = 0
                self._animate_hint()
        except Exception as e:
            print(f"Hint Icon Error: {e}")

        # ۲. متن راهنما
        tk.Label(hint_frame,
                 text="شروع به تایپ کن...",
                 font=("Segoe UI", 12),
                 bg=p["bg"], fg=p["muted"]).pack(side="right")

    def _animate_hint(self):
        if not self._icon_frames or not hasattr(self, 'hint_icon'):
            return
        try:
            self.hint_icon.configure(image=self._icon_frames[self._icon_index])
            self._icon_index = (self._icon_index + 1) % len(self._icon_frames)
            self._anim_job = self.hint_icon.after(80, self._animate_hint)
        except Exception:
            pass

    def _schedule_search(self):
        if self._job:
            try:
                self.win.after_cancel(self._job)
            except Exception:
                pass
        # زمان انتظار از 250 به 100 کاهش یافت تا جستجو سریع‌تر انجام شود
        self._job = self.win.after(100, self._do_search)

    def _do_search(self):
        query = self.query_var.get().strip()
        p = self.palette

        if self._anim_job:
            try:
                self.win.after_cancel(self._anim_job)
                self._anim_job = None
            except Exception:
                pass

        for w in self.results_inner.winfo_children():
            w.destroy()

        if len(query) < 2:
            self._show_hint()
            return

        try:
            results = search_module.search_all(query)
        except Exception as e:
            tk.Label(self.results_inner,
                     text=f"خطا: {e}",
                     font=("Segoe UI", 10),
                     bg=p["bg"], fg=p["danger"],
                     pady=20).pack()
            return

        if not results:
            tk.Label(self.results_inner,
                     text=f"😕  نتیجه‌ای برای «{query}» پیدا نشد",
                     font=("Segoe UI", 11),
                     bg=p["bg"], fg=p["muted"],
                     pady=40).pack()
            return

        total = sum(len(v) for v in results.values())
        tk.Label(self.results_inner,
                 text=f"✅  {total} نتیجه در {len(results)} دسته",
                 font=("Segoe UI", 10, "bold"),
                 bg=p["bg"], fg=p["success"],
                 anchor="e").pack(anchor="e", pady=(0, 10), padx=5)

        for category, items in results.items():
            self._add_category(category, items, p)

    def _add_category(self, category, items, p):
        cat_frame = tk.Frame(self.results_inner, bg=p["bg"])
        cat_frame.pack(fill="x", pady=(10, 4))
        tk.Label(cat_frame, text=f"{category}  ({len(items)})",
                 font=("Segoe UI", 11, "bold"),
                 bg=p["bg"], fg=p["accent"],
                 anchor="e").pack(anchor="e", padx=5)
        tk.Frame(self.results_inner, bg=p["border"], height=1).pack(
            fill="x", padx=5, pady=(0, 6))
        for item in items:
            self._add_result_row(item, category, p)

    def _add_result_row(self, item, category, p):
        row = tk.Frame(self.results_inner, bg=p["card"],
                        cursor="hand2",
                        highlightbackground=p["border"],
                        highlightthickness=1)
        row.pack(fill="x", padx=5, pady=2)
        body = tk.Frame(row, bg=p["card"])
        body.pack(fill="both", expand=True, padx=12, pady=8)
        tk.Label(body, text=item["title"],
                 font=("Segoe UI", 10, "bold"),
                 bg=p["card"], fg=p["text"],
                 anchor="e").pack(anchor="e", fill="x")
        if item["subtitle"]:
            tk.Label(body, text=item["subtitle"],
                     font=("Segoe UI", 8),
                     bg=p["card"], fg=p["muted"],
                     anchor="e").pack(anchor="e", fill="x")

        def on_click(e):
            self._go_to(category, item)

        def on_enter(e):
            row.config(bg=p["bg"])
            body.config(bg=p["bg"])
            for w in body.winfo_children():
                w.config(bg=p["bg"])

        def on_leave(e):
            row.config(bg=p["card"])
            body.config(bg=p["card"])
            for w in body.winfo_children():
                w.config(bg=p["card"])

        for w in (row, body):
            w.bind("<Button-1>", on_click)
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)

    def _go_to(self, category, item):
        tab_map = {
            "📁 پروژه‌ها": "پروژه‌ها",
            "👥 کاربران": "کاربران",
            "📝 گزارش‌ها": "گزارش‌ها",
            "💰 هزینه‌ها": "هزینه‌ها",
            "🔧 مصالح": "مصالح",
            "💬 پیام‌ها": "پیام‌ها",
            "📎 فایل‌ها": "فایل‌ها",
            "⏰ ساعات کار": "ساعات کار",
        }
        tab_name = tab_map.get(category)
        if tab_name:
            self.app._goto_tab_by_name(tab_name)
        if self.win:
            self.win.destroy()