"""
OpenBCI → ML pipeline: load recording, preprocess, extract features, output.

Works with OpenBCI CSV export (reference + DRL + two bicep channels).
Configure channel indices and filtering in config/pipeline_config.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow importing config when run from project root
_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

import numpy as np
import pandas as pd
from scipy import signal as scipy_signal
from typing import Tuple, Optional

# Project config
try:
    from config.pipeline_config import (
        get_active_channel_indices,
        SAMPLE_RATE_HZ,
        HIGHPASS_HZ,
        LOWPASS_HZ,
        USE_EMG_BAND,
        EMG_LOW_HZ,
        EMG_HIGH_HZ,
        WINDOW_LENGTH_S,
        WINDOW_STEP_S,
        FEATURES_CSV_PATH,
    )
except ImportError:
    def get_active_channel_indices():
        return [0, 1]
    SAMPLE_RATE_HZ = 250
    HIGHPASS_HZ = 0.5
    LOWPASS_HZ = 100.0
    USE_EMG_BAND = True
    EMG_LOW_HZ = 20.0
    EMG_HIGH_HZ = 450.0
    WINDOW_LENGTH_S = 2.0
    WINDOW_STEP_S = 1.0
    FEATURES_CSV_PATH = "features.csv"


def load_openbci_csv(csv_path: str) -> Tuple[pd.DataFrame, np.ndarray, float]:
    """
    Load an OpenBCI GUI-exported CSV.
    Returns (full dataframe, bicep data array in µV, sample_rate).
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    df = pd.read_csv(csv_path)
    # Find EXG columns: "EXG Channel 0" ... "EXG Channel 7" or similar
    exg_cols = [c for c in df.columns if "EXG" in c or (isinstance(c, str) and "Channel" in c and c.split()[-1].isdigit())]
    if not exg_cols:
        numeric = df.select_dtypes(include=[np.number]).columns.tolist()
        exg_cols = numeric[1:17] if len(numeric) >= 17 else numeric[:16]

    # Build channel index -> column name (allow 0..15 for Cyton+Daisy)
    MAX_EXG = 16
    channel_cols = []
    for i in range(MAX_EXG):
        found = False
        for c in exg_cols:
            if f"Channel {i}" in c or c == f"EXG Channel {i}":
                channel_cols.append(c)
                found = True
                break
        if not found and i < len(exg_cols):
            channel_cols.append(exg_cols[i])

    active_indices = get_active_channel_indices()
    if not active_indices or len(channel_cols) <= max(active_indices):
        raise ValueError(
            f"Config needs channel indices up to {max(active_indices)} but CSV has {len(channel_cols)} EXG columns. "
            "Check pipeline_config.py and your CSV header."
        )

    selected_cols = [channel_cols[i] for i in active_indices]
    data = df[selected_cols].values.astype(np.float64)
    # Replace any NaN with 0 for safety
    np.nan_to_num(data, copy=False, nan=0.0)
    return df, data, SAMPLE_RATE_HZ


def bandpass_filter(data: np.ndarray, low_hz: float, high_hz: float, fs: float, order: int = 4) -> np.ndarray:
    """Butterworth bandpass. data shape (samples, channels)."""
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


def highpass_filter(data: np.ndarray, cutoff_hz: float, fs: float, order: int = 4) -> np.ndarray:
    """Highpass to remove DC / drift."""
    nyq = fs / 2.0
    low = min(0.99, max(0.001, cutoff_hz / nyq))
    b, a = scipy_signal.butter(order, low, btype="high")
    out = np.zeros_like(data)
    for ch in range(data.shape[1]):
        out[:, ch] = scipy_signal.filtfilt(b, a, data[:, ch])
    return out


def preprocess(data: np.ndarray, fs: float) -> np.ndarray:
    """Highpass then optional EMG bandpass."""
    data = highpass_filter(data, HIGHPASS_HZ, fs)
    if USE_EMG_BAND:
        data = bandpass_filter(data, EMG_LOW_HZ, min(EMG_HIGH_HZ, fs / 2.0 - 1), fs)
    else:
        data = bandpass_filter(data, HIGHPASS_HZ, LOWPASS_HZ, fs)
    return data


def extract_features_for_window(window: np.ndarray) -> dict:
    """One window (samples x channels). Returns RMS and mean abs value per channel."""
    features = {}
    for ch in range(window.shape[1]):
        x = window[:, ch]
        features[f"ch{ch}_rms"] = np.sqrt(np.mean(x ** 2))
        features[f"ch{ch}_mean_abs"] = np.mean(np.abs(x))
    return features


def run_pipeline(csv_path: str, output_csv: Optional[str] = None, plot: bool = False) -> pd.DataFrame:
    """
    Load CSV, preprocess active channels (EMG/EEG), segment, extract features, save to CSV.
    Returns the features DataFrame.
    """
    output_csv = output_csv or FEATURES_CSV_PATH
    df_raw, data, fs = load_openbci_csv(csv_path)
    n_samples, n_channels = data.shape
    print(f"Loaded {n_samples} samples at {fs} Hz, {n_channels} bicep channel(s).")

    data = preprocess(data, fs)
    win_samples = int(WINDOW_LENGTH_S * fs)
    step_samples = int(WINDOW_STEP_S * fs)
    if step_samples < 1:
        step_samples = win_samples

    rows = []
    t_start = 0
    while t_start + win_samples <= n_samples:
        window = data[t_start : t_start + win_samples, :]
        feats = extract_features_for_window(window)
        feats["time_start_s"] = t_start / fs
        feats["time_center_s"] = (t_start + win_samples / 2) / fs
        rows.append(feats)
        t_start += step_samples

    features_df = pd.DataFrame(rows)
    features_df.to_csv(output_csv, index=False)
    print(f"Computed {len(features_df)} windows → saved to {output_csv}")

    if plot and len(rows) > 0:
        try:
            import matplotlib.pyplot as plt
            fig, axes = plt.subplots(n_channels, 1, figsize=(10, 2 * n_channels), sharex=True)
            if n_channels == 1:
                axes = [axes]
            t_axis = np.arange(n_samples) / fs
            active_idx = get_active_channel_indices()
            for ch in range(n_channels):
                axes[ch].plot(t_axis, data[:, ch], alpha=0.8)
                axes[ch].set_ylabel(f"Ch{active_idx[ch] if ch < len(active_idx) else ch} (µV)")
            axes[-1].set_xlabel("Time (s)")
            axes[0].set_title("Preprocessed channels")
            plt.tight_layout()
            plot_path = Path(output_csv).with_suffix(".png")
            plt.savefig(plot_path)
            plt.close()
            print(f"Plot saved to {plot_path}")
        except Exception as e:
            print(f"Plot skip: {e}")

    return features_df


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python openbci_ml_pipeline.py <path_to_openbci.csv> [output_features.csv] [--plot]")
        sys.exit(1)
    csv_path = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None
    do_plot = "--plot" in sys.argv
    run_pipeline(csv_path, output_csv=out, plot=do_plot)
