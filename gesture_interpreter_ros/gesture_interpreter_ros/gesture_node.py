"""
ROS 2 Jazzy node: subscribe to /emg_commands (std_msgs/Int32MultiArray, length 4),
run GestureInterpreter, publish std_msgs/String on /robot_commands (always) and
/robot_motion_command (only when deadman is active).

Deadman sources (parameter deadman_source):
  topic      — use /deadman (std_msgs/Bool), e.g. from teleop or `ros2 topic pub`
  keyboard   — space key via pynput (needs local display; optional dependency)
  always_on  — motion enabled always (simulation / testing)
"""

from __future__ import annotations

import threading
import time
from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Int32MultiArray, String

from gesture_interpreter.sim.gesture_interpreter_sim import GestureInterpreter


class GestureInterpreterNode(Node):
    def __init__(self) -> None:
        super().__init__("emg_gesture_interpreter")

        self.declare_parameter("window_s", 0.2)
        self.declare_parameter("min_activation_count", 3)
        self.declare_parameter("cooldown_s", 0.35)
        self.declare_parameter("emit_unknown", False)
        self.declare_parameter("emg_topic", "/emg_commands")
        self.declare_parameter("robot_commands_topic", "/robot_commands")
        self.declare_parameter("robot_motion_command_topic", "/robot_motion_command")
        self.declare_parameter("deadman_active_topic", "/deadman_active")
        self.declare_parameter("deadman_source", "topic")
        self.declare_parameter("deadman_topic", "/deadman")
        self.declare_parameter("deadman_publish_hz", 10.0)

        self._lock = threading.Lock()
        self._deadman: bool = False
        self._deadman_sub = None
        self._kb_listener = None

        w = float(self.get_parameter("window_s").value)
        mac = int(self.get_parameter("min_activation_count").value)
        cd = float(self.get_parameter("cooldown_s").value)
        eu = bool(self.get_parameter("emit_unknown").value)

        self._interpreter = GestureInterpreter(
            window_s=w,
            min_activation_count=mac,
            cooldown_s=cd,
            emit_unknown=eu,
        )

        emg_topic = str(self.get_parameter("emg_topic").value)
        cmd_topic = str(self.get_parameter("robot_commands_topic").value)
        motion_topic = str(self.get_parameter("robot_motion_command_topic").value)
        deadman_pub_topic = str(self.get_parameter("deadman_active_topic").value)

        self._pub_cmd = self.create_publisher(String, cmd_topic, 10)
        self._pub_motion = self.create_publisher(String, motion_topic, 10)
        self._pub_deadman = self.create_publisher(Bool, deadman_pub_topic, 10)

        self.create_subscription(Int32MultiArray, emg_topic, self._on_emg, 10)

        source = str(self.get_parameter("deadman_source").value).strip().lower()
        if source == "always_on":
            with self._lock:
                self._deadman = True
            self.get_logger().info("deadman_source=always_on: motion commands enabled")
        elif source == "keyboard":
            self._start_keyboard_deadman()
        elif source == "topic":
            dt = str(self.get_parameter("deadman_topic").value)
            self._deadman_sub = self.create_subscription(Bool, dt, self._on_deadman_msg, 10)
            self.get_logger().info('deadman_source=topic: subscribe to "%s" (Bool)', dt)
        else:
            self.get_logger().warn(
                "Unknown deadman_source=%r; using topic", source
            )
            dt = str(self.get_parameter("deadman_topic").value)
            self._deadman_sub = self.create_subscription(Bool, dt, self._on_deadman_msg, 10)

        hz = float(self.get_parameter("deadman_publish_hz").value)
        period = 1.0 / hz if hz > 0.0 else 0.1
        self.create_timer(period, self._publish_deadman_state)

        self.get_logger().info(
            'Subscribing emg="%s" publishing commands="%s" motion="%s" deadman_state="%s"',
            emg_topic,
            cmd_topic,
            motion_topic,
            deadman_pub_topic,
        )

    def _on_deadman_msg(self, msg: Bool) -> None:
        with self._lock:
            self._deadman = bool(msg.data)

    def _start_keyboard_deadman(self) -> None:
        try:
            from pynput import keyboard
        except ImportError:
            self.get_logger().error(
                "deadman_source=keyboard but pynput is not installed. "
                "Install with: pip install pynput  OR  use deadman_source:=topic"
            )
            return

        def on_press(key: object) -> None:
            try:
                if key == keyboard.Key.space:
                    with self._lock:
                        self._deadman = True
            except Exception:
                pass

        def on_release(key: object) -> None:
            try:
                if key == keyboard.Key.space:
                    with self._lock:
                        self._deadman = False
            except Exception:
                pass

        self._kb_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._kb_listener.daemon = True
        self._kb_listener.start()
        self.get_logger().info("deadman_source=keyboard: hold SPACE to enable motion")

    def _deadman_active(self) -> bool:
        with self._lock:
            return self._deadman

    def _publish_deadman_state(self) -> None:
        msg = Bool()
        msg.data = self._deadman_active()
        self._pub_deadman.publish(msg)

    def _on_emg(self, msg: Int32MultiArray) -> None:
        data = list(msg.data)
        if len(data) != 4:
            self.get_logger().warn(
                "Expected 4 EMG channels [bicep, forearm, shoulder, thumb]; got len=%d",
                len(data),
            )
            return

        t = time.monotonic()
        self._interpreter.add_input(data, t_mono=t)
        cmd = self._interpreter.process_gesture(t_mono=t)
        if cmd is None:
            return

        s = String()
        s.data = cmd
        self._pub_cmd.publish(s)
        self.get_logger().info('Gesture detected: command="%s" (published to robot_commands)', cmd)

        motion = String()
        motion.data = cmd if self._deadman_active() else ""
        self._pub_motion.publish(motion)
        if self._deadman_active():
            self.get_logger().info(
                'Deadman active: motion command="%s" -> %s',
                cmd,
                str(self.get_parameter("robot_motion_command_topic").value),
            )
        else:
            self.get_logger().info(
                'Deadman inactive: motion command suppressed (command="%s" still on robot_commands)',
                cmd,
            )


def main(args: Optional[list] = None) -> None:
    rclpy.init(args=args)
    node: Optional[GestureInterpreterNode] = None
    try:
        node = GestureInterpreterNode()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            if node._kb_listener is not None:
                node._kb_listener.stop()
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
