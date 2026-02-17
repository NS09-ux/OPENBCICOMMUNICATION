"""
SSVEP interpretation: from a short window of EEG (e.g. occipital channels),
compute power at each target frequency and return the best-matching command.

Use with stream_openbci.py --ssvep (and set channel indices to occipital).
"""

from __future__ import annotations

import sys
from pathlib import Path

_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

import numpy as np
from scipy import signal as scipy_signal
from typing import Optional

from config.ssvep_config import FREQUENCY_LIST_HZ, COMMAND_NAMES, get_command_for_frequency


# SSVEP bandpass (Hz): typical range for flicker responses
SSVEP_LOW_HZ = 4.0
SSVEP_HIGH_HZ = 60.0
# Bin width (Hz) for power at each target frequency
FREQ_BIN_HZ = 1.0


def _bandpass(data: np.ndarray, low_hz: float, high_hz: float, fs: float, order: int = 4) -> np.ndarray:
    """Butterworth bandpass; data (samples, channels)."""
    nyq = fs / 2.0
    low = max(0.01, low_hz / nyq)
    high = min(0.99, high_hz / nyq)
    if low >= high:
        return data
    b, a = scipy_signal.butter(order, [low, high], btype="band")
    out = np.zeros_like(data)
    for ch in range(data.shape[1]):
        out[:, ch] = scipy_signal.filtfilt(b, a, data[:, ch])
    return out


def _power_at_freq(signal_1ch: np.ndarray, fs: float, freq_hz: float, bin_hz: float = FREQ_BIN_HZ) -> float:
    """Average power in [freq_hz - bin_hz/2, freq_hz + bin_hz/2] using FFT."""
    n = len(signal_1ch)
    if n == 0:
        return 0.0
    fft_vals = np.fft.rfft(signal_1ch)
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    df = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
    power = np.abs(fft_vals) ** 2
    low_idx = max(0, int((freq_hz - bin_hz / 2) / df))
    high_idx = min(len(freqs), int((freq_hz + bin_hz / 2) / df) + 1)
    if low_idx >= high_idx:
        return 0.0
    return float(np.mean(power[low_idx:high_idx]))


def interpret_ssvep_window(
    window: np.ndarray,
    fs: float,
    freq_bin_hz: float = FREQ_BIN_HZ,
) -> dict:
    """
    From one window of EEG (samples x channels), return the SSVEP command with
    highest power at the target frequencies.

    window: (n_samples, n_channels) in µV
    fs: sampling rate (Hz)
    freq_bin_hz: width of frequency bin for power (default 1 Hz)

    Returns dict with:
      - command: str, e.g. "LEFT", "FRONT", or "NONE" if no clear peak
      - frequency_hz: float, best frequency
      - power: float, power at that frequency (averaged across channels)
      - powers: dict freq -> power for debugging
    """
    if window.size == 0 or window.shape[0] < 10:
        return {"command": "NONE", "frequency_hz": 0.0, "power": 0.0, "powers": {}}

    filtered = _bandpass(window.copy(), SSVEP_LOW_HZ, min(SSVEP_HIGH_HZ, fs / 2.0 - 1), fs)
    n_channels = filtered.shape[1]
    powers_at_targets = []
    for f in FREQUENCY_LIST_HZ:
        p = 0.0
        for ch in range(n_channels):
            p += _power_at_freq(filtered[:, ch], fs, f, freq_bin_hz)
        p /= max(1, n_channels)
        powers_at_targets.append(p)

    best_idx = int(np.argmax(powers_at_targets))
    best_freq = FREQUENCY_LIST_HZ[best_idx]
    best_power = powers_at_targets[best_idx]
    command = get_command_for_frequency(best_freq, tolerance_hz=1.0) or "NONE"
    if command == "NONE":
        command = COMMAND_NAMES[best_idx]

    powers_dict = {COMMAND_NAMES[i]: powers_at_targets[i] for i in range(len(COMMAND_NAMES))}
    return {
        "command": command,
        "frequency_hz": best_freq,
        "power": best_power,
        "powers": powers_dict,
    }
