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
