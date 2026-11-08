import os
from pathlib import Path

# ====================================================
# ۱. اصلاح فایل main_window.py
# ====================================================
main_win_path = Path("electrocalc/ui/main_window.py")
if main_win_path.exists():
    with open(main_win_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # اضافه کردن متغیر تایمر
    if "self._refresh_job = None" not in content:
        content = content.replace(
            "self.status_var = None",
            "self.status_var = None\n        self._refresh_job = None"
        )
    
    # اضافه کردن فراخوانی به‌روزرسانی خودکار در _select_page
    if "self._start_auto_refresh()" not in content:
        content = content.replace(
            "self.current_page = idx\n",
            "self.current_page = idx\n            self._start_auto_refresh()\n"
        )
    
    # اضافه کردن توابع جدید
    if "def _start_auto_refresh" not in content:
        auto_refresh_code = """
    def _start_auto_refresh(self):
        if getattr(self, "_refresh_job", None):
            try:
                self.root.after_cancel(self._refresh_job)
            except Exception:
                pass
        def auto_refresh_loop():
            if self.current_page >= 0 and self.current_page < len(self.pages):
                page = self.pages[self.current_page]
                if hasattr(page, "refresh") and callable(getattr(page, "refresh")):
                    try:
                        page.refresh()
                    except Exception as e:
                        print(f"Auto-refresh error: {e}")
            self._refresh_job = self.root.after(2000, auto_refresh_loop)
        self._refresh_job = self.root.after(2000, auto_refresh_loop)

    def _select_page(self, idx):"""
        content = content.replace("    def _select_page(self, idx):", auto_refresh_code)
    
    with open(main_win_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("✅ main_window.py با موفقیت اصلاح شد!")

# ====================================================
# ۲. اصلاح فایل finance_tab.py (برای هماهنگی)
# ====================================================
finance_path = Path("electrocalc/ui/tabs/finance_tab.py")
if finance_path.exists():
    with open(finance_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    if "def refresh(self):" not in content:
        content = content.replace(
            "    def _on_period_change(self):",
            "    def refresh(self):\n        self._refresh()\n\n    def _on_period_change(self):"
        )
        with open(finance_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("✅ finance_tab.py با موفقیت اصلاح شد!")

print("\n🎉 همه چیز آماده است! حالا برنامه را اجرا کنید: python main.py")