from __future__ import annotations

import json
import os
import sys
from pathlib import Path
import pytest

from val_overlay.config_manager import ConfigManager
from val_overlay.coordinate_engine import CoordinateEngine
from val_overlay.win32_bridge import (
    apply_efficiency_scheduler_profile,
    enable_per_monitor_dpi_v2,
)


class TestCoordinateEngine:
    """Verifies CoordinateEngine aspect ratio classification and bi-directional UV mapping."""

    @pytest.mark.parametrize(
        "width,height,expected_key",
        [
            (1920, 1080, "16:9"),
            (2560, 1440, "16:9"),
            (3840, 2160, "16:9"),
            (2560, 1600, "16:10"),
            (1920, 1200, "16:10"),
            (1280, 1024, "other"),  # 5:4
            (1024, 768, "other"),   # 4:3
            (0, 0, "16:9"),         # Degenerate guard
        ],
    )
    def test_aspect_key_detection(self, width: int, height: int, expected_key: str):
        assert CoordinateEngine.detect_aspect_key(width, height) == expected_key

    @pytest.mark.parametrize(
        "width,height",
        [
            (1920, 1080),  # 16:9 FHD
            (2560, 1440),  # 16:9 QHD
            (2560, 1600),  # 16:10 WQXGA
        ],
    )
    def test_uv_physical_round_trip_accuracy(self, width: int, height: int):
        test_uvs = [
            (0.0, 0.0),
            (0.5, 0.5),
            (1.0, 1.0),
            (0.0885, 0.1950),  # Role UV
            (0.1180, 0.3050),  # Agent UV
            (0.5000, 0.8150),  # Lock-in UV
        ]
        for u, v in test_uvs:
            px, py = CoordinateEngine.uv_to_physical(u, v, width, height)
            assert 0 <= px <= width
            assert 0 <= py <= height

            # Invert back to UV
            recovered_u, recovered_v = CoordinateEngine.physical_to_uv(px, py, width, height)
            # Bi-directional accuracy within physical single-pixel granularity
            pixel_u_epsilon = 1.0 / width
            pixel_v_epsilon = 1.0 / height
            assert abs(recovered_u - u) <= pixel_u_epsilon + 1e-4
            assert abs(recovered_v - v) <= pixel_v_epsilon + 1e-4

    def test_uv_clamping_and_bounds(self):
        w, h = 1920, 1080
        # Underflow clamped to 0
        assert CoordinateEngine.uv_to_physical(-0.5, -1.0, w, h) == (0, 0)
        # Overflow clamped to width, height
        assert CoordinateEngine.uv_to_physical(1.5, 2.0, w, h) == (w, h)

        # Physical clamping to [0.0, 1.0]
        assert CoordinateEngine.physical_to_uv(-100, -50, w, h) == (0.0, 0.0)
        assert CoordinateEngine.physical_to_uv(3000, 2000, w, h) == (1.0, 1.0)


class TestConfigManager:
    """Verifies ConfigManager atomic read/write integrity, schema validation, and fallback."""

    def test_auto_generate_default_config(self, tmp_path: Path):
        cfg_file = tmp_path / "overlay_config.json"
        assert not cfg_file.exists()

        mgr = ConfigManager(str(cfg_file))
        assert cfg_file.exists()
        assert mgr.data["active_preset_index"] == 0
        assert len(mgr.data["presets"]) == 3
        assert mgr.data["presets"][0]["name"] == "Jett (Duelist)"
        assert "16:9" in mgr.data["presets"][0]["aspect_profiles"]
        assert "16:10" in mgr.data["presets"][0]["aspect_profiles"]

    def test_atomic_write_and_reload_round_trip(self, tmp_path: Path):
        cfg_file = tmp_path / "overlay_config.json"
        mgr = ConfigManager(str(cfg_file))

        # Mutate configuration
        mgr.data["active_preset_index"] = 2
        mgr.data["reticle_opacity"] = 0.95
        mgr.data["presets"][0]["aspect_profiles"]["16:9"]["agent_uv"] = [0.1234, 0.5678]
        mgr.save()

        # Ensure no leftover temporary file
        assert not (tmp_path / "overlay_config.json.tmp").exists()

        # Reload in a separate instance
        reloaded = ConfigManager(str(cfg_file))
        assert reloaded.data["active_preset_index"] == 2
        assert reloaded.data["reticle_opacity"] == 0.95
        assert reloaded.data["presets"][0]["aspect_profiles"]["16:9"]["agent_uv"] == [0.1234, 0.5678]

    def test_corrupted_json_fallback(self, tmp_path: Path):
        cfg_file = tmp_path / "corrupted_config.json"
        cfg_file.write_text("{ incomplete json content ...", encoding="utf-8")

        mgr = ConfigManager(str(cfg_file))
        assert mgr.data["active_preset_index"] == 0
        assert len(mgr.data["presets"]) == 3


class TestWin32Bridge:
    """Verifies Win32 system tuning profile and DPI awareness."""

    def test_apply_efficiency_scheduler_profile_executes_cleanly(self):
        # Must execute on Windows 11 without raising OSError/WinError
        try:
            apply_efficiency_scheduler_profile(prefer_last_n_cores=4)
        except Exception as exc:
            pytest.fail(f"apply_efficiency_scheduler_profile raised an unexpected exception: {exc}")

    def test_enable_per_monitor_dpi_v2_executes_cleanly(self):
        try:
            enable_per_monitor_dpi_v2()
        except Exception as exc:
            pytest.fail(f"enable_per_monitor_dpi_v2 raised an unexpected exception: {exc}")
