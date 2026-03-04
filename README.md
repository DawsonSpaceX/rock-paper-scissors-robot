# Rock Paper Scissors Robot (Web + MediaPipe + Raspberry Pi)

A browser-based Rock Paper Scissors game using a USB webcam, **MediaPipe Tasks API (Hand Landmarker)**, and OpenCV.
It is designed for Raspberry Pi 5 and remote access from Windows using SSH port forwarding.

## Features

- FastAPI web app with:
  - `GET /` UI page
  - `GET /stream` MJPEG live video stream with landmark overlay
  - `WS /ws` real-time game state updates
- Hand tracking with MediaPipe **Tasks API** Hand Landmarker
- Fist detection heuristic for robust rock/start gesture
- Motion-based **bob detection** (down→up) with smoothing + debouncing
- Selection cycle logic:
  - start: Rock
  - bob 1: Paper
  - bob 2: Scissors
  - continues cyclically
- Lock rules:
  - lock immediately at bob count 3
  - OR lock after 1 second idle after at least one bob
- Game engine scoring (you/cpu/ties)
- Safe threaded camera/vision loop and graceful shutdown

## Repository structure

```text
src/rps_web/
  __init__.py
  main.py
  config.py
  camera/opencv_cam.py
  vision/hands.py
  vision/motion.py
  vision/gesture.py
  game/engine.py
  web/templates/index.html
  web/static/app.js
  web/static/style.css
scripts/pi_install.sh
requirements.txt
.env.example
```

## Raspberry Pi install

```bash
bash scripts/pi_install.sh
```

This script updates apt, installs build/runtime dependencies, creates `.venv`, installs Python deps, and downloads the Hand Landmarker model file.

## Run on Raspberry Pi

```bash
cd ~/Documents/rock-paper-scissors-robot
git checkout main
git pull

# First-time setup only
bash scripts/pi_install.sh

cp -n .env.example .env
source .venv/bin/activate
PYTHONPATH=src python -m rps_web.main --host 0.0.0.0 --port 8000
```

## Access from Windows via SSH tunnel

On Windows (PowerShell/CMD):

```bash
ssh -L 8000:localhost:8000 pi@<PI_IP>
```

Then open:

- <http://localhost:8000>

You can also view from LAN directly if server binds to `0.0.0.0` and firewall allows port 8000.

## Gameplay notes

1. Show your hand to the camera.
2. Make a fist (rock) to enter tracking mode.
3. Bob hand **down then up** to advance selection.
4. Selection locks when:
   - bob count reaches 3, or
   - no new bob for `LOCK_IDLE_SEC` after at least one bob.
5. CPU move and round result appear for ~2 seconds, then round resets.

## Config (`.env`)

- `OPENCV_DEVICE=0`
- `WIDTH=640`
- `HEIGHT=480`
- `FPS=30`
- `HOST=0.0.0.0`
- `PORT=8000`
- `BOB_THRESHOLD_PX=35`
- `BOB_COOLDOWN_MS=300`
- `LOCK_IDLE_SEC=1.0`
- `MEDIAPIPE_MODEL_PATH=models/hand_landmarker.task`
- `MEDIAPIPE_AUTO_DOWNLOAD_MODEL=true`

## Troubleshooting

- If camera fails, UI shows *Camera not available* and logs include device tips.
- Verify webcam exists as `/dev/video0` (or set `OPENCV_DEVICE`).
- Ensure the model file exists at `MEDIAPIPE_MODEL_PATH`; install script downloads it.
- Use `MEDIAPIPE_MODEL_PATH` (not `HAND_MODEL_PATH`) if setting the model path manually.
- If you see this startup error on Raspberry Pi:

  ```
  OSError: .../mediapipe/tasks/c/libmediapipe.so: undefined symbol: _ZN12carotene_o4t24isSupportedConfigurationEv
  ```

  do a clean reinstall with system OpenCV dev packages removed (they can conflict with the Python wheel MediaPipe expects):

  ```bash
  cd ~/Documents/rock-paper-scissors-robot
  deactivate 2>/dev/null || true
  rm -rf .venv
  sudo apt remove -y libopencv-dev
  sudo apt autoremove -y
  bash scripts/pi_install.sh
  source .venv/bin/activate
  PYTHONPATH=src python -m rps_web.main --host 0.0.0.0 --port 8000
  ```

- If it still fails on Raspberry Pi OS with Python 3.12, use a Python 3.11 virtualenv for this project, then reinstall requirements and run again.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=src python -m rps_web.main
```
