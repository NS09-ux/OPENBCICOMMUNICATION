"""Simulation / test harness for 4-ch binary EMG (time window, cooldown).

Imports are lazy to avoid runpy warnings when executing gesture_interpreter_sim as __main__.
"""

from typing import TYPE_CHECKING, Any

__all__ = [
    "GestureInterpreter",
    "generate_binary_pattern",
    "generate_fixed_pattern",
]


def __getattr__(name: str) -> Any:
    if name == "GestureInterpreter":
        from .gesture_interpreter_sim import GestureInterpreter

        return GestureInterpreter
    if name == "generate_binary_pattern":
        from .gesture_interpreter_sim import generate_binary_pattern

        return generate_binary_pattern
    if name == "generate_fixed_pattern":
        from .gesture_interpreter_sim import generate_fixed_pattern

        return generate_fixed_pattern
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if TYPE_CHECKING:
    from .gesture_interpreter_sim import (
        GestureInterpreter,
        generate_binary_pattern,
        generate_fixed_pattern,
    )
