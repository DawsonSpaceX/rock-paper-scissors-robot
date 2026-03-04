#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

source .venv/bin/activate

echo "=== System ==="
uname -a || true
cat /etc/os-release || true

echo "=== Python ==="
python --version
which python

echo "=== Installed packages ==="
pip show mediapipe || true
pip show opencv-python || true

echo "=== MediaPipe native lib dependencies ==="
python - <<'PY'
from pathlib import Path
import mediapipe
lib = Path(mediapipe.__file__).resolve().parent / "tasks" / "c" / "libmediapipe.so"
print(lib)
PY
LIB_PATH=$(python - <<'PY'
from pathlib import Path
import mediapipe
print(Path(mediapipe.__file__).resolve().parent / "tasks" / "c" / "libmediapipe.so")
PY
)
ldd "$LIB_PATH" || true

echo "=== App startup ==="
PYTHONPATH=src python -m rps_web.main --host 0.0.0.0 --port 8000
