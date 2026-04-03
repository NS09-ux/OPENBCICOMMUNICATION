# Project layout

```
OPENBCICOMMUNICATION/
├── config/                    # Shared settings
│   ├── pipeline_config.py     # Channels, COM port, filters, windows
│   └── ssvep_config.py        # Flicker frequencies → commands
├── gesture_interpreter/       # EMG → gesture (ament_python + pure Python)
│   ├── package.xml            # colcon ROS 2 package (core library)
│   ├── interpreter.py         # interpret_gesture(features)
│   ├── gesture_config.py      # GESTURE_NAMES
│   ├── sim/                   # Standalone timing / threshold simulation
│   │   └── gesture_interpreter_sim.py
│   └── README.md
├── gesture_interpreter_ros/   # ROS 2 Jazzy: /emg_commands → /robot_commands
│   ├── launch/
│   └── gesture_interpreter_ros/
├── cyton_emg_ros/             # ROS 2: Cyton (BrainFlow) → /emg_commands
│   ├── launch/
│   └── cyton_emg_ros/
├── README_ROS2.md             # colcon build, topics, deadman, Kinova notes
├── robot_driver_ros2.py       # Optional rclpy print stub for gesture topics
├── ssvep_interpreter/         # EEG window → SSVEP command (FRONT/LEFT/…)
│   └── interpreter.py
├── docs/                      # Guides (Pi, ROS, next steps, …)
├── openbci_ml_pipeline.py     # Offline CSV → features
├── stream_openbci.py          # Live BrainFlow → features / SSVEP
├── bci_to_robot.py            # Pi: stream → robot driver
├── robot_driver.py            # Print or ROS 1 cmd_vel (Husky-style)
├── requirements.txt
└── README.md
```

**Run from the project root** (so `config`, `gesture_interpreter`, and `ssvep_interpreter` import correctly):

```bash
python stream_openbci.py
python -m gesture_interpreter.sim.gesture_interpreter_sim
```
