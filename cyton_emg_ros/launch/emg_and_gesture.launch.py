"""Cyton → /emg_commands → gesture → /robot_motion_command → motion_command_bridge (stub).

Tune serial_port / simulate on the Pi. Hold /deadman (Bool true) unless deadman_source is always_on.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "simulate",
                default_value="false",
                description="If true, publish zeros (no Cyton / BrainFlow hardware).",
            ),
            DeclareLaunchArgument(
                "serial_port",
                default_value="/dev/ttyACM0",
                description="Cyton serial device on the Pi.",
            ),
            DeclareLaunchArgument(
                "deadman_source",
                default_value="topic",
                description="topic | always_on | keyboard — passed to gesture_interpreter_node.",
            ),
            Node(
                package="cyton_emg_ros",
                executable="cyton_emg_publisher",
                name="cyton_emg_publisher",
                output="screen",
                parameters=[
                    {
                        "simulate": ParameterValue(
                            LaunchConfiguration("simulate"), value_type=bool
                        ),
                        "serial_port": ParameterValue(
                            LaunchConfiguration("serial_port"), value_type=str
                        ),
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
                        "deadman_source": ParameterValue(
                            LaunchConfiguration("deadman_source"), value_type=str
                        ),
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
