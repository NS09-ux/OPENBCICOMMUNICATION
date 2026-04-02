#!/usr/bin/env python3
"""
EMG gesture interpreter: 4-channel binary vectors [bicep, forearm, shoulder, thumb]
over a time window, count activations per muscle, threshold to a combined pattern,
map pattern -> robot command. Window + cooldown + logging + test harness.

Input type: List[int] with values 0 or 1 per muscle (not scalar aggregation).
"""

from __future__ import annotations

import logging
import random
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Optional, Tuple

from gesture_interpreter import gesture_commands as GC

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gesture_interpreter_sim")

MUSCLE_NAMES = ("bicep", "forearm", "shoulder", "thumb")
NUM_MUSCLES = 4


# ---------------------------------------------------------------------------
# Binary noise for tests (replaces float Gaussian noise)
# ---------------------------------------------------------------------------


def generate_binary_pattern(
    n_samples: int,
    p_active: Tuple[float, float, float, float] = (0.2, 0.2, 0.2, 0.2),
    seed: Optional[int] = None,
) -> List[List[int]]:
    """
    Return n_samples independent random binary vectors [b,f,s,t], each bit 1 with prob p_active[i].
    """
    if seed is not None:
        random.seed(seed)
    out: List[List[int]] = []
    for _ in range(n_samples):
        row = [1 if random.random() < p_active[i] else 0 for i in range(NUM_MUSCLES)]
        out.append(row)
    logger.debug(
        "generate_binary_pattern: n=%d p=%s seed=%s",
        n_samples,
        p_active,
        seed,
    )
    return out


def generate_fixed_pattern(pattern: List[int], n_samples: int) -> List[List[int]]:
    """Repeat the same 4-bit pattern for n_samples (for deterministic tests)."""
    if len(pattern) != NUM_MUSCLES:
        raise ValueError(f"pattern must have length {NUM_MUSCLES}")
    return [list(pattern) for _ in range(n_samples)]


# ---------------------------------------------------------------------------
# Default gesture map: combined tuple -> robot command (>= 7 gestures + HOME example)
# ---------------------------------------------------------------------------

DEFAULT_GESTURE_MAP: Dict[Tuple[int, int, int, int], str] = {
    (1, 1, 1, 1): GC.HOME,
    (1, 1, 0, 0): GC.MOVE_FORWARD,
    (1, 0, 1, 0): GC.REACH_UP,
    (0, 1, 1, 0): GC.ELBOW_TUCK,
    (0, 0, 1, 1): GC.SHOULDER_THUMB_COMBO,
    (1, 0, 0, 1): GC.GRIPPER_BICEP,
    (0, 1, 0, 1): GC.GRIPPER_FOREARM,
    (1, 1, 1, 0): GC.READY_STANCE,
    (0, 0, 0, 0): GC.IDLE,
}


# ---------------------------------------------------------------------------
# GestureInterpreter (4-channel binary EMG)
# ---------------------------------------------------------------------------


@dataclass
class GestureInterpreter:
    """
    Buffer (t_mono, List[int] length 4). Within window_s, count how many samples
    each muscle was 1; if count >= min_activation_count, that muscle is 1 in the
    combined pattern. Map combined tuple -> command. Cooldown between emits.
    """

    window_s: float = 0.2
    min_activation_count: int = 3
    cooldown_s: float = 0.35
    """If False, patterns that map to UNKNOWN do not emit (no cooldown update)."""
    emit_unknown: bool = False
    gesture_map: Dict[Tuple[int, int, int, int], str] = field(
        default_factory=lambda: dict(DEFAULT_GESTURE_MAP)
    )

    _buffer: Deque[Tuple[float, List[int]]] = field(default_factory=deque)
    _last_emit_mono: float = field(default_factory=lambda: 0.0)
    _last_command: str = GC.UNKNOWN

    def __post_init__(self) -> None:
        self._last_emit_mono = 0.0
        logger.info(
            "GestureInterpreter init: window_s=%.3f s min_activation_count=%d cooldown_s=%.3f",
            self.window_s,
            self.min_activation_count,
            self.cooldown_s,
        )

    def clear_buffer(self) -> None:
        n = len(self._buffer)
        self._buffer.clear()
        self._last_emit_mono = 0.0
        logger.info("clear_buffer: dropped %d samples, cooldown reset", n)

    def add_input(self, value: List[int], t_mono: Optional[float] = None) -> None:
        """
        Append one 4-channel binary sample. value[i] in {0,1} for
        [bicep, forearm, shoulder, thumb].
        """
        if len(value) != NUM_MUSCLES:
            raise ValueError(f"value must have length {NUM_MUSCLES}, got {len(value)}")
        if t_mono is None:
            t_mono = time.monotonic()
        v = [1 if int(x) != 0 else 0 for x in value]
        self._buffer.append((t_mono, v))
        cutoff = t_mono - self.window_s
        while self._buffer and self._buffer[0][0] < cutoff:
            self._buffer.popleft()
        logger.debug(
            "add_input: t=%.6f value=%s buffer_len=%d",
            t_mono,
            v,
            len(self._buffer),
        )

    def map_gesture(self, combined: Tuple[int, int, int, int]) -> str:
        """Map combined pattern to robot command string."""
        cmd = self.gesture_map.get(combined, GC.UNKNOWN)
        logger.debug("map_gesture: combined=%s -> %s", combined, cmd)
        return cmd

    def process_gesture(self, t_mono: Optional[float] = None) -> Optional[str]:
        """
        Count per-muscle activations in buffer; threshold to combined tuple;
        if pattern matches and cooldown elapsed, return command.
        """
        if t_mono is None:
            t_mono = time.monotonic()
        if not self._buffer:
            logger.debug("process_gesture: empty buffer")
            return None

        counts = [0, 0, 0, 0]
        for _, reading in self._buffer:
            for i in range(NUM_MUSCLES):
                if reading[i] == 1:
                    counts[i] += 1

        thr = self.min_activation_count
        combined_list = [1 if c >= thr else 0 for c in counts]
        combined = (combined_list[0], combined_list[1], combined_list[2], combined_list[3])

        logger.debug(
            "process_gesture: n_samples=%d counts=%s thr=%d combined=%s",
            len(self._buffer),
            counts,
            thr,
            combined,
        )

        if combined == (0, 0, 0, 0):
            logger.debug("process_gesture: all muscles below threshold -> no emit")
            return None

        prev_emit = self._last_emit_mono
        dt_since_last = (t_mono - prev_emit) if prev_emit > 0.0 else 0.0
        if prev_emit > 0.0 and dt_since_last < self.cooldown_s:
            logger.debug(
                "process_gesture: cooldown active (%.3f s < %.3f s), skip emit",
                dt_since_last,
                self.cooldown_s,
            )
            return None

        command = self.map_gesture(combined)
        if command == GC.UNKNOWN and not self.emit_unknown:
            logger.debug(
                "process_gesture: combined=%s maps to UNKNOWN (emit_unknown=False), skip",
                combined,
            )
            return None

        self._last_emit_mono = t_mono
        self._last_command = command
        logger.info(
            "process_gesture: EMIT command=%s combined=%s counts=%s dt_since_last=%.3f",
            command,
            combined,
            counts,
            dt_since_last,
        )
        return command


# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------


def main() -> None:
    logger.info("=== gesture_interpreter_sim test harness (4-ch EMG) ===")
    gi = GestureInterpreter(
        window_s=0.2,
        min_activation_count=3,
        cooldown_s=0.25,
    )

    dt = 0.02
    t0 = time.monotonic()

    # Phase 1: sparse random bits — counts likely below threshold
    logger.info("Phase 1: sparse binary noise")
    patterns = generate_binary_pattern(20, p_active=(0.15, 0.15, 0.15, 0.15), seed=42)
    for i, row in enumerate(patterns):
        gi.add_input(row, t0 + i * dt)
        gi.process_gesture(t0 + i * dt)

    gi.clear_buffer()

    # Phase 2: sustained HOME pattern [1,1,1,1] — should exceed threshold
    logger.info("Phase 2: sustained HOME pattern [1,1,1,1]")
    t1 = time.monotonic()
    burst = generate_fixed_pattern([1, 1, 1, 1], 25)
    for i, row in enumerate(burst):
        gi.add_input(row, t1 + i * dt)
        out = gi.process_gesture(t1 + i * dt)
        if out:
            logger.info("Harness: emitted %s at i=%d", out, i)

    gi.clear_buffer()

    # Phase 3: MOVE_FORWARD [1,1,0,0]
    logger.info("Phase 3: MOVE_FORWARD [1,1,0,0]")
    t2 = time.monotonic()
    burst2 = generate_fixed_pattern([1, 1, 0, 0], 20)
    for i, row in enumerate(burst2):
        gi.add_input(row, t2 + i * dt)
        out = gi.process_gesture(t2 + i * dt)
        if out:
            logger.info("Harness: emitted %s at i=%d", out, i)

    gi.clear_buffer()

    # Phase 4: cooldown — same pattern twice quickly
    logger.info("Phase 4: cooldown (double process same window time)")
    t3 = time.monotonic()
    for row in generate_fixed_pattern([1, 0, 1, 0], 15):
        gi.add_input(row, t3)
        t3 += dt
    g1 = gi.process_gesture(t3)
    logger.info("Harness: first emit -> %s", g1)
    g2 = gi.process_gesture(t3)
    logger.info("Harness: immediate repeat -> %s (expect None if cooldown)", g2)

    logger.info("=== test harness finished ===")


if __name__ == "__main__":
    main()
