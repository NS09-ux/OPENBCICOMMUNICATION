# Full Code Layout: Option B — Everything on Raspberry Pi 4

Everything runs on the Pi: Cyton plugs into the Pi; the Pi runs the BCI stream, interpretation, and robot commands.

---

## 1. Hardware

```
[Cyton + Dongle]  --USB-->  [Raspberry Pi 4]  --USB/Network-->  [Robot base]
                                    |
                              (WiFi optional:
                               for monitoring
                               from laptop)
```

- **Cyton USB dongle** → Pi’s USB port (e.g. `/dev/ttyUSB0` on Linux).
- **Pi** → Robot via USB serial, or network (e.g. ROS over Ethernet/WiFi to robot’s computer), depending on the robot.

---

## 2. Software Stack on the Pi

| Layer        | Role |
|-------------|------|
| OS          | Raspberry Pi OS (64-bit recommended). |
| Python      | 3.8+ (usually preinstalled). |
| BrainFlow   | `pip install brainflow` — talks to Cyton. |
| ROS (optional) | If the robot uses ROS: install ROS on Pi (e.g. ROS Noetic or Melodic, or ROS 2). If the robot has a simple serial/HTTP API, you can skip ROS. |
| This repo   | Cloned/copied onto the Pi (stream, config, SSVEP interpreter, bridge to robot). |

---

## 3. Directory Layout on the Pi

Suggested folder structure (you can clone the current repo and add the Pi/robot parts):

```
OPENBCICOMMUNICATION/          # Same repo as on your PC (clone or copy)
├── config/
│   ├── __init__.py
│   ├── pipeline_config.py     # COM port = /dev/ttyUSB0 (or ttyACM0), channel indices
│   └── ssvep_config.py        # FRONT/BACK/LEFT/RIGHT/STARTSTOP frequencies
├── openbci_ml_pipeline.py     # Load CSV, preprocess, features (used by stream)
├── stream_openbci.py          # Real-time stream from Cyton (BrainFlow)
├── ssvep_interpreter/         # Window → command (FRONT/LEFT/etc.)
├── gesture_interpreter/       # EMG features → gesture (optional)
├── bci_to_robot.py            # NEW: runs stream + sends command to robot (no ROS or with ROS)
├── robot_driver.py            # NEW: abstract “send command to robot” (ROS or serial/HTTP)
├── requirements.txt           # numpy, pandas, scipy, brainflow (matplotlib optional)
├── docs/
│   ├── RASPBERRY_PI_LAYOUT.md # This file
│   └── ...
└── README.md
```

**New files for Option B:**

- **`bci_to_robot.py`**  
  - Entry point on the Pi.  
  - Starts the Cyton stream (BrainFlow), runs SSVEP (or feature) pipeline, gets one command per window.  
  - Calls the robot driver with that command (e.g. "FRONT", "LEFT").  
  - Handles shutdown (Ctrl+C) and optional timeout (stop robot if no command for X seconds).

- **`robot_driver.py`**  
  - Single interface: `set_command("FRONT")` / `set_command("LEFT")` / `stop()`.  
  - Implementation depends on the robot:
    - **If robot uses ROS:** publish `geometry_msgs/Twist` to `cmd_vel` (or subscribe to `bci_cmd` and convert to Twist).
    - **If robot has serial/HTTP API:** send the appropriate bytes or HTTP request from the Pi.

---

## 4. Data Flow (No Code, Just Flow)

```
1. Cyton (USB) → BrainFlow on Pi
2. BrainFlow → stream_openbci.run_stream(..., ssvep=True)
3. Every window (~1 s): SSVEP interpreter → command string ("FRONT", "LEFT", …)
4. bci_to_robot passes command to robot_driver
5. robot_driver converts to robot-specific action (Twist / serial / HTTP)
6. Robot moves
```

Optional: if no command for N seconds, robot_driver.stop() so the robot halts.

---

## 5. Config on the Pi

- **`config/pipeline_config.py`**
  - `CYTON_SERIAL_PORT = "/dev/ttyUSB0"` (or `"/dev/ttyACM0"` — check with `ls /dev/tty*` with dongle plugged in).
  - `BICEP_CHANNEL_INDICES`: same as now if you keep the same electrodes (e.g. N2P, N7P → `[1, 6]`). For SSVEP, set to occipital channel indices.
- **`config/ssvep_config.py`**
  - No change; already has FRONT/BACK/LEFT/RIGHT/STARTSTOP frequencies.

---

## 6. Robot Driver Variants (Concept Only)

**6a) Robot uses ROS (e.g. Husky)**  
- `robot_driver` uses `rospy`.  
- On `set_command("FRONT")`: publish a Twist with `linear.x > 0`.  
- On `set_command("LEFT")`: publish Twist with `angular.z > 0`.  
- On `stop()` or timeout: publish Twist with zeros.  
- Topic: usually `cmd_vel` (`geometry_msgs/Twist`).  
- ROS master can run on the Pi (robot connects to Pi) or on the robot (Pi runs a node that publishes to the robot’s ROS master over network).

**6b) Robot has serial or simple API**  
- `robot_driver` opens a serial port or sends HTTP requests to the robot’s IP.  
- Same idea: map "FRONT"/"LEFT"/… to the bytes or API calls that make the robot move or stop.

---

## 7. Running on the Pi

- SSH or attach monitor/keyboard to the Pi.
- Clone/copy this repo onto the Pi.
- Install deps: `pip install -r requirements.txt` (and BrainFlow; on Pi you may need to use the Linux wheel or build from source if needed — check BrainFlow docs for ARM).
- Plug in the Cyton dongle; confirm port: `ls /dev/ttyUSB*` or `ls /dev/ttyACM*`.
- (Optional) If using ROS: install ROS, source `setup.bash`, then run your node.
- Run the single entry point:
  - `python bci_to_robot.py`
  - Or `python bci_to_robot.py --ssvep` if you use SSVEP commands.
- Stop with Ctrl+C; robot_driver should stop the robot on exit.

---

## 8. Summary Table

| Component        | Location  | Role |
|-----------------|-----------|------|
| Cyton + Dongle  | USB to Pi | Acquire EEG |
| BrainFlow       | Pi        | Read Cyton stream |
| stream_openbci  | Pi        | Buffer, filter, window, SSVEP or features |
| ssvep_interpreter/ | Pi     | Window → "FRONT"/"LEFT"/… |
| bci_to_robot    | Pi        | Orchestrate stream + call robot_driver |
| robot_driver    | Pi        | Map command string → robot motion (ROS or serial/API) |
| Robot           | Connected to Pi (or same ROS network) | Execute motion |

The repo includes `bci_to_robot.py` and `robot_driver.py`. On the Pi: run `python bci_to_robot.py --ssvep` to test (prints commands); run `python bci_to_robot.py --ssvep --robot ros` when using ROS to publish to cmd_vel.

This is the full layout for Option B; next step is to add the actual `bci_to_robot.py` and `robot_driver.py` implementations when you’re ready to code.
