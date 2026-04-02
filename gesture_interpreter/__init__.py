"""
Gesture interpreter: map EMG features to discrete gesture labels.

Use: from gesture_interpreter import interpret_gesture, GESTURE_NAMES
"""

from .gesture_config import GESTURE_NAMES
from .interpreter import interpret_gesture

__all__ = ["interpret_gesture", "GESTURE_NAMES"]
