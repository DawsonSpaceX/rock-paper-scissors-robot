from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional

from rps_web.vision.motion import BobDetector

logger = logging.getLogger(__name__)

MOVES = ["rock", "paper", "scissors"]


def _next_move(current: str) -> str:
    idx = MOVES.index(current)
    return MOVES[(idx + 1) % len(MOVES)]


def _judge(you: str, cpu: str) -> str:
    if you == cpu:
        return "tie"
    wins = {("rock", "scissors"), ("paper", "rock"), ("scissors", "paper")}
    return "win" if (you, cpu) in wins else "lose"


@dataclass
class GameSnapshot:
    phase: str = "waiting_for_fist"
    selection: str = "rock"
    locked: bool = False
    computer: Optional[str] = None
    result: Optional[str] = None
    score: dict = field(default_factory=lambda: {"you": 0, "cpu": 0, "ties": 0})
    camera_available: bool = True


class GameEngine:
    def __init__(self, detector: BobDetector, lock_idle_sec: float = 1.0, result_show_sec: float = 2.0) -> None:
        self.detector = detector
        self.lock_idle_sec = lock_idle_sec
        self.result_show_sec = result_show_sec

        self.lock = Lock()
        self.state = GameSnapshot()
        self.last_bob_time: Optional[float] = None
        self.round_end_time: Optional[float] = None

    def _lock_round(self) -> None:
        self.state.locked = True
        self.state.phase = "locked"
        self.state.computer = random.choice(MOVES)
        self.state.result = _judge(self.state.selection, self.state.computer)
        if self.state.result == "win":
            self.state.score["you"] += 1
        elif self.state.result == "lose":
            self.state.score["cpu"] += 1
        else:
            self.state.score["ties"] += 1
        self.round_end_time = time.monotonic() + self.result_show_sec
        logger.info("Round locked selection=%s cpu=%s result=%s score=%s", self.state.selection, self.state.computer, self.state.result, self.state.score)

    def _reset_round(self) -> None:
        self.state.phase = "waiting_for_fist"
        self.state.selection = "rock"
        self.state.locked = False
        self.state.computer = None
        self.state.result = None
        self.last_bob_time = None
        self.round_end_time = None
        self.detector.reset()

    def update(self, hand_present: bool, fist: bool, y_px: Optional[float], camera_available: bool = True) -> None:
        with self.lock:
            self.state.camera_available = camera_available
            now = time.monotonic()

            if self.state.locked:
                self.state.phase = "show_result"
                if self.round_end_time and now >= self.round_end_time:
                    self._reset_round()
                return

            enabled = hand_present and fist
            if not hand_present:
                self.state.phase = "no_hand"
            elif not fist:
                self.state.phase = "show_fist_to_start"
            else:
                self.state.phase = "tracking"

            event = self.detector.update(y_px, enabled=enabled)
            if event.counted:
                self.state.selection = _next_move(self.state.selection)
                self.last_bob_time = now
                logger.info("Bob detected count=%s selection=%s", event.bob_count, self.state.selection)
                if event.bob_count >= 3:
                    self._lock_round()
                    return

            if self.last_bob_time and event.bob_count >= 1 and (now - self.last_bob_time) >= self.lock_idle_sec:
                logger.info("Locking after idle timeout %.2fs", self.lock_idle_sec)
                self._lock_round()

    def snapshot(self) -> dict:
        with self.lock:
            return {
                "phase": self.state.phase,
                "selection": self.state.selection,
                "locked": self.state.locked,
                "computer": self.state.computer,
                "result": self.state.result,
                "score": self.state.score.copy(),
                "camera_available": self.state.camera_available,
            }
