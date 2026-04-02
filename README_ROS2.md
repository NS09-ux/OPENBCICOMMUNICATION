# ROS 2 Jazzy — EMG gesture interpreter

This workspace contains two **colcon** packages:

| Package | Role |
|---------|------|
| `gesture_interpreter` | Pure Python: 4× binary EMG → combined pattern → command string |
| `gesture_interpreter_ros` | `rclpy` node: `/emg_commands` → `/robot_commands` + deadman-gated `/robot_motion_command` |

## Build (Ubuntu 24.04 / Raspberry Pi / lab PC with Jazzy)

```bash
cd /path/to/OPENBCICOMMUNICATION
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install --packages-select gesture_interpreter gesture_interpreter_ros
source install/setup.bash
```

## Run the node

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

### Parameters

- `deadman_source`: `topic` (default) | `keyboard` (space via optional `pynput`) | `always_on` (testing)
- `window_s`, `min_activation_count`, `cooldown_s`, `emit_unknown` — passed to `GestureInterpreter`

### Quick test without EMG hardware

Terminal A — interpreter with deadman always on:

```bash
ros2 run gesture_interpreter_ros gesture_interpreter_node --ros-args -p deadman_source:=always_on
```

Terminal B — fake EMG (HOME pattern: four ones, sent as repeated samples):

```bash
ros2 topic pub /emg_commands std_msgs/msg/Int32MultiArray "{data: [1,1,1,1]}"
```

Watch:

```bash
ros2 topic echo /robot_commands
ros2 topic echo /robot_motion_command
```

### Deadman via topic (e.g. SSH on Pi)

Terminal A: run node with defaults (`deadman_source:=topic`).

Terminal B: hold deadman true:

```bash
ros2 topic pub /deadman std_msgs/msg/Bool "{data: true}" --rate 10
```

## Kinova Gen3 / `ros2_kortex`

This repo **does not** install or launch Kortex. Your lab stack should:

1. Subscribe to **`/robot_motion_command`** (`std_msgs/String`) — or **`/robot_commands`** if you ignore deadman at your own risk.
2. Map command strings (`HOME`, `MOVE_FORWARD`, …) to **MoveIt / kortex_driver** actions or joint trajectories as you already do for direct EMG.
3. Run **Gazebo / RViz** from the official `ros2_kortex` bringup on a capable machine.

See [Kinova ros2_kortex](https://github.com/Kinovarobotics/ros2_kortex) for simulation bringup.

## Windows development

ROS 2 is not typically built on Windows in this layout; edit here, then build and run on Ubuntu 24.04 + Jazzy (Pi or lab PC).
