"""Input system for handling player controls and keyboard input.

This package provides:
- InputManager: Core input handling system with key state tracking

The input system handles keyboard input for player movement and actions,
with support for both arrow keys and WASD, normalized diagonal movement,
and configurable movement speed.
"""

from pedre.systems.input.manager import InputManager

__all__ = [
    "InputManager",
]
