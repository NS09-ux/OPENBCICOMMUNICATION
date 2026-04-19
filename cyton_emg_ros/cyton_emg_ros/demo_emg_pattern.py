"""
Publish a fixed 4× binary pattern on /emg_commands for testing gesture_interpreter_node
without a Cyton (e.g. sustained [1,1,1,1] → HOME after window fills).

Do not run alongside cyton_emg_publisher on the same topic.
"""

from __future__ import annotations

from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray


class DemoEmgPattern(Node):
    def __init__(self) -> None:
        super().__init__("demo_emg_pattern")
        self.declare_parameter("emg_topic", "/emg_commands")
        self.declare_parameter("publish_rate_hz", 20.0)
        self.declare_parameter("pattern", [1, 1, 1, 1])

        topic = str(self.get_parameter("emg_topic").value)
        rate = float(self.get_parameter("publish_rate_hz").value)
        raw = self.get_parameter("pattern").value
        if isinstance(raw, (list, tuple)) and len(raw) == 4:
            pat = [int(x) for x in raw]
        else:
            pat = [1, 1, 1, 1]
        if len(pat) != 4:
            self.get_logger().error(f"pattern must have 4 elements; got {pat!r}")
            raise ValueError("pattern")
        self._pat = [1 if int(x) != 0 else 0 for x in pat]

        self._pub = self.create_publisher(Int32MultiArray, topic, 10)
        period = 1.0 / rate if rate > 0.0 else 0.05
        self.create_timer(period, self._tick)
        self.get_logger().info(
            f'Publishing pattern={self._pat} to "{topic}" at ~{1.0 / period:.1f} Hz (for gesture demo)'
        )

    def _tick(self) -> None:
        msg = Int32MultiArray()
        msg.data = list(self._pat)
        self._pub.publish(msg)


def main(args: Optional[list] = None) -> None:
    rclpy.init(args=args)
    node = DemoEmgPattern()
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
