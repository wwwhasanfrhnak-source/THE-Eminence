"""Shared THE Eminence desktop design tokens and ttk styling helpers."""

from tkinter import ttk

TOKENS = {
    "font_family": "Segoe UI",
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

# Premium base palettes are deliberately limited to the standard light/dark
# choices. The application's named color themes retain their original identity.
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
        "success": "#168A65", "danger": "#C83E4D", "status_bar": "#EAF0F8",
    },
    "windows11_dark": {
        "bg": "#0D1420", "sidebar": "#121D2C", "card": "#182538",
        "border": "#2A3A51", "accent": "#55A5F5", "text": "#F2F6FC",
        "muted": "#A1AEC0", "h_start": "#173D68", "h_end": "#087B9C",
        "success": "#55C994", "danger": "#FF818B", "status_bar": "#0A111C",
    },
}


def premium_palette(name, base):
    """Return a fresh palette, upgrading standard themes without mutating source data."""
    result = dict(base)
    result.update(PREMIUM_PALETTES.get(name, {}))
    return result


def configure_ttk(style, palette):
    """Apply consistent typography, states and surfaces to ttk controls."""
    style.theme_use("clam")
    font = (TOKENS["font_family"], TOKENS["font_body"])
    style.configure("TFrame", background=palette["bg"])
    style.configure("Surface.TFrame", background=palette["card"])
    style.configure("TLabel", background=palette["bg"], foreground=palette["text"], font=font)
    style.configure("Surface.TLabel", background=palette["card"], foreground=palette["text"], font=font)
    style.configure("Muted.TLabel", background=palette["bg"], foreground=palette["muted"], font=font)
    style.configure("Title.TLabel", background=palette["bg"], foreground=palette["text"],
                    font=(TOKENS["font_family"], TOKENS["font_title"], "bold"))
    style.configure("TLabelframe", background=palette["card"], bordercolor=palette["border"],
                    relief="solid", padding=TOKENS["space_md"])
    style.configure("TLabelframe.Label", background=palette["card"], foreground=palette["accent"],
                    font=(TOKENS["font_family"], TOKENS["font_section"], "bold"))
    style.configure("TButton", font=(TOKENS["font_family"], TOKENS["font_body"], "bold"),
                    padding=(TOKENS["space_md"], TOKENS["space_sm"]), borderwidth=0,
                    background=palette["card"], foreground=palette["text"])
    style.map("TButton", background=[("active", palette["border"]), ("pressed", palette["border"])],
              foreground=[("disabled", palette["muted"])])
    style.configure("Accent.TButton", background=palette["accent"], foreground="#FFFFFF")
    style.map("Accent.TButton", background=[("active", palette["h_end"]), ("pressed", palette["h_start"])])
    style.configure("TEntry", padding=(TOKENS["space_sm"], TOKENS["space_sm"]),
                    fieldbackground=palette["card"], foreground=palette["text"],
                    bordercolor=palette["border"], insertcolor=palette["text"])
    style.configure("TCombobox", padding=(TOKENS["space_sm"], 6),
                    fieldbackground=palette["card"], foreground=palette["text"],
                    bordercolor=palette["border"])
    style.configure("Treeview", background=palette["card"], foreground=palette["text"],
                    fieldbackground=palette["card"], rowheight=34, bordercolor=palette["border"],
                    font=font)
    style.configure("Treeview.Heading", background=palette["sidebar"], foreground=palette["muted"],
                    font=(TOKENS["font_family"], TOKENS["font_small"], "bold"), padding=10)
    style.map("Treeview", background=[("selected", palette["accent"])],
              foreground=[("selected", "#FFFFFF")])
    style.configure("TScrollbar", background=palette["border"], troughcolor=palette["bg"],
                    bordercolor=palette["bg"], arrowsize=12)


def style_toplevel(window, palette):
    """Apply the shared app surface to a Tk/Toplevel window."""
    window.configure(bg=palette["bg"])


def style_label(widget, palette, role="body"):
    """Apply a palette-aware style to a classic Tk label."""
    options = {"bg": palette["bg"], "fg": palette["text"], "font": (TOKENS["font_family"], TOKENS["font_body"])}
    if role == "muted":
        options["fg"] = palette["muted"]
    elif role == "title":
        options["font"] = (TOKENS["font_family"], TOKENS["font_title"], "bold")
    elif role == "brand":
        options.update(fg=palette["accent"], font=(TOKENS["font_family"], TOKENS["font_title"], "bold"))
    widget.configure(**options)
    return widget
