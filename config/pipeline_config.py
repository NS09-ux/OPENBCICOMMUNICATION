"""
Configuration for the OpenBCI → ML pipeline.

Supports:
- EMG: 10 electrodes (Cyton + Daisy required; use 10 of the 16 EXG channels).
- EEG: 16 electrodes (Cyton + Daisy, all 16 EXG channels).

Set ACTIVE_CHANNELS to "emg" or "eeg" to choose which set is used for streaming and CSV pipeline.
"""

# --- Channel layout (indices 0–15 on Cyton + Daisy) ---
# EMG: 10 electrodes. Set to the EXG indices where your 10 EMG electrodes are connected.
EMG_CHANNEL_INDICES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]  # 10 channels

# EEG: 16 electrodes. All 16 EXG channels (Cyton + Daisy).
EEG_CHANNEL_INDICES = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]  # 16 channels

# Which set to use for streaming and CSV pipeline: "emg" or "eeg"
ACTIVE_CHANNELS = "emg"

# Backward compatibility: used only if ACTIVE_CHANNELS is not set (legacy).
# Prefer EMG_CHANNEL_INDICES / EEG_CHANNEL_INDICES + ACTIVE_CHANNELS.
BICEP_CHANNEL_INDICES = [1, 6]

# --- Board and sampling ---
# Cyton + Daisy required for 16 channels. Daisy sampling rate is 125 Hz; Cyton-only is 250 Hz.
CYTON_DAISY = True
SAMPLE_RATE_HZ = 125  # 125 for Daisy; use 250 for Cyton-only (8 ch)

# --- Preprocessing ---
# For EEG (e.g. SSVEP) set USE_EMG_BAND = False so you keep 4–60 Hz; for EMG keep True.
HIGHPASS_HZ = 0.5   # Remove DC / slow drift
LOWPASS_HZ = 100.0
USE_EMG_BAND = True
EMG_LOW_HZ = 20.0
EMG_HIGH_HZ = 450.0

# --- Segmentation ---
WINDOW_LENGTH_S = 2.0
WINDOW_STEP_S = 1.0

# --- Output ---
FEATURES_CSV_PATH = "features.csv"

# --- Streaming ---
CYTON_SERIAL_PORT = "COM3"  # Windows. On Pi: "/dev/ttyUSB0" or "/dev/ttyACM0"

# --- ROS /emg_commands (cyton_emg_ros): four muscles → EXG indices 0–15 ---
# Order: [bicep, forearm, shoulder, thumb]. Match your electrode wiring to the board.
EMG_COMMANDS_EXG_INDICES = [0, 1, 2, 3]
# Mean absolute envelope (µV) must exceed this to count as active (1). Tune per user; or use four values.
EMG_COMMANDS_THRESHOLD_UV = 75.0
# How many samples per channel to average for envelope (at ~125 Hz, 32 ≈ 0.26 s)
EMG_COMMANDS_ENVELOPE_SAMPLES = 32


def get_active_channel_indices():
    """Return the list of EXG channel indices to use (10 for EMG, 16 for EEG)."""
    if ACTIVE_CHANNELS == "eeg":
        return list(EEG_CHANNEL_INDICES)
    if ACTIVE_CHANNELS == "emg":
        return list(EMG_CHANNEL_INDICES)
    return list(BICEP_CHANNEL_INDICES)
