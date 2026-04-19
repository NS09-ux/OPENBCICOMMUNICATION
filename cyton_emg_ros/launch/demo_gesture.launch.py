"""
Layer-2 demo: fake sustained EMG pattern + gesture_interpreter_node + motion_command_bridge.

Publishes [1,1,1,1] on /emg_commands at 20 Hz and runs the gesture node with deadman
always_on so /robot_commands and /robot_motion_command both show HOME (after window fills).
The bridge logs [robot_pipeline] when a new motion command arrives (same seam as real robot).

Terminal B:
  ros2 topic echo /robot_commands
  ros2 topic echo /robot_motion_command
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="cyton_emg_ros",
                executable="demo_emg_pattern",
                name="demo_emg_pattern",
                output="screen",
                parameters=[
                    {
                        "emg_topic": "/emg_commands",
                        "publish_rate_hz": 20.0,
                        "pattern": [1, 1, 1, 1],
                    }
                ],
            ),
            Node(
                package="gesture_interpreter_ros",
                executable="gesture_interpreter_node",
                name="emg_gesture_interpreter",
                output="screen",
                parameters=[
                    {
                        "deadman_source": "always_on",
                        "emg_topic": "/emg_commands",
                    }
                ],
            ),
            Node(
                package="gesture_interpreter_ros",
                executable="motion_command_bridge",
                name="motion_command_bridge",
                output="screen",
                parameters=[{"motion_command_topic": "/robot_motion_command"}],
            ),
        ]
    )
