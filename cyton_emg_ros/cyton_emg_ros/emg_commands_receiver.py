"""
ROS 2 subscriber: print / log std_msgs/Int32MultiArray from /emg_commands (or any topic).

Run in a second terminal while cyton_emg_publisher (or another publisher) runs:

  ros2 run cyton_emg_ros emg_commands_receiver
  ros2 run cyton_emg_ros emg_commands_receiver --ros-args -p topic:=/emg_commands
"""

from __future__ import annotations

import time
from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray


class EmgCommandsReceiver(Node):
    def __init__(self) -> None:
        super().__init__("emg_commands_receiver")
        self.declare_parameter("topic", "/emg_commands")
        self.declare_parameter("log_hz", 5.0)

        topic = str(self.get_parameter("topic").value)
        self._min_dt = 1.0 / max(float(self.get_parameter("log_hz").value), 0.1)
        self._last_log = 0.0

        self.create_subscription(Int32MultiArray, topic, self._cb, 10)
        self.get_logger().info(f'Subscribed to "{topic}" (Int32MultiArray); logging up to ~{1.0 / self._min_dt:.1f} Hz')

    def _cb(self, msg: Int32MultiArray) -> None:
        now = time.monotonic()
        if now - self._last_log < self._min_dt:
            return
        self._last_log = now
        data = list(msg.data)
        self.get_logger().info(f"received data={data} len={len(data)}")


def main(args: Optional[list] = None) -> None:
    rclpy.init(args=args)
    node = EmgCommandsReceiver()
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
