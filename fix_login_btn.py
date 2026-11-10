import re

p = 'electrocalc/ui/login_window.py'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. حذف کردن دکمه‌های قبلی (اگه وجود دارن)
c = re.sub(r'self\.(login_button|check_button|enter_btn)\s*=.*?\n\s*self\.(login_button|check_button|enter_btn)\.pack\(.*?\)\n', '', c)

# 2. اضافه کردن دکمه تیک جدید
btn_code = '''
        self.check_button = ttk.Button(shell, text="✓", style="Accent.TButton", command=self._login)
        self.check_button.pack(fill="x", pady=(10, 8), ipady=5)
'''

# پیدا کردن جای مناسب برای اضافه کردن دکمه (بعد از انیمیشن)
if 'self.anim_frame.pack' in c:
    c = c.replace('self.anim_frame.pack(fill="x", pady=(5, 0))\n        self.anim_frame.pack_propagate(False) \n        self.anim_label = tk.Label(self.anim_frame, bg=p["bg"])\n        self.anim_label.pack(expand=True)', 'self.anim_frame.pack(fill="x", pady=(5, 0))\n        self.anim_frame.pack_propagate(False) \n        self.anim_label = tk.Label(self.anim_frame, bg=p["bg"])\n        self.anim_label.pack(expand=True)\n' + btn_code)
else:
    # اگه پیدا نشد، بعد از فرم اضافه کن
    c = c.replace('self.pass_entry.pack(fill="x", pady=(4, 4), ipady=5)', 'self.pass_entry.pack(fill="x", pady=(4, 4), ipady=5)\n' + btn_code)

# 3. اطمینان از اینکه Enter کیبورد کار می‌کنه
if 'self.root.bind("<Return>"' not in c:
    c = c.replace('self.root.protocol("WM_DELETE_WINDOW", self._cancel)', 'self.root.bind("<Return>", lambda event: self._login())\n        self.root.protocol("WM_DELETE_WINDOW", self._cancel)')

# 4. ذخیره
with open(p, 'w', encoding='utf-8') as f:
    f.write(c)

print("✅ دکمه تیک اضافه شد و Enter کیبورد هم فعال شد!")