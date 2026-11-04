"""کلاس اپلیکیشن ElectroCalc."""

from electrocalc.config import constants as C
from electrocalc.ui.main_window import MainWindow
from electrocalc.utils.logger import log


class ElectroCalcApp:
    def __init__(self, current_user=None):
        self.current_user = current_user
        log.info(f"راه‌اندازی {C.APP_NAME} v{C.APP_VERSION}")
        self.window = MainWindow(current_user=current_user)

    def run(self) -> None:
        self.window.run()