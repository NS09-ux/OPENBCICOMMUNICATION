"""Cyton /emg_commands publisher + gesture interpreter (tune serial_port on the Pi)."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="cyton_emg_ros",
                executable="cyton_emg_publisher",
                name="cyton_emg_publisher",
                output="screen",
                parameters=[
                    {
                        "simulate": False,
                        "serial_port": "/dev/ttyACM0",
                        "use_daisy": True,
                        "exg_indices": [0, 1, 2, 3],
                        "threshold_microvolts": [75.0, 75.0, 75.0, 75.0],
                        "envelope_samples": 32,
                        "publish_rate_hz": 50.0,
                        "emg_topic": "/emg_commands",
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
                        "deadman_source": "topic",
                        "emg_topic": "/emg_commands",
                    }
                ],
            ),
        ]
    )
