from __future__ import annotations

from typing import Any

import math
import mediapipe as mp


def _dist(a: Any, b: Any) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def is_fist(landmarks: Any) -> bool:
    if landmarks is None:
        return False

    lms = landmarks.landmark
    hand = mp.solutions.hands.HandLandmark
    wrist = lms[hand.WRIST]

    fingers = [
        (hand.INDEX_FINGER_MCP, hand.INDEX_FINGER_PIP, hand.INDEX_FINGER_TIP),
        (hand.MIDDLE_FINGER_MCP, hand.MIDDLE_FINGER_PIP, hand.MIDDLE_FINGER_TIP),
        (hand.RING_FINGER_MCP, hand.RING_FINGER_PIP, hand.RING_FINGER_TIP),
        (hand.PINKY_MCP, hand.PINKY_PIP, hand.PINKY_TIP),
    ]

    curled = 0
    for mcp_i, pip_i, tip_i in fingers:
        mcp = lms[mcp_i]
        pip = lms[pip_i]
        tip = lms[tip_i]
        y_curled = tip.y > pip.y
        d_curled = _dist(tip, wrist) < _dist(mcp, wrist) * 1.05
        if y_curled or d_curled:
            curled += 1

    return curled >= 3
