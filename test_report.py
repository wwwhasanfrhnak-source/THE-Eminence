# test_report.py
from electrocalc.core import report_builder as rb

# تست گیج
buf = rb.build_gauge_chart(50, 100, "پروژه‌ها", "#7c3aed", "عدد")
with open("test_gauge.png", "wb") as f:
    f.write(buf.read())
print("✅ test_gauge.png ساخته شد")

# تست پای‌چارت
buf = rb.build_pie_chart([("فعال", 5), ("تمام‌شده", 3)], "وضعیت پروژه‌ها")
with open("test_pie.png", "wb") as f:
    f.write(buf.read())
print("✅ test_pie.png ساخته شد")

# تست PDF کامل
path = rb.build_dashboard_pdf()
print(f"✅ PDF ساخته شد: {path}")