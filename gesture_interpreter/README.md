# Gesture interpreter (EMG)

Maps **binary EMG vectors** `[bicep, forearm, shoulder, thumb]` (per sample) over a **time window** to **combined patterns** `(1,1,0,0)` and **robot command strings** (`HOME`, `MOVE_FORWARD`, …).

## Layout

| Path | Role |
|------|------|
| `interpreter.py` | `interpret_gesture(features_dict)` — legacy placeholder for ML pipeline |
| `gesture_config.py` | `GESTURE_NAMES` list |
| `gesture_commands.py` | Named command strings for the Kinova pipeline |
| `sim/gesture_interpreter_sim.py` | **Simulation**: `Deque[(t, List[int])]`, per-muscle counts → combined tuple → command; window, cooldown, logging, harness |
| `sim/__init__.py` | Lazy exports: `GestureInterpreter`, `generate_binary_pattern`, `generate_fixed_pattern` |

## Run the simulator

From project root:

```bash
python -m gesture_interpreter.sim.gesture_interpreter_sim
```

## ROS 2 (Jazzy)

Build and run the gesture node from the repo root — see **`README_ROS2.md`** (`colcon build`, `gesture_interpreter_ros`).

## SSVEP

Flicker-based commands use **`ssvep_interpreter/`** at the repo root (separate from EMG gestures).
