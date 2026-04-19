"""
Consumption point for /robot_motion_command (deadman-gated strings).

Lab goal: Cyton EMG → gesture names → **this topic** → Kinova / MoveIt / ros2_kortex.
This node logs each *new* non-empty command so you see the pipeline complete on the Pi.
Replace or extend the callback with your driver (trajectory, gripper, etc.).
"""

from __future__ import annotations

from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import String


class MotionCommandBridge(Node):
    def __init__(self) -> None:
        super().__init__("motion_command_bridge")
        self.declare_parameter("motion_command_topic", "/robot_motion_command")
        topic = str(self.get_parameter("motion_command_topic").value)
        self._last_nonempty = ""
        self.create_subscription(String, topic, self._on_motion, 10)
        self.get_logger().info(
            f'Subscribed to "{topic}" — stub bridge; wire callback to robot driver.'
        )

    def _on_motion(self, msg: String) -> None:
        cmd = (msg.data or "").strip()
        if not cmd:
            if self._last_nonempty:
                self.get_logger().info("Motion command cleared (deadman off or empty).")
            self._last_nonempty = ""
            return
        if cmd == self._last_nonempty:
            return
        self._last_nonempty = cmd
        self.get_logger().info(
            f'[robot_pipeline] New motion command: "{cmd}" '
            "(stub — map to trajectories / ros2_kortex on the execution machine)."
        )


def main(args: Optional[list[str]] = None) -> None:
    rclpy.init(args=args)
    node = MotionCommandBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
