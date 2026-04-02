"""
Robot driver: turn BCI commands (FRONT/LEFT/etc.) into robot motion.

Use one of:
- PrintDriver: no robot, just prints (for testing on Pi).
- ROSDriver: publishes geometry_msgs/Twist to cmd_vel (ROS 1 rospy — Husky-style).
- For ROS 2 Jazzy + Kinova gesture strings, see `robot_driver_ros2.py` and
  `gesture_interpreter_ros` (topics /robot_commands, /robot_motion_command).
- (Later) SerialDriver or HTTPDriver for robots with serial/HTTP API.
"""

from __future__ import annotations

import time
from typing import Optional


class RobotDriver:
    """Base: one method to set command, one to stop."""

    def set_command(self, command: str) -> None:
        """Apply command: FRONT, BACK, LEFT, RIGHT, STARTSTOP, NONE."""
        raise NotImplementedError

    def stop(self) -> None:
        """Stop the robot (e.g. on timeout or Ctrl+C)."""
        raise NotImplementedError


class PrintDriver(RobotDriver):
    """No real robot; print commands. Use on Pi to test without a robot."""

    def set_command(self, command: str) -> None:
        print(f"[robot_driver] command={command}")

    def stop(self) -> None:
        print("[robot_driver] stop")


class ROSDriver(RobotDriver):
    """
    Publish Twist to cmd_vel. Use when the robot runs ROS (e.g. Husky).
    On the Pi: install ROS, source setup.bash, run this script.
    """

    def __init__(
        self,
        topic: str = "cmd_vel",
        linear_speed: float = 0.3,
        angular_speed: float = 0.4,
    ):
        self._topic = topic
        self._linear = linear_speed
        self._angular = angular_speed
        self._pub = None
        self._last_cmd_time = 0.0
        self._timeout_s = 2.0  # stop if no command for this long

    def _ensure_pub(self):
        if self._pub is not None:
            return
        try:
            import rospy
            from geometry_msgs.msg import Twist
            rospy.init_node("bci_robot_driver", anonymous=True)
            self._pub = rospy.Publisher(self._topic, Twist, queue_size=1)
            self._Twist = Twist
        except ImportError:
            raise ImportError("ROS (rospy, geometry_msgs) not available. Install and source ROS.")

    def set_command(self, command: str) -> None:
        self._ensure_pub()
        self._last_cmd_time = time.time()
        t = self._Twist()
        cmd = (command or "").upper()
        if cmd == "FRONT":
            t.linear.x = self._linear
            t.angular.z = 0.0
        elif cmd == "BACK":
            t.linear.x = -self._linear * 0.7
            t.angular.z = 0.0
        elif cmd == "LEFT":
            t.linear.x = 0.0
            t.angular.z = self._angular
        elif cmd == "RIGHT":
            t.linear.x = 0.0
            t.angular.z = -self._angular
        else:
            t.linear.x = 0.0
            t.angular.z = 0.0
        self._pub.publish(t)

    def stop(self) -> None:
        self._ensure_pub()
        t = self._Twist()
        t.linear.x = 0.0
        t.angular.z = 0.0
        self._pub.publish(t)


def get_driver(kind: str = "print", **kwargs) -> RobotDriver:
    """kind: 'print' | 'ros'. Extra kwargs passed to the driver."""
    if kind == "print":
        return PrintDriver()
    if kind == "ros":
        return ROSDriver(**kwargs)
    raise ValueError(f"Unknown driver kind: {kind}")
