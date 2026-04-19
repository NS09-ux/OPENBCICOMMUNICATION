# ROS 2 Jazzy — EMG gesture interpreter + Cyton bridge

This workspace contains **three** **colcon** packages:

| Package | Role |
|---------|------|
| `gesture_interpreter` | Pure Python: 4× binary EMG → combined pattern → command string |
| `gesture_interpreter_ros` | `rclpy` node: `/emg_commands` → `/robot_commands` + deadman-gated `/robot_motion_command` |
| `cyton_emg_ros` | **Phase 2:** Cyton via **BrainFlow** → `/emg_commands` (`Int32MultiArray` length 4) |

## BrainFlow on the Pi (required for real hardware)

BrainFlow is **not** installed by `apt` with ROS. Install once (system or user):

```bash
pip install brainflow
# or: pip install --user brainflow
```

Use the same Python ROS uses (`which python3`). If `ros2 run` cannot import brainflow, try `pip3 install brainflow` or a venv aligned with your ROS setup.

## Build (Ubuntu 24.04 / Raspberry Pi / lab PC with Jazzy)

```bash
cd /path/to/OPENBCICOMMUNICATION
source /opt/ros/jazzy/setup.bash
colcon build --packages-select gesture_interpreter gesture_interpreter_ros cyton_emg_ros
source install/setup.bash
```

On Raspberry Pi, **omit** `--symlink-install` if colcon errors on `rmtree` / `Invalid argument`.

## Configure muscles → Cyton EXG channels

Edit **`config/pipeline_config.py`**:

- **`EMG_COMMANDS_EXG_INDICES`** — four indices `0…15` for **[bicep, forearm, shoulder, thumb]** (must match wiring).
- **`EMG_COMMANDS_THRESHOLD_UV`** — single µV threshold or tune per channel via ROS params.
- **`CYTON_SERIAL_PORT`** — e.g. `/dev/ttyACM0` or `/dev/ttyUSB0` on Pi; overridden by ROS param `serial_port`.
- **`CYTON_DAISY`** — `True` if using Daisy (16 EXG); must match ROS param `use_daisy`.

When you run from the **source tree**, `cyton_emg_publisher` loads these as defaults. After `colcon install`, set params in launch or CLI if defaults are wrong.

## Run Cyton → `/emg_commands` only

1. Plug in Cyton USB; confirm port (`dmesg | tail`, or `ls /dev/ttyACM*`).
2. Launch (edit `serial_port` in the launch file if needed):

```bash
ros2 launch cyton_emg_ros cyton_emg.launch.py
```

Override examples:

```bash
ros2 run cyton_emg_ros cyton_emg_publisher --ros-args \
  -p serial_port:=/dev/ttyUSB0 \
  -p threshold_microvolts:="[80.0, 80.0, 90.0, 70.0]"
```

### No hardware (smoke test)

Publishes `[0,0,0,0]` at the configured rate:

```bash
ros2 run cyton_emg_ros cyton_emg_publisher --ros-args -p simulate:=true
```

## Run Cyton + gesture interpreter together

```bash
ros2 launch cyton_emg_ros emg_and_gesture.launch.py
```

Hold deadman (default `deadman_source:=topic`):

```bash
ros2 topic pub /deadman std_msgs/msg/Bool "{data: true}" --rate 10
```

## Run gesture node alone (fake EMG)

```bash
ros2 run gesture_interpreter_ros gesture_interpreter_node
# or
ros2 launch gesture_interpreter_ros gesture_interpreter.launch.py
```

### Topics

| Topic | Type | Meaning |
|-------|------|---------|
| `/emg_commands` | `std_msgs/msg/Int32MultiArray` | Four values `[bicep, forearm, shoulder, thumb]` (0/1) |
| `/robot_commands` | `std_msgs/msg/String` | Command whenever a gesture is detected (always) |
| `/robot_motion_command` | `std_msgs/msg/String` | Same command **only while deadman is active**; empty string otherwise |
| `/deadman_active` | `std_msgs/msg/Bool` | Echo of whether motion is allowed |
| `/deadman` | `std_msgs/msg/Bool` | **Input** when `deadman_source:=topic` (hold `true` to allow motion) |

### Gesture node parameters

- `deadman_source`: `topic` (default) | `keyboard` (space via optional `pynput`) | `always_on` (testing)
- `window_s`, `min_activation_count`, `cooldown_s`, `emit_unknown` — passed to `GestureInterpreter`

### Cyton publisher parameters

- `simulate`, `serial_port`, `use_daisy`, `exg_indices`, `threshold_microvolts`, `envelope_samples`, `publish_rate_hz`, `emg_topic`

### Echo `/emg_commands` in a second terminal

While `cyton_emg_publisher` is running:

```bash
source /opt/ros/jazzy/setup.bash
source ~/OPENBCICOMMUNICATION/install/setup.bash
ros2 run cyton_emg_ros emg_commands_receiver
```

Optional: `-p log_hz:=10.0` to change how often lines print (rate-limited logging).

### Quick test without Cyton (fake EMG)

```bash
ros2 run gesture_interpreter_ros gesture_interpreter_node --ros-args -p deadman_source:=always_on
ros2 topic pub /emg_commands std_msgs/msg/Int32MultiArray "{data: [1,1,1,1]}" --rate 20
```

## Kinova Gen3 / `ros2_kortex`

This repo **does not** install or launch Kortex. Your lab stack should:

1. Subscribe to **`/robot_motion_command`** (`std_msgs/String`) — or **`/robot_commands`** if you accept the risk without deadman.
2. Map command strings (`HOME`, `MOVE_FORWARD`, …) to **MoveIt / kortex_driver** actions or joint trajectories.
3. Run **Gazebo / RViz** from the official `ros2_kortex` bringup on a capable machine.

See [Kinova ros2_kortex](https://github.com/Kinovarobotics/ros2_kortex).

## Windows development

ROS 2 is not typically built on Windows in this layout; edit here, then build and run on Ubuntu 24.04 + Jazzy (Pi or lab PC).
