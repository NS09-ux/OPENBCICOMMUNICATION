"""
Real-time streaming from OpenBCI Cyton using BrainFlow: poll the board buffer,
run the same preprocess + feature extraction as the CSV pipeline, and output
features every window step (e.g. every 1 s for a 2 s window).

Requirements: pip install brainflow
Configure: config/pipeline_config.py (BICEP_CHANNEL_INDICES, CYTON_SERIAL_PORT, etc.)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

_script_dir = Path(__file__).resolve().parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

import numpy as np

try:
    from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds
except ImportError:
    BoardShim = None  # type: ignore
    BrainFlowInputParams = None  # type: ignore
    BoardIds = None  # type: ignore

from openbci_ml_pipeline import (
    preprocess,
    extract_features_for_window,
)
from config.pipeline_config import (
    BICEP_CHANNEL_INDICES,
    SAMPLE_RATE_HZ,
    WINDOW_LENGTH_S,
    WINDOW_STEP_S,
    CYTON_SERIAL_PORT,
    CYTON_DAISY,
)


def run_stream(
    port: Optional[str] = None,
    on_features=None,
    verbose: bool = True,
    ssvep: bool = False,
):
    """
    Stream from Cyton in real time using BrainFlow; every WINDOW_STEP_S seconds
    poll new data, buffer it, and when a full window is available run preprocess +
    feature extraction (or SSVEP interpretation if ssvep=True) and call
    on_features(...) or print.

    port: Serial port (e.g. "COM4" on Windows). None = use config.
    on_features: Callable(features_dict) called for each new feature/command window.
    verbose: If True, print each feature set or command to stdout.
    ssvep: If True, interpret window as SSVEP EEG and output command (FRONT/LEFT/etc.)
           Set BICEP_CHANNEL_INDICES to occipital channels (e.g. O1, Oz, O2).
    """
    if BoardShim is None or BrainFlowInputParams is None or BoardIds is None:
        raise ImportError(
            "BrainFlow is not installed. Run: pip install brainflow"
        )

    port = port or CYTON_SERIAL_PORT
    if not port:
        raise ValueError(
            "Serial port is required. Set CYTON_SERIAL_PORT in config/pipeline_config.py "
            "or pass --port COM4 (Windows) or /dev/ttyUSB0 (Linux)."
        )

    board_id = BoardIds.CYTON_DAISY_BOARD if CYTON_DAISY else BoardIds.CYTON_BOARD
    exg_channels = BoardShim.get_exg_channels(board_id)
    # Subset of EXG row indices for our bicep channels (0..7 map to EXG 0..7)
    channel_rows = [exg_channels[i] for i in BICEP_CHANNEL_INDICES if i < len(exg_channels)]
    if len(channel_rows) != len(BICEP_CHANNEL_INDICES):
        raise ValueError(
            f"BICEP_CHANNEL_INDICES {BICEP_CHANNEL_INDICES} out of range for "
            f"{len(exg_channels)} EXG channels."
        )

    fs = BoardShim.get_sampling_rate(board_id)
    win_samples = int(WINDOW_LENGTH_S * fs)
    step_samples = max(1, int(WINDOW_STEP_S * fs))
    n_channels = len(channel_rows)

    params = BrainFlowInputParams()
    params.serial_port = port
    board = BoardShim(board_id, params)

    try:
        board.prepare_session()
        board.start_stream()
        if verbose:
            print(
                f"Streaming from Cyton (BrainFlow, port={port}, {n_channels} channels). "
                "Ctrl+C to stop.",
                flush=True,
            )
    except Exception as e:
        raise RuntimeError(f"Failed to start Cyton stream: {e}") from e

    buffer: list[np.ndarray] = []

    try:
        while True:
            time.sleep(WINDOW_STEP_S)
            # Get all data accumulated since last call (and remove from BrainFlow buffer)
            data = board.get_board_data()
            if data is None or data.size == 0:
                continue
            # data shape: (num_rows, num_samples); we need (num_samples, n_channels)
            n_rows, n_cols = data.shape
            if n_cols == 0:
                continue
            # Extract bicep channel rows and transpose -> (n_cols, n_channels)
            chunk = data[channel_rows, :].T.astype(np.float64)
            np.nan_to_num(chunk, copy=False, nan=0.0)
            for i in range(chunk.shape[0]):
                buffer.append(chunk[i, :])

            while len(buffer) >= win_samples:
                window = np.stack(buffer[:win_samples], axis=0)
                del buffer[:step_samples]
                feats = {"time_center_s": time.time()}
                try:
                    if ssvep:
                        from ssvep_interpreter import interpret_ssvep_window
                        result = interpret_ssvep_window(window, fs)
                        feats["command"] = result["command"]
                        feats["frequency_hz"] = result["frequency_hz"]
                        feats["power"] = result["power"]
                    else:
                        filtered = preprocess(window.copy(), fs)
                        feats.update(extract_features_for_window(filtered))
                except Exception as e:
                    if verbose:
                        print(f"Pipeline error: {e}", file=sys.stderr)
                    continue
                if on_features:
                    try:
                        on_features(feats)
                    except Exception as e:
                        print(f"on_features error: {e}", file=sys.stderr)
                if verbose:
                    if ssvep:
                        print(f"command={feats['command']} frequency_hz={feats['frequency_hz']:.1f} power={feats['power']:.4f}")
                    else:
                        parts = [
                            f"{k}={v:.4f}"
                            for k, v in feats.items()
                            if isinstance(v, (int, float))
                        ]
                        print("features:", " ".join(parts))
    except KeyboardInterrupt:
        pass
    finally:
        try:
            board.stop_stream()
            board.release_session()
        except Exception:
            pass
        if verbose:
            print("Stream stopped.", flush=True)


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(
        description="Stream OpenBCI Cyton (BrainFlow) and run ML pipeline in real time."
    )
    p.add_argument(
        "--port",
        default=None,
        help="Serial port (default: from config). Example: COM4 or /dev/ttyUSB0",
    )
    p.add_argument("--quiet", action="store_true", help="Do not print features/command to stdout.")
    p.add_argument(
        "--ssvep",
        action="store_true",
        help="SSVEP mode: output command (FRONT/LEFT/etc.) from flicker frequency. Use occipital channels.",
    )
    args = p.parse_args()
    run_stream(port=args.port, verbose=not args.quiet, ssvep=args.ssvep)
