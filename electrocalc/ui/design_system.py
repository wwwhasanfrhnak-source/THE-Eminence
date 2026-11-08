"""Shared THE Eminence desktop design tokens and ttk styling helpers."""

from tkinter import ttk

TOKENS = {
    "font_family": "Vazirmatn",
    "font_mono": "Consolas",
    "font_small": 9,
    "font_body": 10,
    "font_section": 12,
    "font_title": 20,
    "space_xs": 4,
    "space_sm": 8,
    "space_md": 14,
    "space_lg": 20,
    "space_xl": 28,
    "radius_sm": 8,
    "radius_md": 12,
    "radius_lg": 18,
}

PREMIUM_PALETTES = {
    "light": {
        "bg": "#F4F7FC", "sidebar": "#FFFFFF", "card": "#FFFFFF",
        "border": "#E3EAF4", "accent": "#3867E8", "text": "#17233B",
        "muted": "#71809A", "h_start": "#244FC4", "h_end": "#168CCB",
        "success": "#168A65", "danger": "#D84C5B", "status_bar": "#EAF0F8",
    },
    "dark": {
        "bg": "#0B1220", "sidebar": "#101A2B", "card": "#142137",
        "border": "#243550", "accent": "#4E8BFF", "text": "#EAF1FC",
        "muted": "#93A4BE", "h_start": "#152B55", "h_end": "#116A94",
        "success": "#46C79A", "danger": "#F06B78", "status_bar": "#0A1020",
    },
    "windows11_light": {
        "bg": "#F3F6FB", "sidebar": "#FFFFFF", "card": "#FFFFFF",
        "border": "#E2E8F0", "accent": "#2563C7", "text": "#192536",
        "muted": "#64748B", "h_start": "#2056A8", "h_end": "#1685BD",
    },
    "windows11_dark": {
        "bg": "#1E1F22", "sidebar": "#2B2D31", "card": "#313338",
        "border": "#3F4147", "accent": "#5B8DEF", "text": "#F2F3F5",
        "muted": "#9CA3AF", "h_start": "#4A6FA5", "h_end": "#3B7999",
    },
}

def premium_palette(name_or_dict="light"):
    """Accept either a palette name (str) or a palette dict."""
    if isinstance(name_or_dict, dict):
        return name_or_dict
    return PREMIUM_PALETTES.get(name_or_dict, PREMIUM_PALETTES["light"])

def apply_ttk_styles(style: ttk.Style, palette: dict, font_family: str = "Vazirmatn"):
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("TFrame", background=palette.get("card", "#FFFFFF"))
    style.configure("TLabel", background=palette.get("card", "#FFFFFF"), foreground=palette.get("text", "#000000"),
                    font=(font_family, TOKENS["font_body"]))
    style.configure("TButton", font=(font_family, TOKENS["font_body"], "bold"),
                    padding=(12, 8), borderwidth=0,
                    background=palette.get("card", "#FFFFFF"), foreground=palette.get("text", "#000000"))
    style.configure("Accent.TButton", background=palette.get("accent", "#3867E8"), foreground="#FFFFFF")
    style.configure("TEntry", fieldbackground=palette.get("card", "#FFFFFF"), foreground=palette.get("text", "#000000"),
                    insertcolor=palette.get("text", "#000000"), bordercolor=palette.get("border", "#CCCCCC"), padding=(10, 7))
    style.configure("Treeview", background=palette.get("card", "#FFFFFF"), foreground=palette.get("text", "#000000"),
                    fieldbackground=palette.get("card", "#FFFFFF"), rowheight=34,
                    bordercolor=palette.get("border", "#CCCCCC"), font=(font_family, TOKENS["font_body"]))
    style.configure("Treeview.Heading", background=palette.get("sidebar", "#FFFFFF"),
                    foreground=palette.get("muted", "#888888"), font=(font_family, 9, "bold"),
                    padding=(10, 9))
    style.map("Treeview", background=[("selected", palette.get("accent", "#3867E8"))], foreground=[("selected", "white")])

def configure_ttk(style: ttk.Style, palette_name="light"):
    palette = premium_palette(palette_name)
    apply_ttk_styles(style, palette, font_family=TOKENS["font_family"])

# ==== توابع سازگاری (حالا هم رشته و هم دیکشنری قبول می‌کنن) ====
def style_toplevel(window, palette="light"):
    p = premium_palette(palette)
    try:
        window.configure(bg=p["bg"])
    except Exception:
        pass

def style_label(label, palette="light"):
    p = premium_palette(palette)
    try:
        label.configure(bg=p["bg"], fg=p["text"])
    except Exception:
        pass

def style_frame(frame, palette="light"):
    p = premium_palette(palette)
    try:
        frame.configure(bg=p["bg"])
    except Exception:
        pass

def style_button(button, palette="light"):
    p = premium_palette(palette)
    try:
        button.configure(bg=p["accent"], fg="#FFFFFF")
    except Exception:
        pass

def style_entry(entry, palette="light"):
    p = premium_palette(palette)
    try:
        entry.configure(bg=p["card"], fg=p["text"], insertbackground=p["text"])
    except Exception:
        pass