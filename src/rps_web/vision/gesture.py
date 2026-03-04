from __future__ import annotations

import math
from typing import Any


def _dist(a: Any, b: Any) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def is_fist(landmarks: Any) -> bool:
    if not landmarks:
        return False

    # MediaPipe Tasks API landmark indices
    WRIST = 0
    INDEX_MCP, INDEX_PIP, INDEX_TIP = 5, 6, 8
    MIDDLE_MCP, MIDDLE_PIP, MIDDLE_TIP = 9, 10, 12
    RING_MCP, RING_PIP, RING_TIP = 13, 14, 16
    PINKY_MCP, PINKY_PIP, PINKY_TIP = 17, 18, 20

    wrist = landmarks[WRIST]
    fingers = [
        (INDEX_MCP, INDEX_PIP, INDEX_TIP),
        (MIDDLE_MCP, MIDDLE_PIP, MIDDLE_TIP),
        (RING_MCP, RING_PIP, RING_TIP),
        (PINKY_MCP, PINKY_PIP, PINKY_TIP),
    ]

    curled = 0
    for mcp_i, pip_i, tip_i in fingers:
        mcp = landmarks[mcp_i]
        pip = landmarks[pip_i]
        tip = landmarks[tip_i]
        y_curled = tip.y > pip.y
        d_curled = _dist(tip, wrist) < _dist(mcp, wrist) * 1.05
        if y_curled or d_curled:
            curled += 1

    return curled >= 3
