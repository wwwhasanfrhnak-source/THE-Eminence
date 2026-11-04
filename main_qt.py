"""Light-themed Persian management dashboard for THE Eminence."""

import sys

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)


STYLE = """
QMainWindow, QWidget {
    background: #F5F7FB;
    color: #20283A;
    font-family: "Segoe UI";
    font-size: 10pt;
}
QFrame#Sidebar { background: #FFFFFF; border: 1px solid #E8ECF3; border-radius: 16px; }
QFrame#Header, QFrame#Card { background: #FFFFFF; border: 1px solid #E8ECF3; border-radius: 14px; }
QLabel#Brand { color: #6D45D8; font-size: 20pt; font-weight: 700; }
QLabel#Subtitle, QLabel#Muted, QLabel#Caption { color: #7B8496; }
QLabel#Subtitle { font-size: 8pt; }
QLabel#Title { color: #20283A; font-size: 18pt; font-weight: 700; }
QLabel#Number { color: #6D45D8; font-size: 25pt; font-weight: 700; }
QLabel#CardTitle { color: #566176; font-size: 10pt; font-weight: 600; }
QPushButton#Nav { background: transparent; color: #667085; border: 0; border-radius: 9px; padding: 12px 10px; text-align: right; }
QPushButton#Nav:hover { background: #F3F0FF; color: #6D45D8; }
QPushButton#Nav:checked { background: #F0ECFF; color: #6D45D8; border-right: 3px solid #6D45D8; font-weight: 700; }
QPushButton#Action { background: #6D45D8; color: white; border: 0; border-radius: 9px; padding: 10px 17px; font-weight: 600; }
QPushButton#Action:hover { background: #5836BF; }
QFrame#SoftCard { background: #F8F6FF; border: 1px solid #E8E1FF; border-radius: 13px; }
QProgressBar { background: #EEF0F5; border: 0; border-radius: 5px; height: 10px; text-align: center; }
QProgressBar::chunk { background: #7B57DF; border-radius: 5px; }
QTableWidget { background: #FFFFFF; alternate-background-color: #F8F9FC; border: 1px solid #E8ECF3; border-radius: 10px; gridline-color: #EDF0F5; }
QHeaderView::section { background: #F5F6FA; color: #596477; padding: 9px; border: 0; font-weight: 600; }
"""


class TrendChart(QWidget):
    """Small dependency-free chart for weekly/monthly dashboard trends."""

    def __init__(self, title, labels, values, parent=None):
        super().__init__(parent)
        self.title = title
        self.labels = labels
        self.values = values
        self.setMinimumHeight(220)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("white"))
        left, right, top, bottom = 38, self.width() - 18, 30, self.height() - 30
        painter.setPen(QColor("#20283A"))
        painter.setFont(QFont("Segoe UI", 10, QFont.DemiBold))
        painter.drawText(0, 20, self.width(), 22, Qt.AlignRight, self.title)

        chart_top, chart_bottom = top + 18, bottom - 18
        for i in range(4):
            y = chart_top + i * (chart_bottom - chart_top) / 3
            painter.setPen(QPen(QColor("#EEF0F5"), 1))
            painter.drawLine(QPointF(left, y), QPointF(right, y))
        maximum = max(self.values) if self.values else 1
        points = []
        for i, value in enumerate(self.values):
            x = left + i * (right - left) / max(1, len(self.values) - 1)
            y = chart_bottom - (value / maximum) * (chart_bottom - chart_top)
            points.append(QPointF(x, y))
        if len(points) > 1:
            painter.setPen(QPen(QColor("#7651D5"), 3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            for first, second in zip(points, points[1:]):
                painter.drawLine(first, second)
        painter.setBrush(QColor("#7651D5"))
        painter.setPen(Qt.NoPen)
        for point in points:
            painter.drawEllipse(point, 4, 4)
        painter.setPen(QColor("#8991A1"))
        painter.setFont(QFont("Segoe UI", 8))
        for i, label in enumerate(self.labels):
            x = left + i * (right - left) / max(1, len(self.labels) - 1)
            painter.drawText(QRectF(x - 25, chart_bottom + 7, 50, 18), Qt.AlignHCenter, label)


class EminenceWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("THE Eminence | پنل مدیریت")
        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)
        self.pages = QStackedWidget()
        self.nav_buttons = []
        self.page_titles = ["داشبورد مدیریتی", "مدیریت پروژه‌ها", "مدیریت کارکنان", "مدیریت مالی", "انبار و تجهیزات", "مشتریان", "گزارش‌ها"]
        self.build_ui()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(245)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(16, 24, 16, 18)
        brand = QLabel("THE Eminence")
        brand.setObjectName("Brand")
        subtitle = QLabel("سامانه مدیریت حرفه‌ای")
        subtitle.setObjectName("Subtitle")
        side.addWidget(brand)
        side.addWidget(subtitle)
        side.addSpacing(25)
        nav = ["⌂   داشبورد", "▦   پروژه‌ها", "♙   کارکنان", "◈   امور مالی", "▤   انبار و تجهیزات", "◉   مشتریان", "▧   گزارش‌ها"]
        for index, text in enumerate(nav):
            button = QPushButton(text)
            button.setObjectName("Nav")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, i=index: self.change_page(i))
            side.addWidget(button)
            self.nav_buttons.append(button)
        side.addStretch()
        footer = QLabel("نسخه مدیریتی  •  ۲.۰")
        footer.setObjectName("Muted")
        footer.setAlignment(Qt.AlignCenter)
        side.addWidget(footer)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)
        header = QFrame()
        header.setObjectName("Header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 13, 20, 13)
        self.header_title = QLabel(self.page_titles[0])
        self.header_title.setObjectName("Title")
        status = QLabel("●  سیستم آماده است")
        status.setStyleSheet("color:#25936A;font-weight:600")
        header_layout.addWidget(self.header_title)
        header_layout.addStretch()
        header_layout.addWidget(status)
        content_layout.addWidget(header)

        self.pages.addWidget(self.dashboard_page())
        for title in self.page_titles[1:]:
            self.pages.addWidget(self.management_page(title))
        content_layout.addWidget(self.pages, 1)
        root.addWidget(sidebar)
        root.addWidget(content, 1)
        self.change_page(0)

    def scroll_page(self, body):
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        area.setWidget(body)
        return area

    def card(self, title, value, caption, accent="#6D45D8"):
        frame = QFrame()
        frame.setObjectName("Card")
        frame.setMinimumHeight(128)
        box = QVBoxLayout(frame)
        box.setContentsMargins(18, 15, 18, 15)
        heading = QLabel(title)
        heading.setObjectName("CardTitle")
        number = QLabel(value)
        number.setObjectName("Number")
        number.setStyleSheet(f"color:{accent}")
        note = QLabel(caption)
        note.setObjectName("Caption")
        box.addWidget(heading)
        box.addWidget(number)
        box.addWidget(note)
        return frame

    def section_card(self, title):
        frame = QFrame()
        frame.setObjectName("Card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(17, 14, 17, 15)
        label = QLabel(title)
        label.setObjectName("CardTitle")
        layout.addWidget(label)
        return frame, layout

    def dashboard_page(self):
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(3, 5, 3, 10)
        layout.setSpacing(14)
        title = QLabel("نمای کلی کسب‌وکار")
        title.setObjectName("Title")
        description = QLabel("خلاصه‌ای از پروژه‌ها، امور مالی و فعالیت‌های اخیر")
        description.setObjectName("Muted")
        layout.addWidget(title)
        layout.addWidget(description)

        grid = QGridLayout()
        grid.setSpacing(12)
        metrics = [
            ("پروژه‌های فعال", "۱۲", "۳ پروژه در حال اجرا"),
            ("مشتریان", "۴۸", "۵ مشتری جدید این ماه", "#279773"),
            ("درآمد کل", "۸۴۵ م.ت", "↑ ۱۲٪ نسبت به ماه قبل", "#279773"),
            ("هزینه‌ها", "۲۱۸ م.ت", "هزینه‌های ثبت‌شده", "#D18B26"),
            ("سفارش‌های در انتظار", "۷", "نیازمند پیگیری", "#D18B26"),
            ("درخواست‌های جدید", "۵", "۲ مورد فوری", "#D65A68"),
        ]
        for i, item in enumerate(metrics):
            grid.addWidget(self.card(*item), i // 3, i % 3)
        layout.addLayout(grid)

        charts = QHBoxLayout()
        weekly, weekly_layout = self.section_card("روند درآمد هفتگی")
        weekly_layout.addWidget(TrendChart("درآمد (میلیون تومان)", ["ش", "ی", "د", "س", "چ", "پ", "ج"], [22, 35, 29, 48, 41, 63, 55]))
        monthly, monthly_layout = self.section_card("درآمد ماهانه")
        monthly_layout.addWidget(TrendChart("عملکرد ۶ ماه اخیر", ["فر", "ار", "خرد", "تیر", "مرد", "شهر"], [30, 42, 38, 58, 51, 72]))
        charts.addWidget(weekly, 1)
        charts.addWidget(monthly, 1)
        layout.addLayout(charts)

        lower = QHBoxLayout()
        projects, project_layout = self.section_card("وضعیت پروژه‌ها")
        for name, percent, color in [("در حال اجرا", 58, "#6D45D8"), ("تکمیل‌شده", 30, "#279773"), ("در انتظار", 12, "#D18B26")]:
            row = QHBoxLayout()
            label = QLabel(name)
            label.setObjectName("Muted")
            amount = QLabel(f"{percent}%")
            amount.setObjectName("CardTitle")
            row.addWidget(label)
            row.addStretch()
            row.addWidget(amount)
            project_layout.addLayout(row)
            progress = QProgressBar()
            progress.setRange(0, 100)
            progress.setValue(percent)
            progress.setTextVisible(False)
            progress.setStyleSheet(f"QProgressBar::chunk{{background:{color};border-radius:5px}}")
            project_layout.addWidget(progress)
        alerts, alert_layout = self.section_card("هشدارهای هوشمند")
        for message in ["۲ فاکتور سررسیدشده برای پیگیری", "موجودی کابل برق به حداقل رسیده است", "پروژه برج آفتاب نزدیک موعد تحویل است"]:
            item = QLabel("•  " + message)
            item.setWordWrap(True)
            item.setStyleSheet("color:#596477;padding:6px")
            alert_layout.addWidget(item)
        lower.addWidget(projects, 1)
        lower.addWidget(alerts, 1)
        layout.addLayout(lower)

        activity, activity_layout = self.section_card("فعالیت‌های اخیر")
        table = self.make_table(["فعالیت", "مسئول", "زمان", "وضعیت"], [
            ["ثبت پرداخت فاکتور #۱۰۴۲", "سارا احمدی", "امروز، ۱۰:۲۰", "تکمیل‌شده"],
            ["به‌روزرسانی پیشرفت پروژه آفتاب", "علی رضایی", "امروز، ۰۹:۴۵", "ثبت‌شده"],
            ["درخواست خرید تجهیزات", "مهدی کریمی", "دیروز، ۱۵:۱۰", "در انتظار"],
        ])
        activity_layout.addWidget(table)
        layout.addWidget(activity)
        return self.scroll_page(body)

    def make_table(self, headers, rows):
        table = QTableWidget(len(rows), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                table.setItem(r, c, QTableWidgetItem(value))
        table.setMinimumHeight(155)
        return table

    def management_page(self, title):
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(3, 5, 3, 10)
        layout.setSpacing(14)
        heading = QLabel(title)
        heading.setObjectName("Title")
        layout.addWidget(heading)
        descriptions = {
            "مدیریت پروژه‌ها": "پروژه‌های فعال و تکمیل‌شده، میزان پیشرفت، مسئول، زمان‌بندی و وضعیت مالی.",
            "مدیریت کارکنان": "فهرست کارکنان، سمت و سطح دسترسی، وظایف روزانه، ساعات کاری و عملکرد.",
            "مدیریت مالی": "درآمد و هزینه، سود و زیان، فاکتورها، بدهی مشتریان و پرداخت‌های دریافتی.",
            "انبار و تجهیزات": "موجودی تجهیزات، ورود و خروج کالا، هشدار کمبود و درخواست خرید.",
            "مشتریان": "اطلاعات مشتریان، پروژه‌های مرتبط، مانده‌حساب و سوابق همکاری.",
            "گزارش‌ها": "گزارش‌های مدیریتی و مالی برای بازه زمانی انتخاب‌شده.",
        }
        intro = QLabel(descriptions.get(title, "مدیریت و پیگیری اطلاعات سامانه."))
        intro.setObjectName("Muted")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        stats = QGridLayout()
        summaries = {
            "مدیریت پروژه‌ها": [("پروژه‌های فعال", "۱۲"), ("تکمیل‌شده", "۳۶"), ("در انتظار", "۴")],
            "مدیریت کارکنان": [("کارکنان", "۲۴"), ("حاضر امروز", "۲۰"), ("وظایف باز", "۱۱")],
            "مدیریت مالی": [("درآمد این ماه", "۱۴۲ م.ت"), ("هزینه این ماه", "۳۸ م.ت"), ("مطالبات", "۲۶ م.ت")],
            "انبار و تجهیزات": [("اقلام انبار", "۱۸۶"), ("کم‌موجودی", "۳"), ("درخواست خرید", "۵")],
            "مشتریان": [("کل مشتریان", "۴۸"), ("مشتری فعال", "۳۱"), ("مانده مطالبات", "۲۶ م.ت")],
            "گزارش‌ها": [("گزارش‌های آماده", "۸"), ("این ماه", "۱۲"), ("آخرین خروجی", "امروز")],
        }
        for i, (name, value) in enumerate(summaries.get(title, [])):
            stats.addWidget(self.card(name, value, "اطلاعات نمونه نمایشی"), 0, i)
        layout.addLayout(stats)
        actions = QHBoxLayout()
        actions.addStretch()
        add_button = QPushButton("＋  افزودن مورد جدید")
        add_button.setObjectName("Action")
        actions.addWidget(add_button)
        layout.addLayout(actions)

        table_titles = {
            "مدیریت پروژه‌ها": ("پروژه", "مسئول", "پیشرفت", "موعد پایان", "وضعیت پرداخت"),
            "مدیریت کارکنان": ("نام کارمند", "سمت", "سطح دسترسی", "وظیفه امروز", "وضعیت"),
            "مدیریت مالی": ("شرح", "نوع", "مبلغ", "سررسید", "وضعیت"),
            "انبار و تجهیزات": ("کالا", "دسته‌بندی", "موجودی", "حداقل موجودی", "وضعیت"),
            "مشتریان": ("نام مشتری", "تلفن", "پروژه‌های فعال", "مانده حساب", "وضعیت"),
            "گزارش‌ها": ("عنوان گزارش", "دسته‌بندی", "بازه زمانی", "تاریخ ایجاد", "وضعیت"),
        }.get(title, ("عنوان", "دسته‌بندی", "جزئیات", "تاریخ", "وضعیت"))
        demo_rows = {
            "مدیریت پروژه‌ها": [["ساختمان اداری آفتاب", "علی رضایی", "۷۵٪", "۱۴۰۵/۰۹/۲۰", "پرداخت مرحله‌ای"], ["توسعه شبکه برق", "مریم کریمی", "۴۰٪", "۱۴۰۵/۱۰/۰۵", "تسویه‌شده"]],
            "مدیریت کارکنان": [["علی رضایی", "مدیر پروژه", "مدیر", "بازبینی پروژه آفتاب", "فعال"], ["سارا احمدی", "حسابدار", "مالی", "پیگیری فاکتورها", "فعال"]],
            "مدیریت مالی": [["فاکتور #۱۰۴۲", "دریافتی", "۲۴,۰۰۰,۰۰۰ تومان", "۱۴۰۵/۰۸/۲۸", "دریافت‌شده"], ["تجهیزات پروژه آفتاب", "هزینه", "۸,۵۰۰,۰۰۰ تومان", "۱۴۰۵/۰۸/۳۰", "ثبت‌شده"]],
            "انبار و تجهیزات": [["کابل برق ۲.۵", "کابل", "۱۸ حلقه", "۲۰ حلقه", "کم‌موجودی"], ["کلید مینیاتوری", "تجهیزات", "۷۲ عدد", "۳۰ عدد", "موجود"]],
            "مشتریان": [["شرکت توسعه آفتاب", "۰۲۱-۱۲۳۴۵۶۷۸", "۲", "۱۲ م.ت", "فعال"], ["گروه ساختمانی سپهر", "۰۲۱-۸۷۶۵۴۳۲۱", "۱", "تسویه", "فعال"]],
            "گزارش‌ها": [["خلاصه عملکرد پروژه‌ها", "پروژه", "ماهانه", "امروز", "آماده"], ["درآمد و هزینه", "مالی", "ماهانه", "دیروز", "آماده"]],
        }.get(title, [])
        table_frame, table_layout = self.section_card("فهرست " + title)
        table_layout.addWidget(self.make_table(table_titles, demo_rows))
        layout.addWidget(table_frame)
        layout.addStretch()
        return self.scroll_page(body)

    def change_page(self, index):
        self.pages.setCurrentIndex(index)
        self.header_title.setText(self.page_titles[index])
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)


def main():
    app = QApplication(sys.argv)
    app.setLayoutDirection(Qt.RightToLeft)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    window = EminenceWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
