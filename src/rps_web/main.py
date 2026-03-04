from __future__ import annotations

import argparse
import asyncio
import logging
import threading
import time
from pathlib import Path
from typing import Optional

import cv2
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from rps_web.camera.opencv_cam import OpenCVCamera
from rps_web.config import settings
from rps_web.game.engine import GameEngine
from rps_web.vision.gesture import is_fist
from rps_web.vision.hands import HandTracker
from rps_web.vision.motion import BobDetector

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"

templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))

app = FastAPI(title="RPS Web")
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")


class AppRuntime:
    def __init__(self) -> None:
        self.camera = OpenCVCamera(settings.opencv_device, settings.width, settings.height, settings.fps)
        self.tracker = HandTracker(settings.mediapipe_model_path, settings.mediapipe_auto_download_model)
        self.engine = GameEngine(BobDetector(settings.bob_threshold_px, settings.bob_cooldown_ms), settings.lock_idle_sec)
        self.annotated_frame: Optional[bytes] = None
        self.frame_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.fps = 0.0

    def start(self) -> None:
        self.camera.open()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def _loop(self) -> None:
        last = time.monotonic()
        while not self.stop_event.is_set():
            frame = self.camera.read()
            if frame is None:
                self.engine.update(False, False, None, camera_available=self.camera.available)
                self._set_frame(self._camera_unavailable_frame())
                continue

            detection = self.tracker.process(frame)
            fist = is_fist(detection.landmarks) if detection.present else False
            self.engine.update(detection.present, fist, detection.y_px, camera_available=True)

            if detection.present and detection.landmarks is not None:
                self.tracker.draw(frame, detection.landmarks)

            snap = self.engine.snapshot()
            now = time.monotonic()
            dt = now - last
            if dt > 0:
                self.fps = 0.9 * self.fps + 0.1 * (1.0 / dt)
            last = now

            cv2.putText(frame, f"Selection: {snap['selection']}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (30, 255, 30), 2)
            cv2.putText(frame, f"Phase: {snap['phase']}", (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 50), 2)
            cv2.putText(frame, f"FPS: {self.fps:.1f}", (10, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 255), 2)

            ok, jpg = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ok:
                self._set_frame(jpg.tobytes())

    def _camera_unavailable_frame(self) -> bytes:
        import numpy as np
        frame = np.zeros((settings.height, settings.width, 3), dtype="uint8")
        cv2.putText(frame, "Camera not available", (30, settings.height // 2), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        ok, jpg = cv2.imencode(".jpg", frame)
        return jpg.tobytes() if ok else b""

    def _set_frame(self, frame_jpeg: bytes) -> None:
        with self.frame_lock:
            self.annotated_frame = frame_jpeg

    def get_frame(self) -> Optional[bytes]:
        with self.frame_lock:
            return self.annotated_frame

    def stop(self) -> None:
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        self.camera.close()
        self.tracker.close()


runtime = AppRuntime()


@app.on_event("startup")
def startup() -> None:
    runtime.start()


@app.on_event("shutdown")
def shutdown() -> None:
    runtime.stop()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


def mjpeg_generator():
    while True:
        frame = runtime.get_frame()
        if frame is None:
            time.sleep(0.03)
            continue
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
        )
        time.sleep(0.03)


@app.get("/stream")
def stream() -> StreamingResponse:
    return StreamingResponse(mjpeg_generator(), media_type="multipart/x-mixed-replace; boundary=frame")


@app.websocket("/ws")
async def ws_state(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(runtime.engine.snapshot())
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run RPS web server")
    parser.add_argument("--host", default=settings.host)
    parser.add_argument("--port", type=int, default=settings.port)
    return parser.parse_args()


def run() -> None:
    import uvicorn

    args = parse_args()
    uvicorn.run("rps_web.main:app", host=args.host, port=args.port, reload=False)


if __name__ == "__main__":
    run()
