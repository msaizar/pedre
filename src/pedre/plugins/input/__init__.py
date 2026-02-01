"""Input plugin for handling player controls and keyboard input.

This package provides:
- InputManager: Core input handling plugin with key state tracking

The input plugin handles keyboard input for player movement and actions,
with support for both arrow keys and WASD, normalized diagonal movement,
and configurable movement speed.
"""

from pedre.plugins.input.manager import InputManager

__all__ = [
    "InputManager",
]
