#!/usr/bin/env bash
set -euo pipefail

sudo apt update
sudo apt install -y python3-venv python3-pip build-essential libgl1 libglib2.0-0 libopencv-dev

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Install complete. Run: source .venv/bin/activate && python -m rps_web.main --host 0.0.0.0 --port 8000"
