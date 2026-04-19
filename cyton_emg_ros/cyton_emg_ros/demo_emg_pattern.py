"""
Publish 4× binary vectors on /emg_commands for testing gesture_interpreter_node without Cyton.

Modes:
  Fixed pattern (default): repeat ``pattern`` at publish_rate_hz (e.g. [1,1,1,1] → HOME).
  cycle_gestures:=true: gap of zeros, then each map entry in order (aligned with
  gesture_interpreter DEFAULT_GESTURE_MAP) so you see HOME, MOVE_FORWARD, … in rotation.

Do not run alongside cyton_emg_publisher on the same topic.
"""

from __future__ import annotations

import time
from typing import List, Optional, Tuple

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray

# Order aligned with gesture_interpreter.sim.gesture_interpreter_sim.DEFAULT_GESTURE_MAP
# (excluding all-zero IDLE, which never emits from the interpreter).
_CYCLE_PATTERNS: Tuple[Tuple[int, int, int, int], ...] = (
    (1, 1, 1, 1),
    (1, 1, 0, 0),
    (1, 0, 1, 0),
    (0, 1, 1, 0),
    (0, 0, 1, 1),
    (1, 0, 0, 1),
    (0, 1, 0, 1),
    (1, 1, 1, 0),
)
_CYCLE_LABELS: Tuple[str, ...] = (
    "HOME",
    "MOVE_FORWARD",
    "REACH_UP",
    "ELBOW_TUCK",
    "SHOULDER_THUMB_COMBO",
    "GRIPPER_BICEP",
    "GRIPPER_FOREARM",
    "READY_STANCE",
)


def _norm4(t: Tuple[int, int, int, int]) -> List[int]:
    return [1 if int(x) != 0 else 0 for x in t]


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
        self._dwell = max(0.5, float(self.get_parameter("dwell_seconds").value))
        self._gap_sec = max(0.15, float(self.get_parameter("gap_seconds").value))

        raw = self.get_parameter("pattern").value
        if isinstance(raw, (list, tuple)) and len(raw) == 4:
            pat = [int(x) for x in raw]
        else:
            pat = [1, 1, 1, 1]
        self._pat = [1 if int(x) != 0 else 0 for x in pat]

        self._pub = self.create_publisher(Int32MultiArray, self._topic, 10)
        period = 1.0 / rate if rate > 0.0 else 0.05
        self.create_timer(period, self._tick)

        if self._cycle:
            self._seq_i = 0
            self._gap = True
            self._t_phase = time.monotonic()
            n = len(_CYCLE_PATTERNS)
            self.get_logger().info(
                f'Cycling {n} gesture patterns on "{self._topic}" at ~{1.0 / period:.1f} Hz '
                f"(dwell={self._dwell}s gap={self._gap_sec}s). "
                "This is not EMG from your body — only proves ROS string mapping."
            )
        else:
            self.get_logger().info(
                f'Publishing pattern={self._pat} to "{self._topic}" at ~{1.0 / period:.1f} Hz '
                "(set cycle_gestures:=true to rotate through all mapped commands)"
            )

    def _tick(self) -> None:
        if not self._cycle:
            out = self._pat
        else:
            now = time.monotonic()
            elapsed = now - self._t_phase
            if self._gap:
                out = [0, 0, 0, 0]
                if elapsed >= self._gap_sec:
                    self._gap = False
                    self._t_phase = now
                    label = _CYCLE_LABELS[self._seq_i]
                    pat = _norm4(_CYCLE_PATTERNS[self._seq_i])
                    self.get_logger().info(
                        f"demo cycle: holding {pat} → expect ~{label} after gesture window"
                    )
            else:
                out = _norm4(_CYCLE_PATTERNS[self._seq_i])
                if elapsed >= self._dwell:
                    self.get_logger().info(
                        "demo cycle: gap (zeros) to clear sliding window before next gesture"
                    )
                    self._gap = True
                    self._t_phase = now
                    self._seq_i = (self._seq_i + 1) % len(_CYCLE_PATTERNS)
                    out = [0, 0, 0, 0]

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
