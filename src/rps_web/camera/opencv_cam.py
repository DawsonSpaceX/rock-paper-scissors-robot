from __future__ import annotations

import logging
import time
from threading import Lock
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class OpenCVCamera:
    def __init__(self, device: int = 0, width: int = 640, height: int = 480, fps: int = 30) -> None:
        self.device = device
        self.width = width
        self.height = height
        self.fps = fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.lock = Lock()
        self.last_frame: Optional[np.ndarray] = None
        self.available = False

    def open(self) -> bool:
        self.cap = cv2.VideoCapture(self.device)
        if not self.cap.isOpened():
            logger.error("Could not open webcam device index %s. Check /dev/video* permissions/device.", self.device)
            self.available = False
            return False

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
        actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
        actual_fps = float(self.cap.get(cv2.CAP_PROP_FPS) or 0.0)
        logger.info("Camera opened device=%s requested=%sx%s@%s actual=%sx%s@%.2f", self.device, self.width, self.height, self.fps, actual_w, actual_h, actual_fps)

        self.available = True
        return True

    def read(self) -> Optional[np.ndarray]:
        if self.cap is None:
            return None
        ok, frame = self.cap.read()
        if not ok:
            logger.warning("Failed to read frame from webcam")
            time.sleep(0.05)
            return None
        with self.lock:
            self.last_frame = frame
        return frame

    def get_last_frame(self) -> Optional[np.ndarray]:
        with self.lock:
            return None if self.last_frame is None else self.last_frame.copy()

    def close(self) -> None:
        if self.cap is not None:
            self.cap.release()
        self.available = False
        logger.info("Camera closed")
