"""
SSVEP flicker frequencies and robot command mapping.

These frequencies drive the visual flicker for each target. The ML pipeline
detects which frequency is dominant in the EEG (occipital channels) and
maps it to a command for the robot (e.g. ROS / Husky).
"""
from __future__ import annotations
from typing import Optional

# Flicker frequencies (Hz) for each marker. These control the
# on/off duty cycle used to create an SSVEP-eliciting flicker.
FREQUENCIES = {
    "FRONT": 5.0,
    "BACK": 10.0,
    "LEFT": 15.0,
    "RIGHT": 25.0,
    # Center Start/Stop marker flickers at 50 Hz when idle.
    "STARTSTOP": 50.0,
}

# Ordered list of command names (for classifiers that output indices).
COMMAND_NAMES = ["FRONT", "BACK", "LEFT", "RIGHT", "STARTSTOP"]

# Frequency values in the same order as COMMAND_NAMES (Hz).
FREQUENCY_LIST_HZ = [FREQUENCIES[name] for name in COMMAND_NAMES]


def get_frequency_for_command(command: str) -> float:
    """Return flicker frequency (Hz) for a command name."""
    return FREQUENCIES.get(command.upper(), 0.0)


def get_command_for_frequency(freq_hz: float, tolerance_hz: float = 0.5) -> Optional[str]:
    """Return command name whose frequency is closest to freq_hz within tolerance, else None."""
    best_cmd = None
    best_diff = tolerance_hz + 1.0
    for cmd, f in FREQUENCIES.items():
        diff = abs(f - freq_hz)
        if diff < best_diff:
            best_diff = diff
            best_cmd = cmd
    return best_cmd if best_diff <= tolerance_hz else None
