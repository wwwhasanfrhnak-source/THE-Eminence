import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QFrame,
    QStackedWidget,
    QGridLayout,
)


STYLE = """
QMainWindow, QWidget {
    background-color: #101827;
    color: #F1F3F5;
    font-family: Segoe UI;
    font-size: 10pt;
}

QFrame#Sidebar {
    background-color: #151F2E;
    border-left: 1px solid #344154;
    border-radius: 14px;
}

QFrame#Header {
    background-color: #1C2636;
    border: 1px solid #344154;
    border-radius: 14px;
}

QFrame#Card {
    background-color: #1C2636;
    border: 1px solid #344154;
    border-radius: 14px;
}

QLabel#Brand {
    color: #D4AF37;
    font-size: 21pt;
    font-weight: bold;
}

QLabel#Subtitle {
    color: #9AA6B2;
    font-size: 8pt;
}

QLabel#Title {
    color: #F1F3F5;
    font-size: 19pt;
    font-weight: bold;
}

QLabel#Muted {
    color: #9AA6B2;
}

QLabel#Number {
    color: #D4AF37;
    font-size: 27pt;
    font-weight: bold;
}

QLabel#CardCaption {
    color: #9AA6B2;
    font-size: 9pt;
}

QPushButton#Nav {
    background-color: transparent;
    color: #9AA6B2;
    border: none;
    border-radius: 9px;
    padding: 14px 12px;
    text-align: right;
}

QPushButton#Nav:hover {
    background-color: #283449;
    color: #F0D77A;
}

QPushButton#Nav:checked {
    background-color: #283449;
    color: #D4AF37;
    border-right: 3px solid #D4AF37;
    font-weight: bold;
}

QPushButton#Action {
    background-color: #D4AF37;
    color: #101827;
    border: none;
    border-radius: 9px;
    padding: 11px 20px;
    font-weight: bold;
}

QPushButton#Action:hover {
    background-color: #F0D77A;
}

QFrame#WelcomeCard {
    background-color: #202D40;
    border: 1px solid #8D752E;
    border-radius: 16px;
}

QLabel#WelcomeTitle {
    color: #D4AF37;
    font-size: 17pt;
    font-weight: bold;
}

QLabel#WelcomeText {
    color: #C0CAD4;
    font-size: 10pt;
}
"""


class EminenceWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(
            "THE Eminence | Professional Electrical Management"
        )
        self.resize(1450, 900)
        self.setMinimumSize(1100, 700)

        self.pages = QStackedWidget()
        self.nav_buttons = []

        self.build_ui()

    def build_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(14)

        # SIDEBAR
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(245)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 25, 15, 20)
        sidebar_layout.setSpacing(8)

        brand = QLabel("THE Eminence")
        brand.setObjectName("Brand")

        subtitle = QLabel("PREMIUM ELECTRICAL MANAGEMENT")
        subtitle.setObjectName("Subtitle")

        sidebar_layout.addWidget(brand)
        sidebar_layout.addWidget(subtitle)
        sidebar_layout.addSpacing(25)

        menu_items = [
            ("âŒ‚", "Ø¯Ø§Ø´Ø¨ÙˆØ±Ø¯"),
            ("âš¡", "Ù…Ø­Ø§Ø³Ø¨Ø§Øª Ø¨Ø±Ù‚"),
            ("â–£", "Ù¾Ø±ÙˆÚ˜Ù‡â€ŒÙ‡Ø§"),
            ("â—‰", "Ù…Ø´ØªØ±ÛŒØ§Ù†"),
            ("â–¤", "Ú¯Ø²Ø§Ø±Ø´â€ŒÙ‡Ø§"),
            ("â—·", "Ø²Ù…Ø§Ù†â€ŒÚ©Ø§Ø±ÛŒ"),
            ("âš™", "ØªÙ†Ø¸ÛŒÙ…Ø§Øª"),
        ]

        for index, (icon, title) in enumerate(menu_items):

            button = QPushButton(f"{icon}    {title}")
            button.setObjectName("Nav")
            button.setCheckable(True)

            button.clicked.connect(
                lambda checked=False, i=index: self.change_page(i)
            )

            sidebar_layout.addWidget(button)
            self.nav_buttons.append(button)

        sidebar_layout.addStretch()

        version = QLabel("PREMIUM EDITION\nVERSION 2.0")
        version.setObjectName("Muted")
        version.setAlignment(Qt.AlignCenter)

        sidebar_layout.addWidget(version)

        # MAIN CONTENT
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(15)

        # HEADER
        header = QFrame()
        header.setObjectName("Header")

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(22, 16, 22, 16)

        header_title = QLabel("Ù¾Ù†Ù„ Ù…Ø¯ÛŒØ±ÛŒØª")
        header_title.setObjectName("Title")

        status = QLabel("â— Ø³ÛŒØ³ØªÙ… Ø¢Ù…Ø§Ø¯Ù‡ Ø§Ø³Øª")
        status.setStyleSheet("color: #D4AF37; font-weight: bold;")

        header_layout.addWidget(header_title)
        header_layout.addStretch()
        header_layout.addWidget(status)

        content_layout.addWidget(header)

        # PAGES
        self.pages.addWidget(self.create_dashboard())

        page_names = [
            "Ø¯Ø§Ø´Ø¨ÙˆØ±Ø¯",
            "Ù…Ø­Ø§Ø³Ø¨Ø§Øª Ø¨Ø±Ù‚",
            "Ù¾Ø±ÙˆÚ˜Ù‡â€ŒÙ‡Ø§",
            "Ù…Ø´ØªØ±ÛŒØ§Ù†",
            "Ú¯Ø²Ø§Ø±Ø´â€ŒÙ‡Ø§",
            "Ø²Ù…Ø§Ù†â€ŒÚ©Ø§Ø±ÛŒ",
            "ØªÙ†Ø¸ÛŒÙ…Ø§Øª",
        ]

        for name in page_names[1:]:
            self.pages.addWidget(self.create_placeholder(name))

        content_layout.addWidget(self.pages, 1)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content, 1)

        self.change_page(0)

    def create_dashboard(self):

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        heading = QLabel("Ø¯Ø§Ø´Ø¨ÙˆØ±Ø¯ Ù…Ø¯ÛŒØ±ÛŒØªÛŒ")
        heading.setObjectName("Title")

        description = QLabel(
            "Ù†Ù…Ø§ÛŒ Ú©Ù„ÛŒ Ø¹Ù…Ù„Ú©Ø±Ø¯ Ùˆ ÙˆØ¶Ø¹ÛŒØª Ø³ÛŒØ³ØªÙ… Ù…Ø¯ÛŒØ±ÛŒØª Ø¨Ø±Ù‚"
        )
        description.setObjectName("Muted")

        layout.addWidget(heading)
        layout.addWidget(description)

        # STATISTICS
        grid = QGridLayout()
        grid.setSpacing(15)

        cards = [
            ("Ù¾Ø±ÙˆÚ˜Ù‡â€ŒÙ‡Ø§ÛŒ ÙØ¹Ø§Ù„", "12", "Active Projects"),
            ("Ù…Ø´ØªØ±ÛŒØ§Ù†", "48", "Registered Customers"),
            ("Ú¯Ø²Ø§Ø±Ø´â€ŒÙ‡Ø§ÛŒ Ø«Ø¨Øªâ€ŒØ´Ø¯Ù‡", "156", "Saved Reports"),
            ("Ù…Ø­Ø§Ø³Ø¨Ø§Øª Ø§Ù†Ø¬Ø§Ù…â€ŒØ´Ø¯Ù‡", "320", "Electrical Calculations"),
        ]

        for index, (name, number, caption) in enumerate(cards):

            card = QFrame()
            card.setObjectName("Card")
            card.setMinimumHeight(145)

            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(22, 18, 22, 18)

            label = QLabel(name)
            label.setObjectName("Muted")

            value = QLabel(number)
            value.setObjectName("Number")

            footer = QLabel(caption)
            footer.setObjectName("CardCaption")

            card_layout.addWidget(label)
            card_layout.addWidget(value)
            card_layout.addWidget(footer)

            grid.addWidget(card, index // 2, index % 2)

        layout.addLayout(grid)

        # WELCOME CARD
        welcome = QFrame()
        welcome.setObjectName("WelcomeCard")

        welcome_layout = QVBoxLayout(welcome)
        welcome_layout.setContentsMargins(25, 22, 25, 22)

        welcome_title = QLabel("THE Eminence")
        welcome_title.setObjectName("WelcomeTitle")

        welcome_text = QLabel(
            "Ø¨Ù‡ Ù…Ø±Ú©Ø² Ù…Ø¯ÛŒØ±ÛŒØª Ø­Ø±ÙÙ‡â€ŒØ§ÛŒ Ø¨Ø±Ù‚ Ø®ÙˆØ´ Ø¢Ù…Ø¯ÛŒØ¯.\n"
            "ØªÙ…Ø§Ù… Ø§Ø¨Ø²Ø§Ø±Ù‡Ø§ÛŒ Ù…Ø¯ÛŒØ±ÛŒØªÛŒ Ùˆ Ù…Ø­Ø§Ø³Ø¨Ø§ØªÛŒ Ø´Ù…Ø§ Ø¯Ø± ÛŒÚ© Ù…Ø­ÛŒØ· ÛŒÚ©Ù¾Ø§Ø±Ú†Ù‡."
        )
        welcome_text.setObjectName("WelcomeText")
        welcome_text.setWordWrap(True)

        welcome_layout.addWidget(welcome_title)
        welcome_layout.addSpacing(8)
        welcome_layout.addWidget(welcome_text)

        layout.addWidget(welcome)

        # QUICK ACTIONS
        actions_title = QLabel("Ø¯Ø³ØªØ±Ø³ÛŒ Ø³Ø±ÛŒØ¹")
        actions_title.setObjectName("Title")

        layout.addWidget(actions_title)

        actions_layout = QHBoxLayout()

        action_names = [
            "Ù…Ø­Ø§Ø³Ø¨Ù‡ Ø¬Ø¯ÛŒØ¯",
            "Ø§ÛŒØ¬Ø§Ø¯ Ù¾Ø±ÙˆÚ˜Ù‡",
            "Ø«Ø¨Øª Ú¯Ø²Ø§Ø±Ø´",
        ]

        for name in action_names:
            button = QPushButton(name)
            button.setObjectName("Action")
            actions_layout.addWidget(button)

        layout.addLayout(actions_layout)
        layout.addStretch()

        return page

    def create_placeholder(self, name):

        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel(name)
        title.setObjectName("Title")

        message = QLabel(
            "Ø§ÛŒÙ† Ø¨Ø®Ø´ Ø¯Ø± Ù…Ø±Ø§Ø­Ù„ Ø¨Ø¹Ø¯ Ø¨Ù‡ Ø§Ù…Ú©Ø§Ù†Ø§Øª ÙˆØ§Ù‚Ø¹ÛŒ Ø¨Ø±Ù†Ø§Ù…Ù‡ Ù…ØªØµÙ„ Ø®ÙˆØ§Ù‡Ø¯ Ø´Ø¯."
        )
        message.setObjectName("Muted")
        message.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(message)
        layout.addStretch()

        return page

    def change_page(self, index):

        self.pages.setCurrentIndex(index)

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
