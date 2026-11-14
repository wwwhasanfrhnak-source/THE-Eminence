import os
import re

def fix():
    p = 'electrocalc/ui/main_window.py'
    with open(p, 'r', encoding='utf-8') as f:
        c = f.read()

    # اطمینان از ایمپورت
    if 'from PIL import Image, ImageTk' not in c:
        c = 'from PIL import Image, ImageTk\n' + c

    # ۱. منوی همبرگری
    c = c.replace('text="☰"', 'text=""')
    if 'self._toggle_sidebar_btn.pack' in c:
        c = c.replace('self._toggle_sidebar_btn.pack(side="left", padx=(0, 9), pady=12)',
                      '''self._toggle_sidebar_btn.pack(side="left", padx=(0, 9), pady=12)
        try:
            base_dir = os.getcwd()
            img = Image.open(os.path.join(base_dir, "assets", "arrow_20261113205622.gif"))
            img.seek(0)
            img = img.convert("RGBA").resize((24, 24), Image.LANCZOS)
            self._menu_img = ImageTk.PhotoImage(img)
            self._toggle_sidebar_btn.configure(image=self._menu_img)
        except Exception as e:
            self._toggle_sidebar_btn.configure(text="☰")''')

    # ۲. آیکون جستجو
    c = c.replace('text="🔍"', 'text=""')
    if 'search_icon.pack(side="right")' in c:
        c = c.replace('search_icon.pack(side="right")',
                      '''search_icon.pack(side="right")
        try:
            base_dir = os.getcwd()
            img = Image.open(os.path.join(base_dir, "assets", "loupe.png")).convert("RGBA").resize((20, 20), Image.LANCZOS)
            self._search_img = ImageTk.PhotoImage(img)
            search_icon.configure(image=self._search_img)
        except Exception as e:
            search_icon.configure(text="🔍")''')

    # ۳. زنگوله اعلان‌ها
    bell_pattern = r'self\._bell_label\s*=\s*action_label\(\s*right,\s*"🔔",\s*self\._show_notifications,\s*width=3\s*\)'
    c = re.sub(bell_pattern, '', c)

    if 'self._bell_label = action_label' not in c and 'self._bell_label = tk.Label' not in c:
        bell_insert = '''try:
            base_dir = os.getcwd()
            img = Image.open(os.path.join(base_dir, "assets", "news.png")).convert("RGBA").resize((24, 24), Image.LANCZOS)
            self._news_icon = ImageTk.PhotoImage(img)
            self._bell_label = tk.Label(right, image=self._news_icon, bg=p["card"], cursor="hand2")
            self._bell_label.pack(side="right", pady=12, padx=10)
            self._bell_label.bind("<Button-1>", lambda e: self._show_notifications())
            self._bell_label.bind("<Enter>", lambda e: self._bell_label.configure(bg=p["active_bg"]))
            self._bell_label.bind("<Leave>", lambda e: self._bell_label.configure(bg=p["card"]))
        except Exception as e:
            print(f"News icon error: {e}")
            self._bell_label = action_label(right, "🔔", self._show_notifications, width=3)
'''
        c = c.replace('action_label(right, "⋯", self._show_header_menu, width=3)', bell_insert + '\n        action_label(right, "⋯", self._show_header_menu, width=3)')

    with open(p, 'w', encoding='utf-8') as f:
        f.write(c)
    print("✅ کدها با موفقیت اصلاح شدند! حالا برنامه را اجرا کنید.")

if __name__ == "__main__":
    fix()