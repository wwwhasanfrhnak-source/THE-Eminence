"""پنجره اصلی THE Eminence — با خروجی PDF/Excel."""

import os
import tkinter as tk
import tkinter.font as tkfont
import traceback
from tkinter import ttk, messagebox
from pathlib import Path
from PIL import Image, ImageTk, ImageSequence

from electrocalc.config import constants as C
from electrocalc.config import themes as themes_module
from electrocalc.core import timer as timer_module
from electrocalc.ui.scrollable_frame import (
    get_scroll_mode, get_scroll_speed, _current_speed,
)
from electrocalc.utils.logger import log


def _hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _rgb_hex(r, g, b):
    return f"#{r:02x}{g:02x}{b:02x}"


def _fmt_elapsed(seconds):
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:02d}"


def draw_h_gradient(canvas, x1, y1, x2, y2, c1, c2):
    r1, g1, b1 = _hex_rgb(c1)
    r2, g2, b2 = _hex_rgb(c2)
    steps = max(1, x2 - x1)
    for i in range(steps):
        r = r1 + (r2 - r1) * i // steps
        g = g1 + (g2 - g1) * i // steps
        b = b1 + (b2 - b1) * i // steps
        canvas.create_line(x1 + i, y1, x1 + i, y2, fill=_rgb_hex(r, g, b))


class TouchScrollable:
    def __init__(self):
        self._drag_data = {"y": 0, "x": 0, "scrolling": False}

    def enable_touch_scroll(self, widget, canvas):
        widget.bind("<Button-1>", lambda e: self._on_start(e), add="+")
        widget.bind("<B1-Motion>", lambda e: self._on_move(e, canvas), add="+")
        widget.bind("<ButtonRelease-1>", lambda e: self._on_end(e), add="+")

    def _on_start(self, event):
        self._drag_data["x"] = event.x_root
        self._drag_data["y"] = event.y_root
        self._drag_data["scrolling"] = False

    def _on_move(self, event, canvas):
        if self._drag_data["y"] == 0:
            return
        dy = event.y_root - self._drag_data["y"]
        dx = event.x_root - self._drag_data["x"]
        if abs(dx) > abs(dy) and not self._drag_data["scrolling"]:
            return
        if not self._drag_data["scrolling"]:
            if abs(dy) < 5:
                return
            self._drag_data["scrolling"] = True
        try:
            step = int(-1 * dy * _current_speed * 0.5)
            if step == 0:
                return
            canvas.yview_scroll(step, "units")
        except Exception:
            pass
        self._drag_data["y"] = event.y_root
        self._drag_data["x"] = event.x_root

    def _on_end(self, event):
        self._drag_data["scrolling"] = False


class SidebarButton(tk.Frame):
    def __init__(self, parent, icon, text, command, palette, collapsed=False):
        super().__init__(parent, bg=palette["sidebar"], cursor="hand2")
        self.palette = palette
        self.command = command
        self.active = False
        self.collapsed = collapsed
        self.active_bg = palette.get("active_bg", palette["card"])
        self.icon = icon
        self.text = text

        self.indicator = tk.Frame(self, width=3, bg=palette["sidebar"])
        self.indicator.pack(side="right", fill="y")

        if collapsed:
            label_text = icon
            padx = 6
            anchor = "center"
        else:
            label_text = f"{text}   {icon}"
            padx = 18
            anchor = "e"

        self.label = tk.Label(
            self,
            text=label_text,
            bg=palette["sidebar"],
            fg=palette["muted"],
            font=(palette.get("font_family", "Segoe UI"), 10),
            anchor=anchor,
            padx=padx,
            pady=10,
        )
        self.label.pack(side="right", fill="both", expand=True)

        self._press_pos = (0, 0)

        for w in (self, self.label):
            w.bind("<Enter>", self._enter)
            w.bind("<Leave>", self._leave)
            w.bind("<ButtonPress-1>", self._on_press, add="+")
            w.bind("<ButtonRelease-1>", self._click_release)

    def _on_press(self, e):
        self._press_pos = (e.x_root, e.y_root)

    def _click_release(self, e):
        dx = abs(e.x_root - self._press_pos[0])
        dy = abs(e.y_root - self._press_pos[1])
        if dx < 5 and dy < 5:
            self.command()

    def _enter(self, e):
        if not self.active:
            hover_bg = self.palette.get("active_bg", self.palette["card"])
            self.label.config(bg=hover_bg, fg=self.palette["text"])
            self.config(bg=hover_bg)

    def _leave(self, e):
        if not self.active:
            self.label.config(bg=self.palette["sidebar"], fg=self.palette["muted"])
            self.config(bg=self.palette["sidebar"])

    def set_active(self, active):
        self.active = active
        background = self.active_bg if active else self.palette["sidebar"]
        self.indicator.config(
            bg=self.palette["accent"] if active else self.palette["sidebar"]
        )
        self.config(bg=background)
        self.label.config(
            bg=background,
            fg=self.palette["accent"] if active else self.palette["muted"],
            font=(
                self.palette.get("font_family", "Segoe UI"),
                10,
                "bold" if active else "normal",
            ),
        )


class MainWindow(TouchScrollable):
    def __init__(self, current_user=None):
        TouchScrollable.__init__(self)

        self.current_user = dict(current_user) if current_user is not None else None
        self.scroll_mode = get_scroll_mode()
        self.scroll_speed = get_scroll_speed()

        self.pages = []
        self.sidebar_buttons = []
        self._tab_classes = {}
        self._built = []
        self.current_page = -1

        self._avatar_ref = None
        self._check_job = None
        self._timer_job = None
        self._session_id = None
        self._session_seconds = 0
        self._current_project_id = None
        self._sidebar_collapsed = False
        self._sidebar_frame = None
        self._content_frame = None
        self._bell_label = None
        self._page_title_label = None
        self._page_subtitle_label = None

        self._toggle_sidebar_btn = None
        self._change_btn = None
        self._proj_label = None
        self._timer_label = None
        self.status_var = None

        self._menu_img = None
        self._search_img = None
        self._news_icon = None

        try:
            from electrocalc.core import settings as st
            self.current_theme = st.get_setting("app_theme", "light")
        except Exception:
            self.current_theme = "light"

        if self.current_theme not in themes_module.get_names():
            self.current_theme = "light"

        themes_module.apply_to_constants(self.current_theme)
        self.palette = themes_module.get_palette(self.current_theme)

        self.root = tk.Tk()
        self._configure_fonts()
        self._setup_root()
        self._build_all()
        self._start_active_check()

        if self._has_timer_permission():
            self._start_session_timer()

        self._start_notification_check()
        self.root.bind("<Control-k>", lambda e: self._show_search())

        log.info(f"MainWindow ساخته شد. تم: {self.current_theme}")

    def _configure_fonts(self):
        families = {name.casefold(): name for name in tkfont.families(self.root)}
        default_family = tkfont.nametofont(
            "TkDefaultFont", root=self.root
        ).actual("family")
        self.font_family = next(
            (
                families[name.casefold()]
                for name in (
                    "Vazirmatn",
                    "IRANSans",
                    "Noto Sans Arabic",
                    "Tahoma",
                    "Segoe UI",
                    "DejaVu Sans",
                    "Arial",
                )
                if name.casefold() in families
            ),
            default_family,
        )
        self.palette["font_family"] = self.font_family

        for font_name in (
            "TkDefaultFont",
            "TkTextFont",
            "TkMenuFont",
            "TkHeadingFont",
            "TkCaptionFont",
            "TkSmallCaptionFont",
            "TkIconFont",
            "TkTooltipFont",
        ):
            try:
                tkfont.nametofont(font_name, root=self.root).configure(
                    family=self.font_family
                )
            except tk.TclError:
                continue

    def _has_timer_permission(self):
        if not self.current_user:
            return False
        if self.current_user["role"] == "admin":
            return False
        from electrocalc.auth import permissions as perms_module
        return perms_module.has_permission(self.current_user, "use_auto_timer")

    def _is_admin(self):
        return bool(self.current_user and self.current_user["role"] == "admin")

    def _is_engineer(self):
        return bool(self.current_user and self.current_user["role"] == "engineer")

    def _is_viewer(self):
        return bool(self.current_user and self.current_user["role"] == "viewer")

    def _setup_root(self):
        self.root.title(C.APP_TITLE)
        self.root.minsize(1100, 700)
        self.root.configure(bg=self.palette["bg"])
        self.root.update_idletasks()
        w, h = 1200, 760
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        try:
            icon_path = Path(__file__).resolve().parents[2] / "assets" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception:
            pass

    def _setup_ttk_styles(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        p = self.palette
        style.configure("TFrame", background=p["card"])
        style.configure(
            "TLabel",
            background=p["card"],
            foreground=p["text"],
            font=(self.font_family, 10),
        )
        style.configure(
            "TLabelframe",
            background=p["card"],
            bordercolor=p["border"],
            relief="solid",
            padding=12,
        )
        style.configure(
            "TLabelframe.Label",
            background=p["card"],
            foreground=p["accent"],
            font=(self.font_family, 11, "bold"),
        )
        style.configure(
            "TButton",
            font=(self.font_family, 10, "bold"),
            padding=(12, 8),
            borderwidth=0,
            background=p["card"],
            foreground=p["text"],
        )
        style.map(
            "TButton",
            background=[("active", p["active_bg"]), ("pressed", p["border"])],
            foreground=[("disabled", p["muted"])],
        )
        style.configure(
            "Accent.TButton",
            background=p["accent"],
            foreground="#FFFFFF",
        )
        style.map(
            "Accent.TButton",
            background=[("active", p["secondary"]), ("pressed", p["accent"])],
            foreground=[("active", "#FFFFFF")],
        )
        style.configure(
            "TEntry",
            fieldbackground=p["card"],
            foreground=p["text"],
            insertcolor=p["text"],
            bordercolor=p["border"],
            padding=(10, 7),
        )
        style.configure(
            "TCombobox",
            fieldbackground=p["card"],
            foreground=p["text"],
            bordercolor=p["border"],
            padding=(8, 6),
        )
        style.configure(
            "TRadiobutton",
            background=p["card"],
            foreground=p["text"],
            font=(self.font_family, 10),
        )
        style.configure(
            "TCheckbutton",
            background=p["card"],
            foreground=p["text"],
            font=(self.font_family, 10),
        )
        style.configure(
            "Treeview",
            background=p["card"],
            foreground=p["text"],
            fieldbackground=p["card"],
            rowheight=34,
            bordercolor=p["border"],
            font=(self.font_family, 10),
        )
        style.configure(
            "Treeview.Heading",
            background=p["sidebar"],
            foreground=p["muted"],
            font=(self.font_family, 9, "bold"),
            padding=(10, 9),
        )
        style.map(
            "Treeview",
            background=[("selected", p["accent"])],
            foreground=[("selected", "white")],
        )
        style.configure(
            "TScrollbar",
            background=p["border"],
            troughcolor=p["bg"],
            bordercolor=p["bg"],
        )

        if self.scroll_mode == "touch":
            style.configure("Touch.Vertical.TScrollbar", width=28, arrowsize=22)
            style.configure("Vertical.TScrollbar", width=28, arrowsize=22)

    def _build_all(self):
        self._setup_ttk_styles()
        self._build_header()

        body = tk.Frame(self.root, bg=self.palette["bg"])
        body.pack(fill="both", expand=True)
        self._body = body

        self._build_sidebar(body)

        self._content_frame = tk.Frame(body, bg=self.palette["bg"])
        self._content_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        self._build_content_header()

        self._create_tabs()
        self._build_status_bar()

        if self.pages:
            self.root.after(100, lambda: self._select_page(0))

    def _build_content_header(self):
        header = tk.Frame(self._content_frame, bg=self.palette["bg"])
        header.pack(fill="x", pady=(0, 14))

        title_block = tk.Frame(header, bg=self.palette["bg"])
        title_block.pack(side="right", fill="x", expand=True)
        items = self._get_items()
        initial_title = items[0][1] if items else C.APP_TITLE
        self._page_title_label = tk.Label(
            title_block,
            text=initial_title,
            bg=self.palette["bg"],
            fg=self.palette["text"],
            font=(self.font_family, 18, "bold"),
            anchor="e",
            justify="right",
        )
        self._page_title_label.pack(anchor="e")
        self._page_subtitle_label = tk.Label(
            title_block,
            text="مدیریت یکپارچه اطلاعات و فعالیت‌های پروژه",
            bg=self.palette["bg"],
            fg=self.palette["muted"],
            font=(self.font_family, 9),
            anchor="e",
            justify="right",
        )
        self._page_subtitle_label.pack(anchor="e", pady=(3, 0))

        tk.Label(
            header,
            text="محیط کار",
            bg=self.palette.get("active_bg", self.palette["card"]),
            fg=self.palette["accent"],
            font=(self.font_family, 8, "bold"),
            padx=10,
            pady=5,
        ).pack(side="left", anchor="n", pady=6)

    def _build_header(self):
        p = self.palette
        h = tk.Frame(self.root, height=76, bg=p["card"])
        h.pack(fill="x", side="top")
        h.pack_propagate(False)

        left = tk.Frame(h, bg=p["card"])
        left.pack(side="left", fill="y", padx=(18, 12))

        self._toggle_sidebar_btn = tk.Label(
            left,
            text="",
            bg=p["card"],
            fg=p["muted"],
            font=(self.font_family, 17, "bold"),
            cursor="hand2",
            padx=10,
            pady=8,
        )
        self._toggle_sidebar_btn.pack(side="left", padx=(0, 9), pady=12)
        self._toggle_sidebar_btn.bind("<Button-1>", lambda e: self._toggle_sidebar())
        self._toggle_sidebar_btn.bind(
            "<Enter>", lambda e: self._toggle_sidebar_btn.config(bg=p["active_bg"])
        )
        self._toggle_sidebar_btn.bind(
            "<Leave>", lambda e: self._toggle_sidebar_btn.config(bg=p["card"])
        )

        try:
            base_dir = os.getcwd()
            img = Image.open(os.path.join(base_dir, "assets", "arrow_20261113205622.gif"))
            img.seek(0)
            img = img.convert("RGBA").resize((24, 24), Image.LANCZOS)
            self._menu_img = ImageTk.PhotoImage(img)
            self._toggle_sidebar_btn.configure(image=self._menu_img)
        except Exception as e:
            print(f"Menu Icon Error: {e}")
            self._toggle_sidebar_btn.configure(text="☰")

        brand = tk.Frame(left, bg=p["card"])
        brand.pack(side="left", pady=12)
        tk.Label(
            brand,
            text="⚡",
            bg=p["card"],
            fg=p["accent"],
            font=(self.font_family, 22, "bold"),
        ).pack(side="left", padx=(0, 8))
        brand_text = tk.Frame(brand, bg=p["card"])
        brand_text.pack(side="left", anchor="w")
        tk.Label(
            brand_text,
            text="THE Eminence",
            bg=p["card"],
            fg=p["text"],
            font=(self.font_family, 12, "bold"),
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            brand_text,
            text=f"نسخه {C.APP_VERSION}",
            bg=p["card"],
            fg=p["muted"],
            font=(self.font_family, 8),
            anchor="w",
        ).pack(anchor="w")

        right = tk.Frame(h, bg=p["card"])
        right.pack(side="right", fill="y", padx=(10, 18))

        def action_label(parent, text, command, width=None):
            widget = tk.Label(
                parent,
                text=text,
                bg=p["card"],
                fg=p["muted"],
                font=(self.font_family, 13),
                cursor="hand2",
                padx=10,
                pady=8,
                width=width,
            )
            widget.pack(side="right", pady=12)
            widget.bind("<Button-1>", lambda e: command())
            widget.bind(
                "<Enter>", lambda e, w=widget: w.config(bg=p["active_bg"], fg=p["accent"])
            )
            widget.bind(
                "<Leave>", lambda e, w=widget: w.config(bg=p["card"], fg=p["muted"])
            )
            return widget

        if self.current_user:
            try:
                un = self.current_user.get("full_name") or self.current_user["username"]
            except AttributeError:
                un = self.current_user["full_name"] or self.current_user["username"]
            role = {"admin": "مدیر", "engineer": "مهندس", "viewer": "ناظر"}.get(self.current_user["role"], "")
            profile = tk.Frame(right, bg=p["card"], cursor="hand2")
            profile.pack(side="right", padx=(8, 0), pady=10)

            from electrocalc.utils.avatar import get_avatar
            avatar = get_avatar(self.current_user, 36)
            if avatar:
                lbl_av = tk.Label(
                    profile,
                    image=avatar,
                    bg=p["card"],
                    cursor="hand2",
                    borderwidth=0,
                    highlightthickness=0,
                )
                lbl_av.image = avatar
                self._avatar_ref = avatar
                lbl_av.pack(side="right", padx=(0, 8))
            profile_text = tk.Frame(profile, bg=p["card"])
            profile_text.pack(side="right")
            tk.Label(
                profile_text,
                text=un,
                bg=p["card"],
                fg=p["text"],
                font=(self.font_family, 9, "bold"),
                anchor="e",
                justify="right",
            ).pack(anchor="e")
            tk.Label(
                profile_text,
                text=role,
                bg=p["card"],
                fg=p["muted"],
                font=(self.font_family, 8),
                anchor="e",
                justify="right",
            ).pack(anchor="e")
            for widget in (
                profile,
                *profile.winfo_children(),
                *profile_text.winfo_children(),
            ):
                widget.bind("<Button-1>", lambda e: self._change_my_profile())

        try:
            base_dir = os.getcwd()
            news_path = os.path.join(base_dir, "assets", "news.png")
            img = Image.open(news_path).convert("RGBA").resize((24, 24), Image.LANCZOS)
            self._news_icon = ImageTk.PhotoImage(img)
            self._bell_label = tk.Label(right, image=self._news_icon, bg=p["card"], cursor="hand2")
            self._bell_label.pack(side="right", pady=12, padx=10)
            self._bell_label.bind("<Button-1>", lambda e: self._show_notifications())
            self._bell_label.bind("<Enter>", lambda e: self._bell_label.configure(bg=p["active_bg"]))
            self._bell_label.bind("<Leave>", lambda e: self._bell_label.configure(bg=p["card"]))
        except Exception as e:
            print(f"News Icon Error: {e}")
            self._bell_label = action_label(right, "🔔", self._show_notifications, width=3)

        action_label(right, "⋯", self._show_header_menu, width=3)

        if self._has_timer_permission():
            timer_frame = tk.Frame(
                h,
                bg=p["active_bg"],
                padx=9,
                pady=5,
            )
            timer_frame.pack(side="right", padx=(0, 12), pady=14)

            self._change_btn = tk.Label(
                timer_frame,
                text="تغییر پروژه",
                bg=p["active_bg"],
                fg=p["accent"],
                font=(self.font_family, 9, "bold"),
                cursor="hand2",
                padx=8,
            )
            self._change_btn.pack(side="right", padx=(8, 0))
            self._change_btn.bind("<Button-1>", lambda e: self._change_project())
            self._change_btn.bind(
                "<Enter>", lambda e: self._change_btn.config(fg=p["secondary"])
            )
            self._change_btn.bind(
                "<Leave>", lambda e: self._change_btn.config(fg=p["accent"])
            )

            self._proj_label = tk.Label(
                timer_frame,
                text="بدون پروژه",
                bg=p["active_bg"],
                fg=p["muted"],
                font=(self.font_family, 9),
            )
            self._proj_label.pack(side="right", padx=4)

            self._timer_label = tk.Label(
                timer_frame,
                text="00:00:00",
                bg=p["active_bg"],
                fg=p["text"],
                font=("Consolas", 10, "bold"),
                padx=4,
            )
            self._timer_label.pack(side="right", padx=4)

        search_frame = tk.Frame(
            h,
            bg=p["bg"],
            highlightbackground=p["border"],
            highlightthickness=1,
        )
        search_frame.pack(side="right", fill="x", expand=True, padx=10, pady=15)
        search_hint = tk.Label(
            search_frame,
            text="جست‌وجو در پروژه‌ها، گزارش‌ها و کاربران",
            bg=p["bg"],
            fg=p["muted"],
            font=(self.font_family, 9),
            anchor="e",
            justify="right",
            cursor="hand2",
            padx=12,
            pady=8,
        )
        search_hint.pack(side="right", fill="x", expand=True)
        search_icon = tk.Label(
            search_frame,
            text="",
            bg=p["bg"],
            fg=p["accent"],
            font=(self.font_family, 12),
            cursor="hand2",
            padx=10,
        )
        search_icon.pack(side="right")

        try:
            base_dir = os.getcwd()
            search_path = os.path.join(base_dir, "assets", "loupe.png")
            img = Image.open(search_path).convert("RGBA").resize((20, 20), Image.LANCZOS)
            self._search_img = ImageTk.PhotoImage(img)
            search_icon.configure(image=self._search_img)
        except Exception as e:
            print(f"Search Icon Error: {e}")
            search_icon.configure(text="🔍")

        for widget in (search_frame, search_hint, search_icon):
            widget.bind("<Button-1>", lambda e: self._show_search())
        search_frame.bind("<Enter>", lambda e: search_frame.config(bg=p["active_bg"]))
        search_frame.bind("<Leave>", lambda e: search_frame.config(bg=p["bg"]))

    def _show_header_menu(self):
        menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=self.palette["card"],
            fg=self.palette["text"],
            activebackground=self.palette["active_bg"],
            activeforeground=self.palette["accent"],
            font=(self.font_family, 10),
        )
        if self.current_user:
            menu.add_command(label="ویرایش پروفایل", command=self._change_my_profile)
            menu.add_command(label="تغییر رمز عبور", command=self._change_my_password)
            menu.add_separator()
        menu.add_command(label="تغییر پوسته", command=self._show_theme_menu)
        menu.add_command(label="خروجی PDF", command=self.export_pdf)
        menu.add_command(label="خروجی Excel", command=self.export_excel)
        menu.add_separator()
        menu.add_command(label="خروج از حساب", command=self.on_close)
        try:
            menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            menu.grab_release()

    def _build_sidebar(self, parent):
        collapsed = self._sidebar_collapsed
        width = 72 if collapsed else 248

        side = tk.Frame(parent, bg=self.palette["sidebar"], width=width)
        side.pack(side="right", fill="y")
        side.pack_propagate(False)
        self._sidebar_frame = side

        brand = tk.Frame(side, bg=self.palette["sidebar"], height=76)
        brand.pack(fill="x", pady=(8, 0))
        brand.pack_propagate(False)
        logo = tk.Label(
            brand,
            text="⚡",
            font=(self.font_family, 24, "bold"),
            bg=self.palette["sidebar"],
            fg=self.palette["accent"],
        )
        if collapsed:
            logo.pack(expand=True)
        else:
            logo.pack(side="right", padx=(0, 14), pady=8)
            brand_text = tk.Frame(brand, bg=self.palette["sidebar"])
            brand_text.pack(side="right", fill="y", expand=True, pady=14)
            tk.Label(
                brand_text,
                text="THE Eminence",
                bg=self.palette["sidebar"],
                fg=self.palette["text"],
                font=(self.font_family, 10, "bold"),
                anchor="e",
            ).pack(anchor="e")
            tk.Label(
                brand_text,
                text="میزکار مدیریت پروژه",
                bg=self.palette["sidebar"],
                fg=self.palette["muted"],
                font=(self.font_family, 8),
                anchor="e",
            ).pack(anchor="e")

        sep = tk.Frame(side, height=1, bg=self.palette["border"])
        sep.pack(fill="x", padx=16, pady=(0, 12))

        scroll_container = tk.Frame(side, bg=self.palette["sidebar"])
        scroll_container.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_container, bg=self.palette["sidebar"], highlightthickness=0, borderwidth=0)

        if self.scroll_mode == "touch":
            scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview, style="Touch.Vertical.TScrollbar")
            scrollbar.pack(side="left", fill="y")
            canvas.configure(yscrollcommand=scrollbar.set)
        elif self.scroll_mode == "hidden":
            pass
        elif self.scroll_mode == "thin":
            scrollbar = tk.Scrollbar(
                scroll_container,
                orient="vertical",
                command=canvas.yview,
                width=6,
                troughcolor=self.palette["bg"],
                bg=self.palette["border"],
                activebackground=self.palette["muted"],
                borderwidth=0,
                highlightthickness=0,
                relief="flat",
            )
            scrollbar.pack(side="left", fill="y")
            canvas.configure(yscrollcommand=scrollbar.set)
        else:
            scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=canvas.yview)
            if not collapsed:
                scrollbar.pack(side="left", fill="y")
            canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="right", fill="both", expand=True)

        items_frame = tk.Frame(canvas, bg=self.palette["sidebar"])
        items_window = canvas.create_window((0, 0), window=items_frame, anchor="nw")

        def on_mousewheel(e):
            try:
                delta = e.delta if hasattr(e, "delta") else 0
                if e.num == 4:
                    delta = 120
                elif e.num == 5:
                    delta = -120
                from electrocalc.ui.scrollable_frame import _current_speed as spd
                step_float = -1 * (delta / 120) * spd
                if step_float >= 1:
                    step = int(step_float)
                elif step_float <= -1:
                    step = int(step_float)
                elif step_float > 0:
                    step = 1
                elif step_float < 0:
                    step = -1
                else:
                    return
                canvas.yview_scroll(step, "units")
            except Exception:
                pass

        canvas.bind("<MouseWheel>", on_mousewheel)
        items_frame.bind("<MouseWheel>", on_mousewheel)
        canvas.bind("<Button-4>", on_mousewheel)
        canvas.bind("<Button-5>", on_mousewheel)

        self.enable_touch_scroll(canvas, canvas)
        self.enable_touch_scroll(items_frame, canvas)

        def on_inner_config(e):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_config(e):
            canvas.itemconfig(items_window, width=e.width)

        items_frame.bind("<Configure>", on_inner_config)
        canvas.bind("<Configure>", on_canvas_config)

        items = self._get_items()

        self.sidebar_buttons = []
        for idx, (icon, label, _, _) in enumerate(items):
            btn = SidebarButton(items_frame, icon, label, lambda i=idx: self._select_page(i), self.palette, collapsed=collapsed)
            btn.pack(fill="x")
            self.enable_touch_scroll(btn, canvas)
            self.enable_touch_scroll(btn.label, canvas)
            self.sidebar_buttons.append(btn)

        if not collapsed:
            bottom = tk.Frame(side, bg=self.palette["sidebar"])
            bottom.pack(side="bottom", fill="x", pady=10)
            tk.Label(
                bottom,
                text=f"نسخه {C.APP_VERSION}",
                bg=self.palette["sidebar"],
                fg=self.palette["muted"],
                font=(self.font_family, 8),
            ).pack()

    def _get_common_items(self, icons):
        return [
            (icons["home"], "خانه", "electrocalc.ui.tabs.home_tab", "HomeTab"),
            (icons["reports"], "تقویم کارگاه", "electrocalc.ui.tabs.calendar_tab", "CalendarTab"),
            (icons["projects"], "پروژه‌ها", "electrocalc.ui.tabs.projects_tab", "ProjectsTab"),
            (icons["reports"], "گزارش‌ها", "electrocalc.ui.tabs.reports_tab", "ReportsTab"),
            (icons["timesheet"], "ساعات کار", "electrocalc.ui.tabs.timesheet_tab", "TimesheetTab"),
            (icons["materials"], "مصالح", "electrocalc.ui.tabs.materials_tab", "MaterialsTab"),
            (icons["expenses"], "هزینه‌ها", "electrocalc.ui.tabs.expenses_tab", "ExpensesTab"),
            (icons["files"], "فایل‌ها", "electrocalc.ui.tabs.files_tab", "FilesTab"),
            (icons["approvals"], "درخواست مصالح", "electrocalc.ui.tabs.requests_tab", "RequestsTab"),
            (icons["ohm"], "ماشین حساب", "electrocalc.ui.tabs.calculator_tab", "CalculatorTab"),
            (icons["power"], "ماشین حساب مهندسی", "electrocalc.ui.tabs.scientific_tab", "ScientificTab"),
            (icons["settings"], "همگام‌سازی", "electrocalc.ui.tabs.sync_tab", "SyncTab"),
        ]

    def _get_admin_items(self, icons):
        top = [
            (icons["dashboard"], "داشبورد", "electrocalc.ui.tabs.dashboard_tab", "DashboardTab"),
            (icons["users"], "عملکرد", "electrocalc.ui.tabs.performance_tab", "PerformanceTab"),
            (icons["expenses"], "مالی پروژه", "electrocalc.ui.tabs.finance_tab", "FinanceTab"),
            (icons["expenses"], "فاکتور", "electrocalc.ui.tabs.invoices_tab", "InvoicesTab"),
        ]

        bottom = [
            (icons["materials"], "انبار", "electrocalc.ui.tabs.warehouse_tab", "WarehouseTab"),
            (icons["approvals"], "تأییدها", "electrocalc.ui.tabs.approvals_tab", "ApprovalsTab"),
            (icons["users"], "مشتریان", "electrocalc.ui.tabs.customers_tab", "CustomersTab"),
            (icons["users"], "کاربران", "electrocalc.ui.tabs.users_tab", "UsersTab"),
            (icons["company"], "اطلاعات شرکت", "electrocalc.ui.tabs.company_tab", "CompanyTab"),
            (icons["backup"], "پشتیبان‌گیری", "electrocalc.ui.tabs.backup_tab", "BackupTab"),
            (icons["audit"], "ثبت فعالیت‌ها", "electrocalc.ui.tabs.audit_tab", "AuditTab"),
            (icons["health"], "سلامت دیتابیس", "electrocalc.ui.tabs.health_tab", "HealthTab"),
            (icons["settings"], "تنظیمات", "electrocalc.ui.tabs.settings_tab", "SettingsTab"),
        ]

        return top, bottom

    def _get_engineer_items(self, icons):
        return [
            (icons["settings"], "تنظیمات", "electrocalc.ui.tabs.settings_tab", "SettingsTab"),
        ]

    def _get_items(self):
        icons = themes_module.get_icons(self.current_theme)
        common = self._get_common_items(icons)

        if self._is_admin():
            admin_top, admin_bottom = self._get_admin_items(icons)
            home = common[0:1]
            rest_common = common[1:]
            return home + admin_top + rest_common + admin_bottom

        elif self._is_engineer():
            eng = self._get_engineer_items(icons)
            return common + eng

        else:
            return common

    def _create_tabs(self):
        items = self._get_items()
        self.pages = []
        self._tab_classes = {}
        self._built = []

        for idx, (icon, label, module_path, class_name) in enumerate(items):
            placeholder = tk.Frame(self._content_frame, bg=self.palette["bg"])
            self.pages.append(placeholder)
            self._built.append(False)
            self._tab_classes[idx] = (label, module_path, class_name)

        self._build_tab(0)

    def _build_tab(self, idx):
        if idx < 0 or idx >= len(self.pages):
            return
        if self._built[idx]:
            return
        if idx not in self._tab_classes:
            return

        label, module_path, class_name = self._tab_classes[idx]

        try:
            try:
                self.pages[idx].destroy()
            except Exception:
                pass

            mod = __import__(module_path, fromlist=[class_name])
            TabCls = getattr(mod, class_name)
            page = TabCls(self._content_frame, self)
            self.pages[idx] = page
            self._built[idx] = True

            log.info(f"✅ تب «{label}» ساخته شد")

        except Exception as e:
            tb = traceback.format_exc()
            log.error(f"❌ خطا در ساخت تب «{label}»:\n{tb}")
            self.pages[idx] = self._placeholder_page(label, str(e))
            self._built[idx] = True

    def _placeholder_page(self, title, error):
        frame = tk.Frame(self._content_frame, bg=self.palette["bg"], padx=20, pady=20)
        tk.Label(frame, text=f"⚠️  تب «{title}» بارگذاری نشد", font=(self.font_family, 16, "bold"), bg=self.palette["bg"], fg=self.palette["danger"], anchor="e", justify="right").pack(anchor="e", pady=(0, 15))
        tk.Label(frame, text="خطا:", font=(self.font_family, 11, "bold"), bg=self.palette["bg"], fg=self.palette["text"], anchor="e", justify="right").pack(anchor="e", pady=(0, 5))
        tk.Label(frame, text=error, font=("Consolas", 9), bg=self.palette["bg"], fg=self.palette["danger"], wraplength=700, justify="right", anchor="e").pack(anchor="e", pady=(0, 15))
        return frame

    def _toggle_sidebar(self):
        prev_page = self.current_page
        self._sidebar_collapsed = not self._sidebar_collapsed

        if self._sidebar_frame:
            self._sidebar_frame.destroy()
        if self._content_frame:
            self._content_frame.destroy()

        self.pages.clear()
        self.sidebar_buttons.clear()
        self._tab_classes = {}
        self._built = []
        self.current_page = -1

        self._build_sidebar(self._body)
        self._content_frame = tk.Frame(self._body, bg=self.palette["bg"])
        self._content_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        self._build_content_header()
        self._create_tabs()

        if 0 <= prev_page < len(self.pages):
            self.root.after(100, lambda: self._select_page(prev_page))
        elif self.pages:
            self.root.after(100, lambda: self._select_page(0))

    def _build_status_bar(self):
        bar = tk.Frame(self.root, height=30, bg=self.palette["status_bar"])
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        self.status_var = tk.StringVar(value="آماده")
        tk.Label(
            bar,
            textvariable=self.status_var,
            bg=self.palette["status_bar"],
            fg=self.palette["muted"],
            font=(self.font_family, 8),
            anchor="e",
            justify="right",
        ).pack(side="right", padx=15)

    def _find_treeview(self, widget):
        try:
            if widget.winfo_class() == "Treeview":
                return widget
        except Exception:
            pass

        try:
            if hasattr(widget, "inner"):
                r = self._find_treeview(widget.inner)
                if r:
                    return r
        except Exception:
            pass

        try:
            for child in widget.winfo_children():
                r = self._find_treeview(child)
                if r:
                    return r
        except Exception:
            pass

        return None

    def _get_current_tree_data(self):
        if self.current_page < 0 or self.current_page >= len(self.pages):
            return None

        page = self.pages[self.current_page]
        tree = self._find_treeview(page)
        if not tree:
            return None

        try:
            cols = tree["columns"]
            if not cols:
                return None
            headers = [tree.heading(c).get("text", c) for c in cols]
        except Exception:
            return None

        rows = []
        for item in tree.get_children():
            vals = tree.item(item, "values")
            rows.append(tuple(vals))

        if not rows:
            return None

        return headers, rows

    def _get_tab_name(self):
        info = self._tab_classes.get(self.current_page, ("خروجی",))
        return info[0] if info else "خروجی"

    def export_excel(self):
        try:
            data = self._get_current_tree_data()
            if not data:
                messagebox.showwarning("هشدار", "این تب جدول نداره یا خالیه.")
                return

            headers, rows = data
            from electrocalc.core import export

            tab_name = self._get_tab_name()
            path = export.export_to_excel(headers, rows, title=tab_name)
            messagebox.showinfo("موفق", f"ذخیره شد:\n{path}")
            try:
                os.startfile(str(Path(path).parent))
            except Exception:
                pass
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("خطا", str(e))

    def export_pdf(self):
        try:
            data = self._get_current_tree_data()
            if not data:
                messagebox.showwarning("هشدار", "این تب جدول نداره یا خالیه.")
                return

            headers, rows = data
            from electrocalc.core import export

            tab_name = self._get_tab_name()
            path = export.export_to_pdf(headers, rows, title=tab_name)
            messagebox.showinfo("موفق", f"ذخیره شد:\n{path}")
            try:
                os.startfile(path)
            except Exception:
                pass
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("خطا", str(e))

    def _show_search(self):
        from electrocalc.ui.search_dialog import SearchDialog
        dlg = SearchDialog(self.root, self.palette, self)
        dlg.show()

    def _goto_tab_by_name(self, name):
        for idx, (_, label, _, _) in enumerate(self._get_items()):
            if label == name and idx < len(self.pages):
                self._select_page(idx)
                return

    def _show_notifications(self):
        if not self.current_user:
            return
        from electrocalc.ui.notifications_panel import NotificationsPanel
        panel = NotificationsPanel(self.root, self.current_user["username"], self.palette, self)
        x = self.root.winfo_rootx() + self.root.winfo_width() - 400
        y = self.root.winfo_rooty() + 75
        panel.show(x, y)

    def _update_bell_badge(self):
        if not self.current_user:
            return
        if not self._bell_label:
            return
        try:
            if not self._bell_label.winfo_exists():
                return
            from electrocalc.core import notifications as notif_module
            count = notif_module.count_unread(self.current_user["username"])
            if count > 0:
                self._bell_label.config(text=f"🔔 {count}", fg=self.palette["accent"])
            else:
                self._bell_label.config(text="🔔", fg=self.palette["muted"])
        except Exception:
            pass

    def _start_notification_check(self):
        def check():
            try:
                self._update_bell_badge()
            except Exception:
                pass
            if self.root.winfo_exists():
                self.root.after(15000, check)

        self.root.after(2000, check)

    def _show_theme_menu(self):
        menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=self.palette["card"],
            fg=self.palette["text"],
            activebackground=self.palette["active_bg"],
            activeforeground=self.palette["accent"],
            font=(self.font_family, 10),
        )
        for key in themes_module.get_names():
            theme = themes_module.THEMES[key]
            prefix = "✅  " if key == self.current_theme else "    "
            menu.add_command(
                label=f"{prefix}{theme['name']}",
                command=lambda k=key: self.set_theme(k),
            )
        try:
            menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            menu.grab_release()

    def set_theme(self, theme_key):
        if theme_key not in themes_module.get_names():
            return
        if theme_key == self.current_theme:
            return

        try:
            from electrocalc.core import settings as st
            st.set_setting("app_theme", theme_key)
        except Exception:
            pass

        self.current_theme = theme_key
        themes_module.apply_to_constants(theme_key)
        self.palette = themes_module.get_palette(theme_key)

        self.reload_ui()

    def reload_ui(self):
        prev_page = self.current_page

        if getattr(self, "_check_job", None):
            try:
                self.root.after_cancel(self._check_job)
            except Exception:
                pass

        if getattr(self, "_timer_job", None):
            try:
                self.root.after_cancel(self._timer_job)
            except Exception:
                pass

        for child in self.root.winfo_children():
            child.destroy()

        self.pages.clear()
        self.sidebar_buttons.clear()
        self._tab_classes = {}
        self._built = []
        self.current_page = -1

        self._avatar_ref = None
        self._sidebar_frame = None
        self._content_frame = None
        self._bell_label = None
        self._toggle_sidebar_btn = None
        self._change_btn = None
        self._proj_label = None
        self._timer_label = None

        self.scroll_mode = get_scroll_mode()
        self.scroll_speed = get_scroll_speed()

        self.root.configure(bg=self.palette["bg"])
        self._build_all()

        if 0 <= prev_page < len(self.pages):
            self.root.after(150, lambda: self._select_page(prev_page))
        elif self.pages:
            self.root.after(150, lambda: self._select_page(0))

        log.info("UI بازسازی شد")

    def _start_session_timer(self):
        if not self.current_user:
            return
        try:
            self._session_id = timer_module.start_session(self.current_user["username"])
            self._session_seconds = 0
            self._tick_timer()
            log.info(f"جلسه شروع شد: id={self._session_id}")
        except Exception as e:
            log.error(f"خطا در شروع جلسه: {e}")

    def _tick_timer(self):
        if not getattr(self, "_session_id", None):
            return

        self._session_seconds += 1
        try:
            self._timer_label.config(text=f"⏱  {_fmt_elapsed(self._session_seconds)}")
        except Exception:
            pass

        if self._session_seconds % 60 == 0:
            try:
                timer_module.ping(self._session_id)
            except Exception:
                pass

        self._timer_job = self.root.after(1000, self._tick_timer)

    def _end_session(self):
        if not getattr(self, "_session_id", None):
            return

        try:
            ts_id = timer_module.end_session(self._session_id)
            if ts_id:
                log.info(f"جلسه ذخیره شد: timesheet_id={ts_id}")
        except Exception as e:
            log.error(f"خطا در بستن جلسه: {e}")
        finally:
            self._session_id = None

    def _change_project(self):
        from electrocalc.core import projects as proj

        user = self.current_user
        if not user:
            return

        items = proj.list_projects_for_user(user["username"])

        win = tk.Toplevel(self.root)
        win.title("تغییر پروژه")
        win.geometry("420x480")
        win.configure(bg=self.palette["bg"])
        win.transient(self.root)
        win.grab_set()

        win.update_idletasks()
        px = self.root.winfo_rootx() + self.root.winfo_width() // 2 - 210
        py = self.root.winfo_rooty() + self.root.winfo_height() // 2 - 240
        win.geometry(f"420x480+{px}+{py}")

        tk.Label(win, text="📁  انتخاب پروژه", font=(self.font_family, 16, "bold"), bg=self.palette["bg"], fg=self.palette["accent"], anchor="e", justify="right").pack(fill="x", padx=24, pady=(20, 8))
        tk.Label(win, text="پروژه‌ای که روش کار می‌کنی را انتخاب کن", font=(self.font_family, 9), bg=self.palette["bg"], fg=self.palette["muted"], anchor="e", justify="right").pack(fill="x", padx=24, pady=(0, 15))

        list_frame = tk.Frame(win, bg=self.palette["bg"])
        list_frame.pack(fill="both", expand=True, padx=30)

        listbox = tk.Listbox(
            list_frame,
            font=(self.font_family, 11),
            activestyle="none",
            selectbackground=self.palette["accent"],
            selectforeground="#FFFFFF",
            justify="right",
            bg=self.palette["card"],
            fg=self.palette["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=self.palette["border"],
        )
        sb = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=sb.set)
        sb.pack(side="left", fill="y")
        listbox.pack(side="right", fill="both", expand=True)

        listbox.insert(tk.END, "🚫  بدون پروژه")
        pid_map = [None]
        for p in items:
            status_fa = proj.STATUS_FA.get(p["status"], p["status"])
            listbox.insert(tk.END, f"📁  {p['name']}  —  {status_fa}")
            pid_map.append(p["id"])

        if self._current_project_id is None:
            listbox.selection_set(0)
        else:
            for i, pid in enumerate(pid_map):
                if pid == self._current_project_id:
                    listbox.selection_set(i)
                    listbox.see(i)
                    break

        def do_change():
            sel = listbox.curselection()
            if not sel:
                messagebox.showwarning("هشدار", "یک پروژه انتخاب کن.", parent=win)
                return
            idx = sel[0]
            new_pid = pid_map[idx]
            new_name = "بدون پروژه"
            if new_pid is not None:
                for p in items:
                    if p["id"] == new_pid:
                        new_name = p["name"]
                        break

            try:
                if getattr(self, "_session_id", None):
                    new_sid = timer_module.change_project(self._session_id, new_pid)
                    if new_sid:
                        self._session_id = new_sid

                self._current_project_id = new_pid
                self._proj_label.config(text=f"📁  {new_name}")
                win.destroy()
            except Exception as e:
                messagebox.showerror("خطا", str(e), parent=win)

        def do_cancel():
            win.destroy()

        btns = tk.Frame(win, bg=self.palette["bg"])
        btns.pack(pady=15)
        ttk.Button(btns, text="✅ انتخاب", command=do_change).pack(side="left", padx=5, ipadx=20, ipady=8)
        ttk.Button(btns, text="انصراف", command=do_cancel).pack(side="left", padx=5, ipadx=20, ipady=8)

        listbox.bind("<Double-1>", lambda e: do_change())
        win.bind("<Return>", lambda e: do_change())
        win.bind("<Escape>", lambda e: do_cancel())

    def _start_active_check(self):
        if not self.current_user:
            return

        def check():
            try:
                from electrocalc.auth import users as users_module
                u = users_module.get_user(self.current_user["username"])
                if not u or not u["active"]:
                    log.warning("کاربر غیرفعال شد — اخراج")
                    self._end_session()
                    messagebox.showerror("دسترسی قطع شد", "حساب کاربری شما توسط مدیر غیرفعال شد.")
                    self.root.destroy()
                    return
                self.current_user = dict(u)
            except Exception as e:
                log.error(f"خطا در چک فعال بودن: {e}")

            if self.root.winfo_exists():
                self._check_job = self.root.after(30000, check)

        self._check_job = self.root.after(30000, check)

    def _select_page(self, idx):
        if idx < 0 or idx >= len(self.pages) or idx == self.current_page:
            return

        if not self._built[idx]:
            self._build_tab(idx)

        if self.current_page >= 0:
            try:
                self.pages[self.current_page].pack_forget()
                self.sidebar_buttons[self.current_page].set_active(False)
            except Exception:
                pass

        try:
            self.pages[idx].pack(fill="both", expand=True)
            self.sidebar_buttons[idx].set_active(True)
            self.current_page = idx
            title = self._tab_classes[idx][0]
            self._page_title_label.config(text=title)
            self._page_subtitle_label.config(
                text=f"مدیریت و مشاهدهٔ اطلاعات بخش {title}"
            )
        except Exception as e:
            log.error(f"خطا در نمایش صفحه {idx}: {e}")

    def _change_my_password(self):
        if not self.current_user:
            return
        from electrocalc.ui.change_password_dialog import ChangePasswordDialog
        dlg = ChangePasswordDialog(self.root, target_username=self.current_user["username"], need_old=True)
        self.root.wait_window(dlg.win)

    def _change_my_profile(self):
        if not self.current_user:
            return
        from electrocalc.ui.profile_dialog import ProfileDialog

        def refresh():
            from electrocalc.auth import users
            self.current_user = users.get_user(self.current_user["username"])
            self.reload_ui()

        dlg = ProfileDialog(self.root, username=self.current_user["username"], on_done=refresh)
        self.root.wait_window(dlg.win)

    def set_status(self, text):
        if self.status_var is not None:
            self.status_var.set(text)

    def run(self):
        log.info("حلقه اصلی اجرا شد.")
        self.root.mainloop()

    def on_close(self):
        log.info("برنامه در حال بسته شدن است.")

        if self.current_user:
            try:
                from electrocalc.core import audit as audit_module
                audit_module.log_action(
                    username=self.current_user["username"],
                    action="logout",
                    description="خروج از سیستم",
                )
            except Exception:
                pass

        if getattr(self, "_check_job", None):
            try:
                self.root.after_cancel(self._check_job)
            except Exception:
                pass

        if getattr(self, "_timer_job", None):
            try:
                self.root.after_cancel(self._timer_job)
            except Exception:
                pass

        if getattr(self, "_session_id", None):
            self._end_session()

        try:
            self.root.destroy()
        except Exception:
            pass