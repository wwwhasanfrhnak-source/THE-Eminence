import sys
from pathlib import Path

# اضافه کردن مسیر پروژه به sys.path
sys.path.insert(0, str(Path(__file__).parent))

from electrocalc.ui.login_window import LoginWindow

# اجرای صفحه لاگین
login = LoginWindow()
user = login.run()
print(f"User logged in: {user}")