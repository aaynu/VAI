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

    @staticmethod
    def get_default_config_path() -> str:
        cwd_path = os.path.abspath("overlay_config.json")
        if os.path.exists(cwd_path):
            return cwd_path
        appdata = os.environ.get("APPDATA")
        if appdata:
            vai_dir = os.path.join(appdata, "VAI")
            try:
                os.makedirs(vai_dir, exist_ok=True)
                return os.path.join(vai_dir, "overlay_config.json")
            except OSError:
                pass
        return cwd_path

    def __init__(self, filepath: Optional[str] = None) -> None:
        if filepath is None:
            filepath = self.get_default_config_path()
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
