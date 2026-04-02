"""
ROS 2 (rclpy) helpers for gesture / command bridging — lab integration stubs.

The gesture node publishes:
  /robot_commands        — every detected gesture (logging / pipeline)
  /robot_motion_command — same string only while deadman is active (use for real arm motion)

Your Kinova stack should subscribe to /robot_motion_command (or compose with your own
deadman) and map strings to kortex actions / trajectories (ros2_kortex).

This module avoids importing rclpy at import time so scripts can run without ROS.
"""

from __future__ import annotations

from typing import Callable, Optional


def run_gesture_print_node(
    motion_topic: str = "/robot_motion_command",
    commands_topic: str = "/robot_commands",
) -> None:
    """
    Minimal subscriber node: logs String messages on motion + commands topics.
    Use for `ros2 run` testing next to gesture_interpreter_node.

    Blocks until Ctrl+C.
    """
    import rclpy
    from rclpy.node import Node
    from std_msgs.msg import String

    class _Print(Node):
        def __init__(self) -> None:
            super().__init__("gesture_print_stub")
            self.create_subscription(
                String, motion_topic, lambda m: self.get_logger().info(f"motion: {m.data!r}"), 10
            )
            self.create_subscription(
                String,
                commands_topic,
                lambda m: self.get_logger().info(f"command (always): {m.data!r}"),
                10,
            )
            self.get_logger().info(
                f"Listening on {motion_topic!r} and {commands_topic!r}"
            )

    rclpy.init()
    node = _Print()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


def make_motion_callback(on_command: Callable[[str], None]) -> Callable[[object], None]:
    """Build a std_msgs/String subscription callback."""

    def _cb(msg: object) -> None:
        data = getattr(msg, "data", "")
        if isinstance(data, str) and data:
            on_command(data)

    return _cb


if __name__ == "__main__":
    run_gesture_print_node()
