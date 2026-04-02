"""Launch the EMG gesture interpreter node (ROS 2 Jazzy).

Override parameters, e.g.:
  ros2 launch gesture_interpreter_ros gesture_interpreter.launch.py
  ros2 run gesture_interpreter_ros gesture_interpreter_node --ros-args -p deadman_source:=always_on
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="gesture_interpreter_ros",
                executable="gesture_interpreter_node",
                name="emg_gesture_interpreter",
                output="screen",
                parameters=[
                    {
                        "deadman_source": "topic",
                        "emg_topic": "/emg_commands",
                        "robot_commands_topic": "/robot_commands",
                        "robot_motion_command_topic": "/robot_motion_command",
                        "deadman_active_topic": "/deadman_active",
                        "deadman_topic": "/deadman",
                    }
                ],
            ),
        ]
    )
