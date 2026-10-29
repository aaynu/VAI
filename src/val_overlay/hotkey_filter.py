from __future__ import annotations

from ctypes import wintypes
from typing import TYPE_CHECKING, Tuple

from PySide6.QtCore import QAbstractNativeEventFilter

from .win32_bridge import WM_HOTKEY

if TYPE_CHECKING:
    from .overlay_window import TacticalOverlayWindow


class Win32HotkeyFilter(QAbstractNativeEventFilter):
    """Intercepts kernel-registered WM_HOTKEY events at 0% idle CPU cost."""

    def __init__(self, overlay: "TacticalOverlayWindow") -> None:
        super().__init__()
        self.overlay = overlay

    def nativeEventFilter(self, event_type, message) -> Tuple[bool, int]:
        if event_type == b"windows_generic_MSG":
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY:
                self.overlay.handle_hotkey(int(msg.wParam))
                return True, 0
        return False, 0
