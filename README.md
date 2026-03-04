# rock-paper-scissors-robot

A Raspberry Pi Rock–Paper–Scissors robot: camera detects your hand gesture, game logic picks a move, and the robot acts it out.

## Goals
- Run on Raspberry Pi (Pi 5) with camera input
- Detect Rock / Paper / Scissors from live video (MediaPipe)
- Stable game loop (countdown → lock player move → reveal → score)
- Hardware layer with a **mock** mode (runs anywhere) + **Pi** mode (GPIO/servos/etc.)

## Repo Structure (planned)
