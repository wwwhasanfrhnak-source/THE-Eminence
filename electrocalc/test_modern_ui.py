import customtkinter as ctk

# تنظیم تم پیش‌فرض
ctk.set_appearance_mode("Dark")  # حالت تیره
ctk.set_default_color_theme("blue")  # تم رنگی

class ModernApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("THE Eminence - Modern Test")
        self.geometry("800x500")

        # سایدبار (مدرن)
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")

        # دکمه‌های سایدبار
        self.btn_dashboard = ctk.CTkButton(self.sidebar, text="داشبورد", corner_radius=8)
        self.btn_dashboard.pack(pady=20, padx=20, fill="x")
        
        self.btn_projects = ctk.CTkButton(self.sidebar, text="پروژه‌ها", corner_radius=8)
        self.btn_projects.pack(pady=10, padx=20, fill="x")

        # بخش اصلی
        self.main_frame = ctk.CTkFrame(self, corner_radius=15)
        self.main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # کارت آمار (مدرن)
        self.card = ctk.CTkFrame(self.main_frame, corner_radius=15)
        self.card.pack(pady=20, padx=20, fill="x")

        self.label = ctk.CTkLabel(self.card, text="کل درآمد", font=("Vazirmatn", 20, "bold"))
        self.label.pack(pady=10, padx=20, anchor="e")

        self.value = ctk.CTkLabel(self.card, text="28,340,000 تومان", font=("Vazirmatn", 30, "bold"), text_color="#f97316")
        self.value.pack(pady=10, padx=20, anchor="e")

if __name__ == "__main__":
    app = ModernApp()
    app.mainloop()