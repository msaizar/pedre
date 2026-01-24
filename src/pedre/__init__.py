"""Pedre - A Python RPG framework built on Arcade with seamless Tiled map editor integration.

This package provides a complete framework for building 2D RPG games with features like:
- Tiled map integration
- NPC system with dialogs
- Event-driven scripting
- Inventory management
- Save/load system
- Audio management
- Camera system

Quick start:
    # Create a settings.py file in your project root:
    # WINDOW_TITLE = "My RPG"
    # SCREEN_WIDTH = 1920
    # SCREEN_HEIGHT = 1080

    from pedre import run_game

    if __name__ == "__main__":
        run_game()

Alternative usage:
    # Access settings in your code
    from pedre.conf import settings

    print(settings.WINDOW_TITLE)  # "My RPG"

    # Or customize settings programmatically
    settings.configure(
        WINDOW_TITLE="My RPG",
        SCREEN_WIDTH=1920,
        SCREEN_HEIGHT=1080,
    )
"""

__version__ = "0.0.7"

from pedre.helpers import run_game

__all__ = ["run_game"]
