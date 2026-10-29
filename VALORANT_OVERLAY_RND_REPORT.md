# R&D Technical Specification: Passive DWM Alignment Overlay for Valorant (`val-reticle-overlay`)

## 1. Executive Summary & Strict Compliance Mandate
This project implements a lightweight, zero-overhead Windows 11 desktop overlay utility in Python 3.11+ (`PySide6` + `ctypes` Win32 API). It renders static, click-through visual alignment markers for *Valorant*'s Agent Select interface (Role Filter Tab, Agent Grid Slot, and Lock-In Button) so the user can manually pre-position their physical mouse cursor prior to UI rendering.

### Non-Negotiable Anti-Cheat (Riot Vanguard) Constraints
1. **Zero Process Interaction:** Never enumerate processes, open handles (`OpenProcess`), read/write process memory (`ReadProcessMemory`), or inspect `VALORANT-Win64-Shipping.exe`.
2. **Zero Input Automation:** Never import or invoke `SendInput`, `mouse_event`, `keybd_event`, `SetCursorPos`, `PyAutoGUI`, or virtual HID drivers. All cursor movement and clicking are 100% manual human input.
3. **Zero Global Input Hooks:** Never call `SetWindowsHookEx` (`WH_KEYBOARD_LL` or `WH_MOUSE_LL`). All hotkeys must use kernel-registered `RegisterHotKey` messages (`WM_HOTKEY`).
4. **True DWM Detachment During Gameplay:** When hidden via hotkey (`Ctrl+Shift+F8`), the window must call `ShowWindow(hwnd, SW_HIDE)` so Windows 11 DWM removes the layered surface from composition and promotes *Valorant* into hardware Independent Flip (iFlip).

---

## 2. Target Project Structure
The AI coding agent must scaffold the project inside PyCharm using the following modular layout:

```text
val-reticle-overlay/
├── pyproject.toml
├── requirements.txt
├── README.md
├── overlay_config.json          # Auto-generated on first run if absent
└── src/
    └── val_overlay/
        ├── __init__.py
        ├── main.py              # Entry point, DPI V2 init, QApplication lifecycle
        ├── win32_bridge.py      # ctypes definitions, EcoQoS, E-Core affinity, Window styles
        ├── config_manager.py    # Atomic JSON persistence & default Valorant presets
        ├── coordinate_engine.py # Normalized [0.0, 1.0] UV <-> Physical pixel math
        ├── hotkey_filter.py     # QAbstractNativeEventFilter for WM_HOTKEY
        └── overlay_window.py    # Static QPainter renderer & interactive calibration mode
```

---

## 3. Dependencies (`requirements.txt`)
```text
PySide6>=6.7.0
```

---

## 4. Module Specifications & Reference Implementation

### 4.1 `src/val_overlay/win32_bridge.py`
Encapsulates all `ctypes` Win32 API calls (`user32.dll`, `kernel32.dll`), Per-Monitor DPI Awareness V2 initialization, Windows 11 EcoQoS power throttling, CPU Efficiency-Core (E-Core) affinity pinning, extended window style mutation, and non-activating visibility toggles.

```python
from __future__ import annotations

import ctypes
from ctypes import wintypes

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# --- DPI Constants ---
DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = ctypes.c_void_p(-4)

# --- Window Extended Styles ---
GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000

# --- SetWindowPos & ShowWindow Flags ---
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
HWND_TOPMOST = ctypes.c_void_p(-1)

SW_HIDE = 0
SW_SHOWNOACTIVATE = 4

# --- Hotkey Constants ---
WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_NOREPEAT = 0x4000

VK_F7 = 0x76   # Ctrl+Shift+F7  -> Cycle Target Monitor
VK_F8 = 0x77   # Ctrl+Shift+F8  -> Toggle Show/Hide (True SW_HIDE for DWM DirectFlip)
VK_F9 = 0x78   # Ctrl+Shift+F9  -> Toggle Calibration Mode (Lock/Unlock)
VK_F10 = 0x79  # Ctrl+Shift+F10 -> Cycle Agent Preset
VK_R = 0x52    # Ctrl+Shift+R   -> Toggle 3-Point Role Filter Waypoint
VK_Q = 0x51    # Ctrl+Shift+Q   -> Clean Exit

HOTKEY_CYCLE_MONITOR = 1
HOTKEY_TOGGLE_VISIBILITY = 2
HOTKEY_TOGGLE_CALIBRATION = 3
HOTKEY_CYCLE_AGENT = 4
HOTKEY_TOGGLE_ROLE_POINT = 5
HOTKEY_EXIT = 6

# --- Process Priority & EcoQoS Constants ---
IDLE_PRIORITY_CLASS = 0x00000040
ProcessPowerThrottling = 4
PROCESS_POWER_THROTTLING_CURRENT_VERSION = 1
PROCESS_POWER_THROTTLING_EXECUTION_SPEED = 0x1


class PROCESS_POWER_THROTTLING_STATE(ctypes.Structure):
    _fields_ = [
        ("Version", wintypes.ULONG),
        ("ControlMask", wintypes.ULONG),
        ("StateMask", wintypes.ULONG),
    ]


class SYSTEM_INFO(ctypes.Structure):
    _fields_ = [
        ("wProcessorArchitecture", wintypes.WORD),
        ("wReserved", wintypes.WORD),
        ("dwPageSize", wintypes.DWORD),
        ("lpMinimumApplicationAddress", ctypes.c_void_p),
        ("lpMaximumApplicationAddress", ctypes.c_void_p),
        ("dwActiveProcessorMask", ctypes.c_size_t),
        ("dwNumberOfProcessors", wintypes.DWORD),
        ("dwProcessorType", wintypes.DWORD),
        ("dwAllocationGranularity", wintypes.DWORD),
        ("wProcessorLevel", wintypes.WORD),
        ("wProcessorRevision", wintypes.WORD),
    ]


LONG_PTR = ctypes.c_longlong if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_long

user32.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
user32.SetProcessDpiAwarenessContext.restype = wintypes.BOOL

user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongPtrW.restype = LONG_PTR

user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, LONG_PTR]
user32.SetWindowLongPtrW.restype = LONG_PTR

user32.SetWindowPos.argtypes = [
    wintypes.HWND,
    wintypes.HWND,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.UINT,
]
user32.SetWindowPos.restype = wintypes.BOOL

user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL

user32.RegisterHotKey.argtypes = [
    wintypes.HWND,
    ctypes.c_int,
    wintypes.UINT,
    wintypes.UINT,
]
user32.RegisterHotKey.restype = wintypes.BOOL

user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UnregisterHotKey.restype = wintypes.BOOL

kernel32.GetCurrentProcess.argtypes = []
kernel32.GetCurrentProcess.restype = wintypes.HANDLE

kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
kernel32.SetPriorityClass.restype = wintypes.BOOL

kernel32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
kernel32.SetProcessAffinityMask.restype = wintypes.BOOL

kernel32.SetProcessInformation.argtypes = [
    wintypes.HANDLE,
    ctypes.c_int,
    ctypes.c_void_p,
    wintypes.DWORD,
]
kernel32.SetProcessInformation.restype = wintypes.BOOL

kernel32.GetSystemInfo.argtypes = [ctypes.POINTER(SYSTEM_INFO)]
kernel32.GetSystemInfo.restype = None


def enable_per_monitor_dpi_v2() -> None:
    """Must be called before QApplication is instantiated."""
    if not user32.SetProcessDpiAwarenessContext(
        DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2
    ):
        user32.SetProcessDPIAware()


def apply_efficiency_scheduler_profile(prefer_last_n_cores: int = 4) -> None:
    """Pins process to Efficiency Cores (E-Cores) and enables Windows 11 EcoQoS."""
    h_proc = kernel32.GetCurrentProcess()
    kernel32.SetPriorityClass(h_proc, IDLE_PRIORITY_CLASS)

    throttling = PROCESS_POWER_THROTTLING_STATE(
        Version=PROCESS_POWER_THROTTLING_CURRENT_VERSION,
        ControlMask=PROCESS_POWER_THROTTLING_EXECUTION_SPEED,
        StateMask=PROCESS_POWER_THROTTLING_EXECUTION_SPEED,
    )
    kernel32.SetProcessInformation(
        h_proc,
        ProcessPowerThrottling,
        ctypes.byref(throttling),
        ctypes.sizeof(throttling),
    )

    sys_info = SYSTEM_INFO()
    kernel32.GetSystemInfo(ctypes.byref(sys_info))
    total_cores = sys_info.dwNumberOfProcessors

    if total_cores > prefer_last_n_cores:
        mask = 0
        for idx in range(total_cores - prefer_last_n_cores, total_cores):
            mask |= 1 << idx
        mask &= sys_info.dwActiveProcessorMask
        if mask != 0:
            kernel32.SetProcessAffinityMask(h_proc, mask)


def set_overlay_window_styles(hwnd: int, click_through: bool = True) -> None:
    """Applies or removes WS_EX_TRANSPARENT and WS_EX_NOACTIVATE on the target HWND."""
    ex_style = user32.GetWindowLongPtrW(hwnd, GWL_EXSTYLE)
    base_flags = WS_EX_TOPMOST | WS_EX_LAYERED | WS_EX_TOOLWINDOW

    if click_through:
        new_style = ex_style | base_flags | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE
    else:
        new_style = (ex_style | base_flags) & ~WS_EX_TRANSPARENT & ~WS_EX_NOACTIVATE

    ctypes.set_last_error(0)
    user32.SetWindowLongPtrW(hwnd, GWL_EXSTYLE, new_style)

    swp_flags = SWP_NOMOVE | SWP_NOSIZE | SWP_FRAMECHANGED
    if click_through:
        swp_flags |= SWP_NOACTIVATE
    user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, swp_flags)


def show_overlay_no_activate(hwnd: int) -> None:
    """Shows the HWND without stealing focus from Valorant."""
    user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)


def hide_overlay_from_dwm(hwnd: int) -> None:
    """Completely hides the HWND so DWM restores hardware Independent Flip (iFlip)."""
    user32.ShowWindow(hwnd, SW_HIDE)
```

---

### 4.2 `src/val_overlay/coordinate_engine.py`
Handles aspect-ratio classification (`16:9`, `16:10`, `other`) and converts normalized $[0.0, 1.0]$ coordinates to physical screen pixels.

```python
from __future__ import annotations

import math
from typing import Tuple


class CoordinateEngine:
    """Bi-directional conversion between normalized [0.0, 1.0] UV coordinates and physical pixels."""

    @staticmethod
    def detect_aspect_key(width: int, height: int) -> str:
        if height <= 0:
            return "16:9"
        ratio = width / height
        if math.isclose(ratio, 16 / 9, rel_tol=0.02):
            return "16:9"
        if math.isclose(ratio, 16 / 10, rel_tol=0.02):
            return "16:10"
        return "other"

    @staticmethod
    def uv_to_physical(u: float, v: float, width: int, height: int) -> Tuple[int, int]:
        cu = max(0.0, min(1.0, u))
        cv = max(0.0, min(1.0, v))
        return round(cu * width), round(cv * height)

    @staticmethod
    def physical_to_uv(x: int, y: int, width: int, height: int) -> Tuple[float, float]:
        if width <= 0 or height <= 0:
            return 0.5, 0.5
        return (
            round(max(0.0, min(1.0, x / width)), 5),
            round(max(0.0, min(1.0, y / height)), 5),
        )
```

---

### 4.3 `src/val_overlay/config_manager.py`
Stores normalized presets adapted for *Valorant*'s modern left-hand 2D Agent Grid, optional Role Filter Tab waypoint, and bottom-center Lock-In button.

```python
from __future__ import annotations

import copy
import json
import os
from typing import Optional


class ConfigManager:
    """Atomic JSON configuration loader and saver."""

    DEFAULT_CONFIG = {
        "active_preset_index": 0,
        "monitor_index": 0,
        "reticle_opacity": 0.88,
        "agent_box_size_px": 54,
        "role_box_size_px": 36,
        "lock_in_radius_px": 24,
        "presets": [
            {
                "name": "Jett (Duelist)",
                "use_role_filter": True,
                "aspect_profiles": {
                    "16:9": {
                        "role_uv": [0.0885, 0.1950],
                        "agent_uv": [0.1180, 0.3050],
                        "lock_uv": [0.5000, 0.8150],
                    },
                    "16:10": {
                        "role_uv": [0.0885, 0.1950],
                        "agent_uv": [0.1180, 0.3050],
                        "lock_uv": [0.5000, 0.8150],
                    },
                    "other": {
                        "role_uv": [0.0885, 0.1950],
                        "agent_uv": [0.1180, 0.3050],
                        "lock_uv": [0.5000, 0.8150],
                    },
                },
            },
            {
                "name": "Clove (Controller)",
                "use_role_filter": True,
                "aspect_profiles": {
                    "16:9": {
                        "role_uv": [0.1450, 0.1950],
                        "agent_uv": [0.1720, 0.3050],
                        "lock_uv": [0.5000, 0.8150],
                    },
                    "16:10": {
                        "role_uv": [0.1450, 0.1950],
                        "agent_uv": [0.1720, 0.3050],
                        "lock_uv": [0.5000, 0.8150],
                    },
                    "other": {
                        "role_uv": [0.1450, 0.1950],
                        "agent_uv": [0.1720, 0.3050],
                        "lock_uv": [0.5000, 0.8150],
                    },
                },
            },
            {
                "name": "Reyna (Duelist)",
                "use_role_filter": True,
                "aspect_profiles": {
                    "16:9": {
                        "role_uv": [0.0885, 0.1950],
                        "agent_uv": [0.1720, 0.3950],
                        "lock_uv": [0.5000, 0.8150],
                    },
                    "16:10": {
                        "role_uv": [0.0885, 0.1950],
                        "agent_uv": [0.1720, 0.3950],
                        "lock_uv": [0.5000, 0.8150],
                    },
                    "other": {
                        "role_uv": [0.0885, 0.1950],
                        "agent_uv": [0.1720, 0.3950],
                        "lock_uv": [0.5000, 0.8150],
                    },
                },
            },
        ],
    }

    def __init__(self, filepath: str = "overlay_config.json") -> None:
        self.filepath = filepath
        self.data = self._load()

    def _load(self) -> dict:
        if not os.path.exists(self.filepath):
            default_copy = copy.deepcopy(self.DEFAULT_CONFIG)
            self.save(default_copy)
            return default_copy
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError):
            return copy.deepcopy(self.DEFAULT_CONFIG)

    def save(self, data: Optional[dict] = None) -> None:
        if data is not None:
            self.data = data
        tmp_path = f"{self.filepath}.tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
        os.replace(tmp_path, self.filepath)
```

---

### 4.4 `src/val_overlay/hotkey_filter.py`
Captures `WM_HOTKEY` directly from the Win32 thread queue without hooks.

```python
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
```

---

### 4.5 `src/val_overlay/overlay_window.py`
Implements the static event-driven `QPainter` renderer, 3-point trajectory guide vectors, multi-monitor switching, drag-and-drop calibration, and 1px arrow-key micro-nudging.

```python
from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QKeyEvent, QMouseEvent, QPainter, QPen
from PySide6.QtWidgets import QApplication, QWidget

from .config_manager import ConfigManager
from .coordinate_engine import CoordinateEngine
from .win32_bridge import (
    HOTKEY_CYCLE_AGENT,
    HOTKEY_CYCLE_MONITOR,
    HOTKEY_EXIT,
    HOTKEY_TOGGLE_CALIBRATION,
    HOTKEY_TOGGLE_ROLE_POINT,
    HOTKEY_TOGGLE_VISIBILITY,
    MOD_CONTROL,
    MOD_NOREPEAT,
    MOD_SHIFT,
    VK_F7,
    VK_F8,
    VK_F9,
    VK_F10,
    VK_Q,
    VK_R,
    hide_overlay_from_dwm,
     set_overlay_window_styles,
    show_overlay_no_activate,
    user32,
)


class TacticalOverlayWindow(QWidget):
    """
    Static DWM-composited overlay window for Valorant Agent Select alignment.
    Executes zero continuous loops; detaches from DWM via SW_HIDE when toggled off.
    """

    def __init__(self, config: ConfigManager) -> None:
        super().__init__()
        self.config = config
        self.calibration_mode = False
        self.overlay_visible = True
        self.selected_target: Optional[str] = "agent"  # "role", "agent", or "lock"
        self.dragging_target: Optional[str] = None

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.screen_w = 1920
        self.screen_h = 1080
        self._apply_monitor_geometry()

        self.hwnd = int(self.winId())
        set_overlay_window_styles(self.hwnd, click_through=True)
        self._register_hotkeys()

    def _apply_monitor_geometry(self) -> None:
        screens = QApplication.screens()
        if not screens:
            return
        idx = int(self.config.data.get("monitor_index", 0)) % len(screens)
        self.config.data["monitor_index"] = idx
        target_screen = screens[idx]
        geom = target_screen.geometry()
        self.screen_w = geom.width()
        self.screen_h = geom.height()
        self.setGeometry(geom)

    def _register_hotkeys(self) -> None:
        mods = MOD_CONTROL | MOD_SHIFT | MOD_NOREPEAT
        bindings = [
            (HOTKEY_CYCLE_MONITOR, mods, VK_F7),
            (HOTKEY_TOGGLE_VISIBILITY, mods, VK_F8),
            (HOTKEY_TOGGLE_CALIBRATION, mods, VK_F9),
            (HOTKEY_CYCLE_AGENT, mods, VK_F10),
            (HOTKEY_TOGGLE_ROLE_POINT, mods, VK_R),
            (HOTKEY_EXIT, mods, VK_Q),
        ]
        for hk_id, mod, vk in bindings:
            user32.RegisterHotKey(None, hk_id, mod, vk)

    def unregister_hotkeys(self) -> None:
        for hk_id in (
            HOTKEY_CYCLE_MONITOR,
            HOTKEY_TOGGLE_VISIBILITY,
            HOTKEY_TOGGLE_CALIBRATION,
            HOTKEY_CYCLE_AGENT,
            HOTKEY_TOGGLE_ROLE_POINT,
            HOTKEY_EXIT,
        ):
            user32.UnregisterHotKey(None, hk_id)

    def _active_preset_and_profile(self) -> Tuple[dict, dict]:
        presets = self.config.data["presets"]
        idx = int(self.config.data.get("active_preset_index", 0)) % len(presets)
        preset = presets[idx]
        aspect_key = CoordinateEngine.detect_aspect_key(self.screen_w, self.screen_h)
        profile = preset["aspect_profiles"].get(
            aspect_key, preset["aspect_profiles"]["16:9"]
        )
        return preset, profile

    def handle_hotkey(self, hotkey_id: int) -> None:
        if hotkey_id == HOTKEY_TOGGLE_VISIBILITY:
            self.overlay_visible = not self.overlay_visible
            if self.overlay_visible:
                show_overlay_no_activate(self.hwnd)
                set_overlay_window_styles(
                    self.hwnd, click_through=not self.calibration_mode
                )
                self.update()
            else:
                # Detach HWND from DWM composition so Valorant enters Independent Flip
                hide_overlay_from_dwm(self.hwnd)

        elif hotkey_id == HOTKEY_TOGGLE_CALIBRATION:
            self.calibration_mode = not self.calibration_mode
            if self.calibration_mode:
                self.overlay_visible = True
                self.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus, False)
                self.show()
                set_overlay_window_styles(self.hwnd, click_through=False)
                self.activateWindow()
                self.setFocus()
            else:
                self.config.save()
                set_overlay_window_styles(self.hwnd, click_through=True)
            self.update()

        elif hotkey_id == HOTKEY_CYCLE_AGENT:
            presets = self.config.data["presets"]
            self.config.data["active_preset_index"] = (
                int(self.config.data.get("active_preset_index", 0)) + 1
            ) % len(presets)
            self.config.save()
            self.update()

        elif hotkey_id == HOTKEY_TOGGLE_ROLE_POINT:
            preset, _ = self._active_preset_and_profile()
            preset["use_role_filter"] = not bool(preset.get("use_role_filter", True))
            self.config.save()
            self.update()

        elif hotkey_id == HOTKEY_CYCLE_MONITOR:
            screens = QApplication.screens()
            if len(screens) > 1:
                self.config.data["monitor_index"] = (
                    int(self.config.data.get("monitor_index", 0)) + 1
                ) % len(screens)
                self._apply_monitor_geometry()
                self.config.save()
                self.update()

        elif hotkey_id == HOTKEY_EXIT:
            self.unregister_hotkeys()
            QApplication.quit()

    def paintEvent(self, event) -> None:
        if not self.overlay_visible:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setOpacity(float(self.config.data.get("reticle_opacity", 0.88)))

        preset, profile = self._active_preset_and_profile()
        use_role = bool(preset.get("use_role_filter", True))

        rx, ry = CoordinateEngine.uv_to_physical(
            profile["role_uv"][0], profile["role_uv"][1], self.screen_w, self.screen_h
        )
        ax, ay = CoordinateEngine.uv_to_physical(
            profile["agent_uv"][0], profile["agent_uv"][1], self.screen_w, self.screen_h
        )
        lx, ly = CoordinateEngine.uv_to_physical(
            profile["lock_uv"][0], profile["lock_uv"][1], self.screen_w, self.screen_h
        )

        # Draw faint dashed vector path connecting waypoints
        guide_pen = QPen(QColor(255, 255, 255, 95), 1.2, Qt.PenStyle.DashLine)
        painter.setPen(guide_pen)
        if use_role:
            painter.drawLine(rx, ry, ax, ay)
        painter.drawLine(ax, ay, lx, ly)

        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))

        # 1. Optional Role Filter Tab Reticle (Magenta Diamond/Square)
        if use_role:
            role_size = int(self.config.data.get("role_box_size_px", 36))
            half_r = role_size / 2.0
            role_color = (
                QColor(255, 255, 100, 245)
                if (self.calibration_mode and self.selected_target == "role")
                else QColor(235, 80, 255, 230)
            )
            painter.setPen(QPen(role_color, 2.0))
            painter.drawRect(QRectF(rx - half_r, ry - half_r, role_size, role_size))
            painter.drawEllipse(QPointF(rx, ry), 2.0, 2.0)
            painter.drawText(QPointF(rx - half_r, ry - half_r - 6), "[1] ROLE TAB")

        # 2. Agent Grid Slot Reticle (Cyan Square + Center Dot)
        box_size = int(self.config.data.get("agent_box_size_px", 54))
        half_b = box_size / 2.0
        agent_color = (
            QColor(255, 255, 100, 245)
            if (self.calibration_mode and self.selected_target == "agent")
            else QColor(0, 240, 255, 230)
        )
        painter.setPen(QPen(agent_color, 2.0))
        painter.drawRect(QRectF(ax - half_b, ay - half_b, box_size, box_size))
        painter.drawEllipse(QPointF(ax, ay), 2.5, 2.5)
        step_num = "2" if use_role else "1"
        painter.drawText(
            QPointF(ax - half_b, ay - half_b - 6), f"[{step_num}] {preset['name']}"
        )

        # 3. Lock-In Target Ring (Amber Ring + Crosshair)
        lock_rad = int(self.config.data.get("lock_in_radius_px", 24))
        lock_color = (
            QColor(255, 255, 100, 245)
            if (self.calibration_mode and self.selected_target == "lock")
            else QColor(255, 170, 0, 230)
        )
        painter.setPen(QPen(lock_color, 2.0))
        painter.drawEllipse(QPointF(lx, ly), lock_rad, lock_rad)
        painter.drawLine(lx - 6, ly, lx + 6, ly)
        painter.drawLine(lx, ly - 6, lx, ly + 6)
        lock_step = "3" if use_role else "2"
        painter.drawText(
            QPointF(lx - lock_rad, ly - lock_rad - 6), f"[{lock_step}] LOCK IN"
        )

        # 4. Calibration HUD Banner
        if self.calibration_mode:
            painter.setOpacity(0.95)
            banner = QRectF(self.screen_w / 2 - 310, 24, 620, 72)
            painter.fillRect(banner, QColor(15, 16, 22, 235))
            painter.setPen(QPen(QColor(0, 240, 255), 1.5))
            painter.drawRect(banner)
            aspect_key = CoordinateEngine.detect_aspect_key(self.screen_w, self.screen_h)
            painter.drawText(
                banner,
                Qt.AlignmentFlag.AlignCenter,
                f"CALIBRATION UNLOCKED | Preset: {preset['name']} | Display: {self.screen_w}x{self.screen_h} ({aspect_key})\n"
                f"Drag Reticles or Click + Use Arrow Keys (1px) / Shift+Arrows (5px) [Selected: {str(self.selected_target).upper()}]\n"
                "Ctrl+Shift+F9: Lock & Save | Ctrl+Shift+F10: Cycle Agent | Ctrl+Shift+R: Toggle Role Waypoint",
            )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if not self.calibration_mode or event.button() != Qt.MouseButton.LeftButton:
            return

        pos = event.position()
        preset, profile = self._active_preset_and_profile()
        targets: Dict[str, Tuple[int, int]] = {
            "agent": CoordinateEngine.uv_to_physical(
                profile["agent_uv"][0], profile["agent_uv"][1], self.screen_w, self.screen_h
            ),
            "lock": CoordinateEngine.uv_to_physical(
                profile["lock_uv"][0], profile["lock_uv"][1], self.screen_w, self.screen_h
            ),
        }
        if preset.get("use_role_filter", True):
            targets["role"] = CoordinateEngine.uv_to_physical(
                profile["role_uv"][0], profile["role_uv"][1], self.screen_w, self.screen_h
            )

        for name, (tx, ty) in targets.items():
            if math.hypot(pos.x() - tx, pos.y() - ty) <= 42:
                self.selected_target = name
                self.dragging_target = name
                self.update()
                break

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if not self.calibration_mode or not self.dragging_target:
            return

        pos = event.position()
        u, v = CoordinateEngine.physical_to_uv(
            int(pos.x()), int(pos.y()), self.screen_w, self.screen_h
        )
        _, profile = self._active_preset_and_profile()
        profile[f"{self.dragging_target}_uv"] = [u, v]
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging_target = None

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """1-pixel (or 5-pixel with Shift) arrow-key micro-nudging during Calibration Mode."""
        if not self.calibration_mode or not self.selected_target:
            return

        step = 5 if (event.modifiers() & Qt.KeyboardModifier.ShiftModifier) else 1
        dx, dy = 0, 0
        if event.key() == Qt.Key.Key_Left:
            dx = -step
        elif event.key() == Qt.Key.Key_Right:
            dx = step
        elif event.key() == Qt.Key.Key_Up:
            dy = -step
        elif event.key() == Qt.Key.Key_Down:
            dy = step
        else:
            return

        _, profile = self._active_preset_and_profile()
        key_name = f"{self.selected_target}_uv"
        px, py = CoordinateEngine.uv_to_physical(
            profile[key_name][0], profile[key_name][1], self.screen_w, self.screen_h
        )
        nu, nv = CoordinateEngine.physical_to_uv(
            px + dx, py + dy, self.screen_w, self.screen_h
        )
        profile[key_name] = [nu, nv]
        self.update()
```

---

### 4.6 `src/val_overlay/main.py`
Entry point that initializes Per-Monitor V2 DPI awareness prior to `QApplication`, applies Windows 11 EcoQoS and E-Core affinity, and starts the native event filter.

```python
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
    config = ConfigManager("overlay_config.json")
    overlay = TacticalOverlayWindow(config)

    hotkey_filter = Win32HotkeyFilter(overlay)
    app.installNativeEventFilter(hotkey_filter)

    overlay.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
```