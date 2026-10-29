from __future__ import annotations

import sys

from .win32_bridge import (
    apply_efficiency_scheduler_profile,
    enable_per_monitor_dpi_v2,
)

# Must run before QApplication is constructed
enable_per_monitor_dpi_v2()

from PySide6.QtWidgets import QApplication

from .config_manager import ConfigManager
from .hotkey_filter import Win32HotkeyFilter
from .overlay_window import TacticalOverlayWindow


def main() -> int:
    apply_efficiency_scheduler_profile(prefer_last_n_cores=4)

    app = QApplication(sys.argv)
    config = ConfigManager()
    overlay = TacticalOverlayWindow(config)

    hotkey_filter = Win32HotkeyFilter(overlay)
    app.installNativeEventFilter(hotkey_filter)

    overlay.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
