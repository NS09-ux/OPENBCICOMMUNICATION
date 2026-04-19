# ROS 2 Jazzy — EMG gesture interpreter + Cyton bridge

## What this stack is for (lab goal)

**OpenBCI Cyton (muscle signals)** → binary **4× EMG** on **`/emg_commands`** → **named commands** (`HOME`, `MOVE_FORWARD`, …) on **`/robot_commands`** / **`/robot_motion_command`** (deadman-gated) → **`motion_command_bridge`** logs each new motion command (stub where you plug in **Kinova / MoveIt / `ros2_kortex`** on the machine that actually moves the arm).

The **`demo_gesture`** launch only **simulates** EMG (rotating patterns through every mapped command) to prove ROS wiring — **it does not move any robot**. Real muscle data comes from **`emg_and_gesture.launch.py`** with the Cyton connected. **Physical motion** requires a separate node (e.g. lab **`ros2_kortex`** / MoveIt) that subscribes to **`/robot_motion_command`** and executes trajectories; this repository stops at the **string command** boundary by design.

This workspace contains **three** **colcon** packages:

| Package | Role |
|---------|------|
| `gesture_interpreter` | Pure Python: 4× binary EMG → combined pattern → command string |
| `gesture_interpreter_ros` | `gesture_interpreter_node`: `/emg_commands` → `/robot_commands` + deadman-gated `/robot_motion_command`; **`motion_command_bridge`**: subscribe to motion commands (stub for robot driver) |
| `cyton_emg_ros` | Cyton via **BrainFlow** → `/emg_commands` (`Int32MultiArray` length 4) |

## BrainFlow on the Pi (required for real hardware)

BrainFlow is **not** installed by `apt` with ROS. Install once (system or user):

```bash
pip install brainflow
# or: pip install --user brainflow
```

Use the same Python ROS uses (`which python3`). If `ros2 run` cannot import brainflow, try `pip3 install brainflow` or a venv aligned with your ROS setup.

### `libBoardController.so: cannot open shared object file` (Pi / Linux)

The Python package is present but the dynamic linker cannot load BrainFlow’s `lib/` (or a dependency of `libBoardController.so` is missing).

1. **Confirm the file exists** (adjust `python3.12` to `python3 -c "import sys; print(sys.version_info)"`):

   ```bash
   ls -la "$HOME/.local/lib/python3.12/site-packages/brainflow/lib/"
   ```

2. **Export `LD_LIBRARY_PATH` in the same shell before `ros2 launch`** (path must match step 1):

   ```bash
   export LD_LIBRARY_PATH="$HOME/.local/lib/python3.12/site-packages/brainflow/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
   ```

3. **If the file exists but still fails**, check missing dependencies:

   ```bash
   ldd "$HOME/.local/lib/python3.12/site-packages/brainflow/lib/libBoardController.so" | grep "not found"
   ```

4. **`cyton_emg_publisher` prepends that `lib/` path automatically** (it searches **user site-packages** as well as `sys.path`, which fixes many `ros2 run` cases). Rebuild after `git pull`. If the `.so` is installed in a custom location:

   ```bash
   export BRAINFLOW_LIB_PATH="/path/to/directory/containing_libBoardController.so"
   ```

5. If `libBoardController.so` is **absent** from `brainflow/lib/`, reinstall: `pip install --user --upgrade --force-reinstall brainflow`. On uncommon ARM images you may need [BrainFlow build from source](https://brainflow.readthedocs.io/en/stable/BuildBrainFlow.html).

6. **Workaround without hardware:** `ros2 launch cyton_emg_ros emg_and_gesture.launch.py simulate:=true` (no BrainFlow board session; gestures stay idle on `[0,0,0,0]` unless you use `demo_gesture.launch.py`).

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

## Run the full EMG → gesture → robot-pipeline stub (main Pi command)

Launches **three** nodes: **`cyton_emg_publisher`**, **`gesture_interpreter_node`**, **`motion_command_bridge`** (consumes `/robot_motion_command` and logs each new command — replace with your driver).

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch cyton_emg_ros emg_and_gesture.launch.py
```

Optional launch overrides:

```bash
ros2 launch cyton_emg_ros emg_and_gesture.launch.py serial_port:=/dev/ttyUSB0
ros2 launch cyton_emg_ros emg_and_gesture.launch.py simulate:=true
ros2 launch cyton_emg_ros emg_and_gesture.launch.py deadman_source:=always_on
```

With default **`deadman_source:=topic`**, allow motion in another terminal:

```bash
ros2 topic pub /deadman std_msgs/msg/Bool "{data: true}" --rate 10
```

Watch the **bridge** (robot side stub) in the launch terminal: lines like **`[robot_pipeline] New motion command: "HOME"`** mean a deadman-safe string reached the consumption node (same place you will call into Kortex later).

### Layer 2 demo (no Cyton, no BrainFlow)

One launch runs **`demo_emg_pattern`** with **`cycle_gestures:=true`** (zeros between holds, then each pattern in the gesture map order), plus **`gesture_interpreter_node`** with **`deadman_source:=always_on`**, plus **`motion_command_bridge`**. You should see **`HOME`**, **`MOVE_FORWARD`**, **`REACH_UP`**, … rotate on **`/robot_commands`** / **`/robot_motion_command`** — still **no hardware motion** until you add a robot driver.

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch cyton_emg_ros demo_gesture.launch.py
```

In another terminal:

```bash
ros2 topic echo /robot_commands
ros2 topic echo /robot_motion_command
```

Do **not** run **`demo_gesture.launch.py`** at the same time as **`cyton_emg_publisher`** on **`/emg_commands`** (two publishers on one topic).

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

**`motion_command_bridge`** (same package): subscribes to `/robot_motion_command`, logs each **new** non-empty command; extend this node (or run your own subscriber) to send trajectories to the arm. Run it via **`emg_and_gesture.launch.py`** or **`demo_gesture.launch.py`**, or: `ros2 run gesture_interpreter_ros motion_command_bridge`.

### Gesture node parameters

- `deadman_source`: `topic` (default) | `keyboard` (space via optional `pynput`) | `always_on` (testing)
- `window_s`, `min_activation_count`, `cooldown_s`, `emit_unknown` — passed to `GestureInterpreter`

### Cyton publisher parameters

- `simulate`, `serial_port`, `use_daisy`, `exg_indices`, `threshold_microvolts`, `envelope_samples`, `publish_rate_hz`, `emg_topic`, `log_publish_hz` (default **1** log/s of what was published; set **0** to turn off)
- `recover_with_simulate_on_brainflow_failure` (default **true**): if `simulate:=false` but BrainFlow or the board fails to start, keep the node alive and publish **`[0,0,0,0]`** with an error log; set **false** to exit (strict / CI).

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

1. Either **extend `motion_command_bridge`** or run a separate node that subscribes to **`/robot_motion_command`** (`std_msgs/String`) — or **`/robot_commands`** only if you accept motion without deadman.
2. Map command strings (`HOME`, `MOVE_FORWARD`, …) to **MoveIt / kortex_driver** actions or joint trajectories.
3. Run **Gazebo / RViz** from the official `ros2_kortex` bringup on a capable machine.

See [Kinova ros2_kortex](https://github.com/Kinovarobotics/ros2_kortex).

## Windows development

ROS 2 is not typically built on Windows in this layout; edit here, then build and run on Ubuntu 24.04 + Jazzy (Pi or lab PC).
