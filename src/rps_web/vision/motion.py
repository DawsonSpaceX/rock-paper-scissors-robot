from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MotionState(str, Enum):
    IDLE = "idle"
    DOWN_CROSSED = "down_crossed"
    UP_CROSSED = "up_crossed"


@dataclass
class BobEvent:
    counted: bool
    bob_count: int


class BobDetector:
    def __init__(self, threshold_px: float, cooldown_ms: int, ema_alpha: float = 0.25) -> None:
        self.threshold_px = threshold_px
        self.cooldown = cooldown_ms / 1000.0
        self.ema_alpha = ema_alpha

        self.state = MotionState.IDLE
        self.baseline: Optional[float] = None
        self.smooth_y: Optional[float] = None
        self.last_bob_ts: float = 0.0
        self.bob_count = 0

    def reset(self) -> None:
        self.state = MotionState.IDLE
        self.baseline = None
        self.smooth_y = None
        self.bob_count = 0
        self.last_bob_ts = 0.0

    def update(self, y_px: Optional[float], enabled: bool) -> BobEvent:
        now = time.monotonic()
        if not enabled or y_px is None:
            self.state = MotionState.IDLE
            return BobEvent(False, self.bob_count)

        if self.smooth_y is None:
            self.smooth_y = y_px
        else:
            self.smooth_y = self.ema_alpha * y_px + (1 - self.ema_alpha) * self.smooth_y

        if self.baseline is None:
            self.baseline = self.smooth_y

        # Slowly adapt baseline to avoid drift while keeping sensitivity
        self.baseline = 0.02 * self.smooth_y + 0.98 * self.baseline

        dy = self.smooth_y - self.baseline

        if self.state == MotionState.IDLE:
            if dy > self.threshold_px:
                self.state = MotionState.DOWN_CROSSED

        elif self.state == MotionState.DOWN_CROSSED:
            if dy < -self.threshold_px * 0.5:
                self.state = MotionState.UP_CROSSED

        elif self.state == MotionState.UP_CROSSED:
            if now - self.last_bob_ts >= self.cooldown:
                self.bob_count += 1
                self.last_bob_ts = now
                self.state = MotionState.IDLE
                return BobEvent(True, self.bob_count)
            self.state = MotionState.IDLE

        return BobEvent(False, self.bob_count)
