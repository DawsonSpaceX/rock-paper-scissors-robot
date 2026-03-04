#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y python3-venv python3-pip build-essential libgl1 libglib2.0-0 curl

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

mkdir -p models
if [ ! -f models/hand_landmarker.task ]; then
  curl -L "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" -o models/hand_landmarker.task
fi

echo "Install complete. Run: source .venv/bin/activate && PYTHONPATH=src python -m rps_web.main --host 0.0.0.0 --port 8000"
