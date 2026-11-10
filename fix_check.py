import re

p = 'electrocalc/ui/login_window.py'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# 1. حذف کردن Enter کیبورد
c = re.sub(r'self\.root\.bind\(.*?Return.*?\)\n', '', c)
c = re.sub(r'self\.pass_entry\.bind\(.*?Return.*?\)\n', '', c)

# 2. پیدا کردن دکمه‌های قبلی و جایگزینی با دکمه تیک
# (دکمه‌هایی که توی کد قبلی بودن رو حذف می‌کنیم)
c = c.replace('self.login_button = ttk.Button(shell, text="ورود امن  →", style="Accent.TButton", command=self._login)\n        self.login_button.pack(fill="x", pady=(15, 8), ipady=5)', 'self.check_button = ttk.Button(shell, text="✓", style="Accent.TButton", command=self._login)\n        self.check_button.pack(fill="x", pady=(15, 8), ipady=5)')

# 3. اگه دکمه ورود امن هنوز بود، اسمش رو عوض کن
c = c.replace('self.login_button', 'self.check_button')

# 4. ذخیره
with open(p, 'w', encoding='utf-8') as f:
    f.write(c)

print("✅ فایل با موفقیت اصلاح شد! حالا برنامه رو اجرا کن.")