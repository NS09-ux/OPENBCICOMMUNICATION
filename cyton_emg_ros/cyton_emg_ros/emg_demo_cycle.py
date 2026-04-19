"""
Rotating 4× binary EMG patterns for demos (aligned with gesture_interpreter DEFAULT_GESTURE_MAP).
Used by demo_emg_pattern and cyton_emg_publisher simulate / recovery modes.
"""

from __future__ import annotations

import time
from typing import Callable, List, Optional, Tuple

# Excludes all-zero IDLE (interpreter does not emit on (0,0,0,0)).
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


class EmgDemoCycle:
    """Gap (zeros) → hold pattern → gap → next pattern, forever."""

    def __init__(
        self,
        dwell_seconds: float,
        gap_seconds: float,
        log: Optional[Callable[[str], None]] = None,
    ) -> None:
        self._dwell = max(0.5, float(dwell_seconds))
        self._gap_sec = max(0.15, float(gap_seconds))
        self._log = log
        self._seq_i = 0
        self._gap = True
        self._t_phase = time.monotonic()

    def next_vector(self) -> List[int]:
        now = time.monotonic()
        elapsed = now - self._t_phase
        if self._gap:
            out: List[int] = [0, 0, 0, 0]
            if elapsed >= self._gap_sec:
                self._gap = False
                self._t_phase = now
                label = _CYCLE_LABELS[self._seq_i]
                pat = _norm4(_CYCLE_PATTERNS[self._seq_i])
                if self._log:
                    self._log(f"demo cycle: holding {pat} → expect ~{label} after gesture window")
            return out

        out = _norm4(_CYCLE_PATTERNS[self._seq_i])
        if elapsed >= self._dwell:
            if self._log:
                self._log("demo cycle: gap (zeros) to clear sliding window before next gesture")
            self._gap = True
            self._t_phase = now
            self._seq_i = (self._seq_i + 1) % len(_CYCLE_PATTERNS)
            return [0, 0, 0, 0]
        return out
