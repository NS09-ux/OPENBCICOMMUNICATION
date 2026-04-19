"""
Publish 4× binary vectors on /emg_commands for testing gesture_interpreter_node without Cyton.

Modes:
  Fixed pattern (default): repeat ``pattern`` at publish_rate_hz (e.g. [1,1,1,1] → HOME).
  cycle_gestures:=true: rotate through map patterns (see emg_demo_cycle).

Do not run alongside cyton_emg_publisher on the same topic.
"""

from __future__ import annotations

from typing import List, Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray

from cyton_emg_ros.emg_demo_cycle import EmgDemoCycle


class DemoEmgPattern(Node):
    def __init__(self) -> None:
        super().__init__("demo_emg_pattern")
        self.declare_parameter("emg_topic", "/emg_commands")
        self.declare_parameter("publish_rate_hz", 20.0)
        self.declare_parameter("pattern", [1, 1, 1, 1])
        self.declare_parameter("cycle_gestures", False)
        self.declare_parameter("dwell_seconds", 1.8)
        self.declare_parameter("gap_seconds", 0.4)

        self._topic = str(self.get_parameter("emg_topic").value)
        rate = float(self.get_parameter("publish_rate_hz").value)
        self._cycle = bool(self.get_parameter("cycle_gestures").value)
        dwell = max(0.5, float(self.get_parameter("dwell_seconds").value))
        gap = max(0.15, float(self.get_parameter("gap_seconds").value))

        raw = self.get_parameter("pattern").value
        if isinstance(raw, (list, tuple)) and len(raw) == 4:
            pat = [int(x) for x in raw]
        else:
            pat = [1, 1, 1, 1]
        self._pat = [1 if int(x) != 0 else 0 for x in pat]

        self._demo_cycle: Optional[EmgDemoCycle] = None
        if self._cycle:
            self._demo_cycle = EmgDemoCycle(
                dwell,
                gap,
                log=lambda m: self.get_logger().info(m),
            )
            n = 8
            self.get_logger().info(
                f'Cycling {n} gesture patterns on "{self._topic}" at ~{1.0 / max(rate, 1e-6):.1f} Hz '
                f"(dwell={dwell}s gap={gap}s). "
                "This is not EMG from your body — only proves ROS string mapping."
            )
        else:
            self.get_logger().info(
                f'Publishing pattern={self._pat} to "{self._topic}" at ~{1.0 / max(rate, 1e-6):.1f} Hz '
                "(set cycle_gestures:=true to rotate through all mapped commands)"
            )

        self._pub = self.create_publisher(Int32MultiArray, self._topic, 10)
        period = 1.0 / rate if rate > 0.0 else 0.05
        self.create_timer(period, self._tick)

    def _tick(self) -> None:
        if self._demo_cycle is not None:
            out = self._demo_cycle.next_vector()
        else:
            out = self._pat
        msg = Int32MultiArray()
        msg.data = list(out)
        self._pub.publish(msg)


def main(args: Optional[list[str]] = None) -> None:
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
