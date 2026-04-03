# OpenBCI Communication & ML Pipeline

EEG/biosignal processing pipeline for OpenBCI (Cyton) data, with a path to SSVEP-based robotic control and ROS integration.

## Setup

- **Hardware**: OpenBCI Cyton (reference + DRL + 2 channels used here for bicep).
- **Data**: Record via OpenBCI GUI → export CSV, or (later) stream via serial or LSL.

## Repo structure

| Path | Description |
|------|-------------|
| `openbci_ml_pipeline.py` | Load OpenBCI CSV → preprocess → segment → extract features → save `features.csv` |
| **`stream_openbci.py`** | **Real-time:** stream from Cyton (BrainFlow); print features or, with `--ssvep`, command (FRONT/LEFT/etc.) every window |
| `config/pipeline_config.py` | Channel indices (bicep), filter settings, window length, output path, **COM port for streaming** |
| `config/ssvep_config.py` | **SSVEP flicker frequencies** → robot commands (FRONT 5 Hz, BACK 10 Hz, LEFT 15 Hz, RIGHT 25 Hz, STARTSTOP 50 Hz) |
| `docs/CONNECTING_OPENBCI_TO_ML.md` | How to get data from OpenBCI into the pipeline (file / serial / LSL; no API) |
| `requirements.txt` | Python dependencies (numpy, pandas, scipy, matplotlib) |

## Step-by-step guide

**New to this repo?** Follow **[docs/STEP_BY_STEP_GUIDE.md](docs/STEP_BY_STEP_GUIDE.md)** for full instructions: hardware setup → COM port → config → run stream (features or `--ssvep` commands).

## Quick start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set your bicep channel indices in `config/pipeline_config.py` (e.g. `BICEP_CHANNEL_INDICES = [2, 3]` if bicep is on EXG 2 and 3).
3. Run the pipeline on a recording:
   ```bash
   python openbci_ml_pipeline.py path/to/your_openbci_recording.csv
   ```
   Optional: `python openbci_ml_pipeline.py recording.csv my_features.csv --plot`

Output: `features.csv` (one row per time window) and optionally a plot of preprocessed channels.

### Real-time streaming from the Cyton board

1. Set your COM port in `config/pipeline_config.py` (`CYTON_SERIAL_PORT`, e.g. `"COM4"` on Windows).
2. Connect the Cyton via USB and run:
   ```bash
   pip install brainflow
   python stream_openbci.py
   ```
   Override port: `python stream_openbci.py --port COM3`. Press **Ctrl+C** to stop.
3. For **SSVEP → command** output: set channel indices to occipital (e.g. O1, Oz, O2), then run `python stream_openbci.py --ssvep` to print one command per window (FRONT, LEFT, etc.). See ** [docs/OUTPUT_AND_INTERPRETATION.md](docs/OUTPUT_AND_INTERPRETATION.md)** for what the program outputs and how to get commands.

## EMG gesture interpreter & ROS 2 (Kinova / lab pipeline)

- **`gesture_interpreter/`** — 4-channel binary EMG `[bicep, forearm, shoulder, thumb]`, time window, combined patterns → command strings (`HOME`, `MOVE_FORWARD`, …).
- **`gesture_interpreter_ros/`** — ROS 2 Jazzy node: subscribes to `/emg_commands`, publishes `/robot_commands` and deadman-gated `/robot_motion_command`.
- **`cyton_emg_ros/`** — ROS 2 node: OpenBCI Cyton (BrainFlow) → `/emg_commands` (Phase 2 pipeline).
- **Build & run (Ubuntu 24.04 + Jazzy):** see **[README_ROS2.md](README_ROS2.md)** (`colcon build`, Raspberry Pi or lab PC).
- **Layout:** [docs/PROJECT_LAYOUT.md](docs/PROJECT_LAYOUT.md), Pi notes: [docs/RASPBERRY_PI_LAYOUT.md](docs/RASPBERRY_PI_LAYOUT.md).

## Roadmap

- **Phase 2 (current)**: ML pipeline for processing OpenBCI data (this repo).
- **Phase 2 (SSVEP)**: Classify flicker frequency → map to robot commands.
- **Phase 3**: ROS integration — SSVEP / EMG commands to robot (Husky `cmd_vel`, Kinova gesture strings via `gesture_interpreter_ros`).

## Pushing to GitHub

To store this project in a new GitHub repo, see **[docs/GITHUB_SETUP.md](docs/GITHUB_SETUP.md)** for step-by-step instructions (create repo on GitHub, then add remote, commit, push).

## License

Use as needed for research / coursework; adjust license as required by your institution.
