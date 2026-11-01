from __future__ import annotations

import sys
from pathlib import Path

# Ensure package root is in sys.path if executed directly as a script
if __package__ is None or not __package__:
    src_dir = str(Path(__file__).resolve().parent.parent)
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)

    from val_overlay.win32_bridge import (
        apply_efficiency_scheduler_profile,
        enable_per_monitor_dpi_v2,
    )
    from val_overlay.config_manager import ConfigManager
    from val_overlay.hotkey_filter import Win32HotkeyFilter
    from val_overlay.overlay_window import TacticalOverlayWindow
else:
    from .win32_bridge import (
        apply_efficiency_scheduler_profile,
        enable_per_monitor_dpi_v2,
    )
    from .config_manager import ConfigManager
    from .hotkey_filter import Win32HotkeyFilter
    from .overlay_window import TacticalOverlayWindow

# Must run before QApplication is constructed
enable_per_monitor_dpi_v2()

from PySide6.QtWidgets import QApplication


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
