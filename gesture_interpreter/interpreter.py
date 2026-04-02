"""
Map EMG feature dict (from openbci_ml_pipeline) to a gesture label.

Replace interpret_gesture() with thresholds, k-NN, LDA, or a trained model.
"""

from __future__ import annotations

from typing import Any, Dict

from .gesture_config import GESTURE_NAMES


def interpret_gesture(features: Dict[str, Any]) -> str:
    """
    Return a gesture label from one window's features (e.g. ch0_rms, ch1_rms).

    Default: placeholder that always returns REST until you implement logic.
    """
    _ = GESTURE_NAMES  # use when you map predictions to labels
    return "REST"
