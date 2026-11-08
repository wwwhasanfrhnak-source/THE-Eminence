import ttkbootstrap as ttk
from ttkbootstrap.constants import *

app = ttk.Window(themename="darkly")  # تم تیره و مدرن
app.title("THE Eminence - Modern Test")
app.geometry("800x500")

# سایدبار
sidebar = ttk.Frame(app, bootstyle="dark", width=200)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

ttk.Label(sidebar, text="⚡ THE Eminence", bootstyle="inverse-dark", font=("Vazirmatn", 14, "bold")).pack(pady=20)
ttk.Button(sidebar, text="داشبورد", bootstyle="primary").pack(pady=5, padx=10, fill="x")
ttk.Button(sidebar, text="پروژه‌ها", bootstyle="secondary").pack(pady=5, padx=10, fill="x")
ttk.Button(sidebar, text="مالی پروژه", bootstyle="success").pack(pady=5, padx=10, fill="x")

# محتوای اصلی
main_frame = ttk.Frame(app, padding=20)
main_frame.pack(side="right", fill="both", expand=True)

# کارت KPI
card = ttk.Frame(main_frame, bootstyle="dark", padding=20)
card.pack(fill="x", pady=10)

ttk.Label(card, text="کل درآمد", bootstyle="inverse-dark", font=("Vazirmatn", 12)).pack(anchor="e")
ttk.Label(card, text="28,340,000 تومان", bootstyle="warning", font=("Vazirmatn", 20, "bold")).pack(anchor="e", pady=5)

# جدول
table = ttk.Treeview(main_frame, columns=("name", "value"), show="headings", bootstyle="dark")
table.heading("name", text="پروژه")
table.heading("value", text="درآمد")
table.pack(fill="both", expand=True, pady=10)
table.insert("", "end", values=("مسکن ملی", "28,340,000"))
table.insert("", "end", values=("امتحان", "0"))

app.mainloop()