"""
Layer-2 demo: demo_emg_pattern (cycles all mapped gestures) + gesture + motion_command_bridge.

Publishes rotating 4-bit patterns (zeros between each) so you see HOME, MOVE_FORWARD, …
on /robot_commands — not real muscle data; no arm moves until lab Kortex/MoveIt consumes
/robot_motion_command. deadman always_on so motion topic matches commands.

Terminal B:
  ros2 topic echo /robot_commands
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
                        "cycle_gestures": True,
                        "dwell_seconds": 1.8,
                        "gap_seconds": 0.4,
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
