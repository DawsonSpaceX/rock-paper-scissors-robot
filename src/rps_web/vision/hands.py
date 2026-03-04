from __future__ import annotations

import logging
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

try:
    from mediapipe.python.solutions.hands_connections import (
        HAND_CONNECTIONS as MP_HAND_CONNECTIONS,
    )
except ImportError:
    MP_HAND_CONNECTIONS = None

logger = logging.getLogger(__name__)

_FALLBACK_HAND_CONNECTIONS = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (0, 17),
    (17, 18),
    (18, 19),
    (19, 20),
]

if MP_HAND_CONNECTIONS is None:
    HAND_CONNECTIONS = _FALLBACK_HAND_CONNECTIONS
    logger.info("Using fallback MediaPipe hand connections topology")
else:
    HAND_CONNECTIONS = list(MP_HAND_CONNECTIONS)
    logger.info("Using canonical MediaPipe hand connections topology")

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"


@dataclass
class HandDetection:
    present: bool
    landmarks: Optional[list]
    y_px: Optional[float]
    confidence: float = 0.0


class HandTracker:
    def __init__(self, model_path: str, auto_download_model: bool = True) -> None:
        model_file = Path(model_path)
        if not model_file.exists() and auto_download_model:
            model_file.parent.mkdir(parents=True, exist_ok=True)
            logger.info("MediaPipe hand model missing; downloading to %s", model_file)
            urllib.request.urlretrieve(MODEL_URL, model_file)

        if not model_file.exists():
            raise FileNotFoundError(
                f"MediaPipe model not found at {model_file}. "
                "Set MEDIAPIPE_MODEL_PATH or enable MEDIAPIPE_AUTO_DOWNLOAD_MODEL=true."
            )

        base_options = python.BaseOptions(model_asset_path=str(model_file))
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.6,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        try:
            self.landmarker = vision.HandLandmarker.create_from_options(options)
        except OSError as exc:
            if "isSupportedConfiguration" in str(exc):
                raise RuntimeError(
                    "MediaPipe failed to load native libraries. On Raspberry Pi, this is often a Python/OpenCV ABI mismatch. "
                    "Recreate the venv with python3.11 and reinstall requirements."
                ) from exc
            raise

    def process(self, frame_bgr: np.ndarray) -> HandDetection:
        h, _, _ = frame_bgr.shape
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
        result = self.landmarker.detect(mp_image)

        if not result.hand_landmarks:
            return HandDetection(False, None, None, 0.0)

        landmarks = result.hand_landmarks[0]
        confidence = result.handedness[0][0].score if result.handedness else 0.0
        y_px = landmarks[0].y * h  # wrist
        return HandDetection(True, landmarks, y_px, confidence)

    def draw(self, frame_bgr: np.ndarray, landmarks: list) -> None:
        h, w, _ = frame_bgr.shape

        for point in landmarks:
            x = int(point.x * w)
            y = int(point.y * h)
            cv2.circle(frame_bgr, (x, y), 3, (0, 255, 0), -1)

        for start_idx, end_idx in HAND_CONNECTIONS:
            p1 = landmarks[start_idx]
            p2 = landmarks[end_idx]
            x1, y1 = int(p1.x * w), int(p1.y * h)
            x2, y2 = int(p2.x * w), int(p2.y * h)
            cv2.line(frame_bgr, (x1, y1), (x2, y2), (255, 200, 0), 2)

    def close(self) -> None:
        self.landmarker.close()
