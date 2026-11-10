p = 'electrocalc/ui/login_window.py'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# پیدا کردن جای دکمه‌های قبلی و حذفشون
import re
c = re.sub(r'self\.(login_button|check_button|enter_btn)\s*=.*?\n\s*self\.(login_button|check_button|enter_btn)\.pack\(.*?\)\n', '', c)

# اضافه کردن دکمه Enter جدید دقیقاً بعد از انیمیشن
btn_code = '''
        self.enter_btn = ttk.Button(shell, text="Enter", style="Accent.TButton", command=self._login)
        self.enter_btn.pack(fill="x", pady=(10, 8), ipady=5)
'''

# پیدا کردن جای مناسب (بعد از انیمیشن)
old_anim = 'self.anim_label = tk.Label(self.anim_frame, bg=p["bg"])\n        self.anim_label.pack(expand=True)'
new_anim = old_anim + '\n' + btn_code

c = c.replace(old_anim, new_anim)

# اگر پیدا نشد، بعد از رمز عبور اضافه کن
if 'self.enter_btn' not in c:
    c = c.replace('self.pass_entry.pack(fill="x", pady=(4, 4), ipady=5)', 'self.pass_entry.pack(fill="x", pady=(4, 4), ipady=5)\n' + btn_code)

# اطمینان از اینکه Enter کیبورد هم کار می‌کنه
if 'self.root.bind("<Return>"' not in c:
    c = c.replace('self.root.protocol("WM_DELETE_WINDOW", self._cancel)', 'self.root.bind("<Return>", lambda event: self._login())\n        self.root.protocol("WM_DELETE_WINDOW", self._cancel)')

# ذخیره
with open(p, 'w', encoding='utf-8') as f:
    f.write(c)

print("✅ دکمه Enter بالای صفحه اضافه شد!")