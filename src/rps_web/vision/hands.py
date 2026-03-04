from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import cv2
import mediapipe as mp
import numpy as np


@dataclass
class HandDetection:
    present: bool
    landmarks: Optional[Any]
    y_px: Optional[float]


class HandTracker:
    def __init__(self) -> None:
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
            model_complexity=0,
        )

    def process(self, frame_bgr: np.ndarray) -> HandDetection:
        h, w, _ = frame_bgr.shape
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        result = self.hands.process(frame_rgb)

        if not result.multi_hand_landmarks:
            return HandDetection(False, None, None)

        lm = result.multi_hand_landmarks[0]
        y_px = lm.landmark[self.mp_hands.HandLandmark.WRIST].y * h
        return HandDetection(True, lm, y_px)

    def draw(self, frame_bgr: np.ndarray, landmarks: Any) -> None:
        self.mp_draw.draw_landmarks(frame_bgr, landmarks, self.mp_hands.HAND_CONNECTIONS)

    def close(self) -> None:
        self.hands.close()
