p = 'electrocalc/ui/login_window.py'
with open(p, 'r', encoding='utf-8') as f:
    c = f.read()

# حذف کلمه assets از مسیرها (اگر هست)
c = c.replace('os.path.join(base_dir, "assets", ', 'os.path.join(base_dir, ')
c = c.replace('os.path.join(base_dir, "assets", gif_name)', 'os.path.join(base_dir, gif_name)')

# اضافه کردن assets به مسیرها (اگر نیست)
if 'os.path.join(base_dir, "news.png")' in c:
    c = c.replace('os.path.join(base_dir, "news.png")', 'os.path.join(base_dir, "assets", "news.png")')
if 'os.path.join(base_dir, gif_name)' in c:
    c = c.replace('os.path.join(base_dir, gif_name)', 'os.path.join(base_dir, "assets", gif_name)')

with open(p, 'w', encoding='utf-8') as f:
    f.write(c)

print("✅ مسیرها اصلاح شدند! حالا برنامه رو اجرا کن.")