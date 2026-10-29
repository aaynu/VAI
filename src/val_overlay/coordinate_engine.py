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
