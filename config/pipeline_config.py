"""
Configuration for the OpenBCI → ML pipeline.

Your setup: reference node, silence/DRL node, and two nodes on the bicep.
The OpenBCI CSV has 8 EXG columns (EXG Channel 0 .. EXG Channel 7).
Map which column indices correspond to your bicep channels.

Example: if reference was on EXG 0, DRL on EXG 1, and the two bicep
electrodes on EXG 2 and EXG 3, set bicep_channel_indices = [2, 3].
"""

# Which EXG column indices (0–7) are your bicep channels?
# Change these to match how you wired the board (ref/DRL may use 0 and 1).
BICEP_CHANNEL_INDICES = [0, 1]  # e.g. [2, 3] if bicep is on channels 2 and 3

# OpenBCI Cyton typical rate (Hz)
SAMPLE_RATE_HZ = 250

# Preprocessing
HIGHPASS_HZ = 0.5   # Remove DC / slow drift (OpenBCI has DC offset)
LOWPASS_HZ = 100.0  # Optional; for EMG often 20–500 Hz, for general biosignal 100 is safe
# Set USE_EMG_BAND = True to bandpass 20–450 Hz (better for muscle activity)
USE_EMG_BAND = True
EMG_LOW_HZ = 20.0
EMG_HIGH_HZ = 450.0

# Segmentation: window length and step (seconds)
WINDOW_LENGTH_S = 2.0
WINDOW_STEP_S = 1.0   # Overlap = window_length - step

# Output
FEATURES_CSV_PATH = "features.csv"

# --- Real-time streaming (Cyton over USB serial) ---
# Windows: "COM3", "COM4", etc. Linux/Mac: "/dev/ttyUSB0" or similar.
# Set to None to auto-detect (pyOpenBCI may try to find a port).
CYTON_SERIAL_PORT = "COM4"
# Set True if using Cyton + Daisy (16 channels).
CYTON_DAISY = False
