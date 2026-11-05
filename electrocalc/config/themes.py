"""تم‌های رنگی برنامه — ۱۴ تم + آیکون‌های اختصاصی."""


# آیکون‌های پیش‌فرض
DEFAULT_ICONS = {
    "home": "🏠", "dashboard": "📊", "projects": "📁",
    "reports": "📝", "timesheet": "⏰", "materials": "🔧",
    "expenses": "💰", "files": "📎", "messages": "💬",
    "approvals": "✅", "education": "🎓",
    "ohm": "⚡", "power": "💡", "voltage": "📉",
    "ampacity": "🔌", "fuse": "🔒", "motor": "⚙️",
    "units": "🔄",
    "users": "👥", "company": "🏢", "backup": "💾",
    "audit": "📝", "health": "🛡️", "settings": "⚙️",
}


THEMES = {
    "light": {
        "name": "☀️  روشن",
        "bg": "#F7F9FC", "sidebar": "#FFFFFF", "card": "#FFFFFF",
        "border": "#E5EAF2", "accent": "#2563EB",
        "secondary": "#0891B2", "active_bg": "#EFF6FF",
        "text": "#172033", "muted": "#66758B",
        "h_start": "#2563EB", "h_end": "#0891B2",
        "success": "#10b981", "danger": "#ef4444",
        "status_bar": "#FFFFFF",
        "icons": DEFAULT_ICONS,
    },
    "dark": {
        "name": "🌙  تاریک",
        "bg": "#0f0f1e", "sidebar": "#1a1a2e", "card": "#1e1e35",
        "border": "#2d2d4a", "accent": "#7c3aed",
        "text": "#e4e4e7", "muted": "#71717a",
        "h_start": "#7c3aed", "h_end": "#06b6d4",
        "success": "#4ecca3", "danger": "#e94560",
        "status_bar": "#0f1729",
        "icons": {
            **DEFAULT_ICONS,
            "home": "🌃", "dashboard": "🌙", "settings": "🔮",
        },
    },
    "ocean": {
        "name": "🌊  اقیانوس",
        "bg": "#f0f9ff", "sidebar": "#ffffff", "card": "#ffffff",
        "border": "#bae6fd", "accent": "#0284c7",
        "text": "#0c4a6e", "muted": "#0369a1",
        "h_start": "#0284c7", "h_end": "#06b6d4",
        "success": "#059669", "danger": "#dc2626",
        "status_bar": "#e0f2fe",
        "icons": {
            **DEFAULT_ICONS,
            "home": "🌊", "projects": "⛵", "materials": "⚓",
            "ampacity": "🐟", "motor": "🚢", "settings": "🧭",
        },
    },
    "forest": {
        "name": "🌲  جنگل",
        "bg": "#f0fdf4", "sidebar": "#ffffff", "card": "#ffffff",
        "border": "#bbf7d0", "accent": "#15803d",
        "text": "#14532d", "muted": "#166534",
        "h_start": "#15803d", "h_end": "#22c55e",
        "success": "#15803d", "danger": "#dc2626",
        "status_bar": "#dcfce7",
        "icons": {
            **DEFAULT_ICONS,
            "home": "🌳", "projects": "🌱", "materials": "🪵",
            "power": "🍃", "motor": "🌾", "settings": "🍀",
        },
    },
    "sunset": {
        "name": "🌅  غروب",
        "bg": "#fff7ed", "sidebar": "#ffffff", "card": "#ffffff",
        "border": "#fed7aa", "accent": "#ea580c",
        "text": "#7c2d12", "muted": "#9a3412",
        "h_start": "#ea580c", "h_end": "#f59e0b",
        "success": "#059669", "danger": "#dc2626",
        "status_bar": "#ffedd5",
        "icons": {
            **DEFAULT_ICONS,
            "home": "🏜️", "power": "🌅", "motor": "🔥",
            "education": "📖", "settings": "☕",
        },
    },
    "purple": {
        "name": "💜  بنفش",
        "bg": "#faf5ff", "sidebar": "#ffffff", "card": "#ffffff",
        "border": "#e9d5ff", "accent": "#7c3aed",
        "text": "#3b0764", "muted": "#6b21a8",
        "h_start": "#7c3aed", "h_end": "#a855f7",
        "success": "#059669", "danger": "#dc2626",
        "status_bar": "#f3e8ff",
        "icons": {
            **DEFAULT_ICONS,
            "home": "🏰", "dashboard": "🔮", "settings": "✨",
        },
    },
    "midnight": {
        "name": "🌃  نیمه‌شب",
        "bg": "#020617", "sidebar": "#0f172a", "card": "#1e293b",
        "border": "#334155", "accent": "#38bdf8",
        "text": "#e2e8f0", "muted": "#94a3b8",
        "h_start": "#0c4a6e", "h_end": "#0369a1",
        "success": "#4ade80", "danger": "#f87171",
        "status_bar": "#020617",
        "icons": {
            **DEFAULT_ICONS,
            "home": "🌌", "dashboard": "⭐", "settings": "🌙",
        },
    },
    "rose": {
        "name": "🌹  رزگلد",
        "bg": "#fff1f2", "sidebar": "#ffffff", "card": "#ffffff",
        "border": "#fecdd3", "accent": "#e11d48",
        "text": "#881337", "muted": "#9f1239",
        "h_start": "#e11d48", "h_end": "#f472b6",
        "success": "#059669", "danger": "#dc2626",
        "status_bar": "#ffe4e6",
        "icons": {
            **DEFAULT_ICONS,
            "home": "🌸", "dashboard": "💖", "education": "🌷",
            "settings": "🎀",
        },
    },
    "paper": {
        "name": "☕  کاغذی",
        "bg": "#fefce8", "sidebar": "#fef9c3", "card": "#fffbeb",
        "border": "#fde68a", "accent": "#92400e",
        "text": "#451a03", "muted": "#78350f",
        "h_start": "#a16207", "h_end": "#ca8a04",
        "success": "#65a30d", "danger": "#dc2626",
        "status_bar": "#fef3c7",
        "icons": {
            **DEFAULT_ICONS,
            "home": "📜", "projects": "📓", "reports": "✏️",
            "education": "📚", "settings": "🖋️",
        },
    },
    "neon": {
        "name": "⚡  نئون",
        "bg": "#000000", "sidebar": "#0a0a0a", "card": "#111111",
        "border": "#1f1f1f", "accent": "#00ffff",
        "text": "#ffffff", "muted": "#808080",
        "h_start": "#00ffff", "h_end": "#ff00ff",
        "success": "#00ff00", "danger": "#ff0000",
        "status_bar": "#0a0a0a",
        "icons": {
            **DEFAULT_ICONS,
            "home": "🏚️", "dashboard": "📈", "projects": "🗂️",
            "reports": "📄", "timesheet": "⏱️", "materials": "🔩",
            "expenses": "💵", "files": "📑", "messages": "📨",
            "approvals": "☑️", "education": "📕",
            "voltage": "⚡", "fuse": "🔐", "motor": "🛞",
            "units": "♻️", "users": "👤", "company": "🏛️",
            "backup": "💿", "audit": "📜", "health": "❤️",
            "settings": "🔧",
        },
    },

    # ============ ویندوز ۱۱ ============
    "windows11_light": {
        "name": "🪟  ویندوز ۱۱ (روشن)",
        "bg": "#f3f3f3", "sidebar": "#f9f9f9", "card": "#ffffff",
        "border": "#e5e5e5", "accent": "#0067c0",
        "text": "#1a1a1a", "muted": "#666666",
        "h_start": "#0067c0", "h_end": "#0078d4",
        "success": "#0f7b0f", "danger": "#c42b1c",
        "status_bar": "#f3f3f3",
        "icons": DEFAULT_ICONS,
    },
    "windows11_dark": {
        "name": "🪟  ویندوز ۱۱ (تیره)",
        "bg": "#202020", "sidebar": "#2b2b2b", "card": "#2d2d2d",
        "border": "#3a3a3a", "accent": "#4cc2ff",
        "text": "#ffffff", "muted": "#a0a0a0",
        "h_start": "#005fb8", "h_end": "#0078d4",
        "success": "#6ccb5f", "danger": "#ff99a4",
        "status_bar": "#202020",
        "icons": DEFAULT_ICONS,
    },

    # ============ ویندوز ۱۰ ============
    "windows10_light": {
        "name": "🪟  ویندوز ۱۰ (روشن)",
        "bg": "#f0f0f0", "sidebar": "#ffffff", "card": "#ffffff",
        "border": "#d1d1d1", "accent": "#0078d4",
        "text": "#000000", "muted": "#5a5a5a",
        "h_start": "#0078d4", "h_end": "#106ebe",
        "success": "#107c10", "danger": "#c42b1c",
        "status_bar": "#e6e6e6",
        "icons": {
            **DEFAULT_ICONS,
            "home": "🏠", "dashboard": "📊", "projects": "📂",
            "reports": "📋", "timesheet": "🕒", "materials": "🧰",
            "expenses": "💳", "files": "🗂️", "messages": "✉️",
            "approvals": "✔️", "education": "🎓",
            "ohm": "⚡", "power": "🔌", "voltage": "📊",
            "ampacity": "🔌", "fuse": "🔒", "motor": "⚙️",
            "units": "🔄",
            "users": "👤", "company": "🏢", "backup": "💾",
            "audit": "📋", "health": "💚", "settings": "⚙️",
        },
    },
    "windows10_dark": {
        "name": "🪟  ویندوز ۱۰ (تیره)",
        "bg": "#1f1f1f", "sidebar": "#2d2d2d", "card": "#2d2d2d",
        "border": "#404040", "accent": "#4cc2ff",
        "text": "#ffffff", "muted": "#a0a0a0",
        "h_start": "#005a9e", "h_end": "#0078d4",
        "success": "#6ccb5f", "danger": "#ff99a4",
        "status_bar": "#1a1a1a",
        "icons": {
            **DEFAULT_ICONS,
            "home": "🏡", "dashboard": "📈", "projects": "🗂️",
            "reports": "📄", "timesheet": "⏱️", "materials": "🔩",
            "expenses": "💰", "files": "📁", "messages": "📨",
            "approvals": "✅", "education": "📚",
            "ohm": "⚡", "power": "💡", "voltage": "📉",
            "ampacity": "🔌", "fuse": "🔐", "motor": "🛞",
            "units": "🔃",
            "users": "👥", "company": "🏛️", "backup": "💿",
            "audit": "📜", "health": "❤️", "settings": "🔧",
        },
    },
}


def get_palette(name):
    palette = dict(THEMES.get(name, THEMES["light"]))
    palette.setdefault("secondary", palette["h_end"])
    palette.setdefault("active_bg", palette["card"])
    return palette


def get_names():
    return list(THEMES.keys())


def get_icons(name):
    """آیکون‌های تم رو برمی‌گردونه."""
    return get_palette(name).get("icons", DEFAULT_ICONS)


def apply_to_constants(name):
    from electrocalc.config import constants as C
    t = get_palette(name)
    C.COLOR_BG = t["bg"]
    C.COLOR_HEADER_BG = t["h_start"]
    C.COLOR_HEADER_FG = "#ffffff"
    C.COLOR_ACCENT = t["accent"]
    C.COLOR_TEXT = t["text"]
    C.COLOR_MUTED = t["muted"]
    C.COLOR_SUCCESS = t["success"]
    C.COLOR_DANGER = t["danger"]
    C.COLOR_TAB_BG = t["card"]