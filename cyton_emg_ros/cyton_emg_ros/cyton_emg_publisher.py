"""
ROS 2 node: stream OpenBCI Cyton (+ optional Daisy) via BrainFlow, threshold 4 EXG
channels to binary activations, publish std_msgs/Int32MultiArray on /emg_commands.

Order: [bicep, forearm, shoulder, thumb] → matches gesture_interpreter_ros.

Install on the Pi: pip install brainflow  (not shipped via apt rosdep)
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32MultiArray

# Optional: load defaults from repo config when running from workspace (…/OPENBCICOMMUNICATION).
_here = Path(__file__).resolve()
_REPO_ROOT = _here.parents[2] if len(_here.parents) > 2 else _here.parent
if (_REPO_ROOT / "config" / "pipeline_config.py").is_file() and str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _load_pipeline_defaults() -> tuple:
    try:
        from config.pipeline_config import (
            CYTON_DAISY,
            CYTON_SERIAL_PORT,
            EMG_COMMANDS_ENVELOPE_SAMPLES,
            EMG_COMMANDS_EXG_INDICES,
            EMG_COMMANDS_THRESHOLD_UV,
        )

        thr = EMG_COMMANDS_THRESHOLD_UV
        if isinstance(thr, (int, float)):
            thr_list = [float(thr)] * 4
        else:
            thr_list = [float(x) for x in thr]
            while len(thr_list) < 4:
                thr_list.append(thr_list[-1])
            thr_list = thr_list[:4]
        return (
            str(CYTON_SERIAL_PORT),
            bool(CYTON_DAISY),
            list(EMG_COMMANDS_EXG_INDICES),
            thr_list,
            int(EMG_COMMANDS_ENVELOPE_SAMPLES),
        )
    except Exception:
        return ("/dev/ttyACM0", True, [0, 1, 2, 3], [75.0, 75.0, 75.0, 75.0], 32)


class CytonEmgPublisher(Node):
    """Publishes 4× binary EMG samples to /emg_commands."""

    def __init__(self) -> None:
        super().__init__("cyton_emg_publisher")

        d_port, d_daisy, d_idx, d_thr, d_env = _load_pipeline_defaults()

        self.declare_parameter("simulate", False)
        self.declare_parameter("serial_port", d_port)
        self.declare_parameter("use_daisy", d_daisy)
        self.declare_parameter("exg_indices", d_idx)
        self.declare_parameter("threshold_microvolts", d_thr)
        self.declare_parameter("envelope_samples", d_env)
        self.declare_parameter("publish_rate_hz", 50.0)
        self.declare_parameter("emg_topic", "/emg_commands")

        self._simulate = bool(self.get_parameter("simulate").value)
        self._pub_topic = str(self.get_parameter("emg_topic").value)
        self._envelope = max(4, int(self.get_parameter("envelope_samples").value))
        self._exg_indices: List[int] = list(
            self.get_parameter("exg_indices").get_parameter_value().integer_array_value
        )
        thr_val = self.get_parameter("threshold_microvolts").get_parameter_value()
        if thr_val.double_array_value:
            self._thresholds = [float(x) for x in thr_val.double_array_value]
        else:
            self._thresholds = [float(thr_val.double_value)] * 4
        while len(self._thresholds) < 4:
            self._thresholds.append(self._thresholds[-1])
        self._thresholds = self._thresholds[:4]

        if len(self._exg_indices) != 4:
            self.get_logger().error(
                f"exg_indices must have length 4 [bicep, forearm, shoulder, thumb]; got {self._exg_indices!r}"
            )
            raise ValueError("exg_indices")

        self._board = None
        self._exg_rows: Optional[List[int]] = None

        self._pub = self.create_publisher(Int32MultiArray, self._pub_topic, 10)

        if self._simulate:
            self.get_logger().warn(
                "simulate=true: publishing zeros on /emg_commands (no Cyton). "
                "Use for testing without hardware."
            )
        else:
            self._init_brainflow_board()

        rate = float(self.get_parameter("publish_rate_hz").value)
        period = 1.0 / rate if rate > 0.0 else 0.02
        self.create_timer(period, self._on_timer)

        self.get_logger().info(
            f'Publishing Int32[4] to "{self._pub_topic}" at ~{rate:.1f} Hz '
            f"(exg_indices={self._exg_indices}, simulate={self._simulate})"
        )

    def _init_brainflow_board(self) -> None:
        try:
            from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
        except ImportError as e:
            self.get_logger().fatal(
                "brainflow is not installed. On the Pi run: pip install brainflow "
                f"(or use simulate:=true). Import error: {e}"
            )
            raise

        port = str(self.get_parameter("serial_port").value).strip()
        if not port:
            port = os.environ.get("CYTON_SERIAL_PORT", "").strip()
        if not port:
            self.get_logger().fatal(
                "serial_port is empty. Set ROS param serial_port or env CYTON_SERIAL_PORT "
                "(e.g. /dev/ttyACM0 on Pi, COM3 on Windows)."
            )
            raise ValueError("serial_port")

        use_daisy = bool(self.get_parameter("use_daisy").value)
        board_id = BoardIds.CYTON_DAISY_BOARD if use_daisy else BoardIds.CYTON_BOARD
        exg_channels = BoardShim.get_exg_channels(board_id)

        rows = []
        for i in self._exg_indices:
            if i < 0 or i >= len(exg_channels):
                self.get_logger().fatal(
                    f"exg_index {i} out of range for board (0..{len(exg_channels) - 1})"
                )
                raise ValueError("exg_indices")
            rows.append(exg_channels[i])
        self._exg_rows = rows

        params = BrainFlowInputParams()
        params.serial_port = port
        board = BoardShim(board_id, params)
        try:
            board.prepare_session()
            board.start_stream()
        except Exception as e:
            try:
                board.release_session()
            except Exception:
                pass
            self.get_logger().fatal(f"Failed to start Cyton stream on {port!r}: {e}")
            raise

        self._board = board
        fs = BoardShim.get_sampling_rate(board_id)
        self.get_logger().info(
            f"Cyton streaming: port={port!r} daisy={use_daisy} fs={fs} Hz rows={rows}"
        )

    def _on_timer(self) -> None:
        if self._simulate:
            msg = Int32MultiArray()
            msg.data = [0, 0, 0, 0]
            self._pub.publish(msg)
            return

        assert self._board is not None and self._exg_rows is not None
        data = self._board.get_board_data()
        if data is None or data.size == 0:
            return
        n_cols = data.shape[1]
        if n_cols < 1:
            return
        w = min(self._envelope, n_cols)
        seg = data[np.ix_(self._exg_rows, range(n_cols - w, n_cols))]
        env = np.mean(np.abs(seg), axis=1)
        out = [1 if env[i] >= self._thresholds[i] else 0 for i in range(4)]
        msg = Int32MultiArray()
        msg.data = [int(x) for x in out]
        self._pub.publish(msg)

    def shutdown_board(self) -> None:
        if self._board is None:
            return
        try:
            self._board.stop_stream()
            self._board.release_session()
        except Exception as e:
            self.get_logger().warn(f"Board shutdown: {e}")
        self._board = None


def main(args: Optional[List[str]] = None) -> None:
    rclpy.init(args=args)
    node: Optional[CytonEmgPublisher] = None
    try:
        node = CytonEmgPublisher()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"cyton_emg_publisher: {e}", file=sys.stderr)
        raise SystemExit(1) from e
    finally:
        if node is not None:
            node.shutdown_board()
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
