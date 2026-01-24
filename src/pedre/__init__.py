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

from pedre.conf import settings
from pedre.helpers import create_game, run_game
from pedre.sprites import AnimatedNPC, AnimatedPlayer
from pedre.systems import (
    AudioManager,
    CameraManager,
    DialogManager,
    EventBus,
    GameContext,
    GameSaveData,
    InputManager,
    InteractionManager,
    InteractiveObject,
    InventoryItem,
    InventoryManager,
    NPCManager,
    ParticleManager,
    PathfindingManager,
    Portal,
    PortalManager,
    SaveManager,
    ScriptManager,
)
from pedre.view_manager import ViewManager
from pedre.views import GameView, MenuView

__all__ = [
    "AnimatedNPC",
    "AnimatedPlayer",
    "AudioManager",
    "CameraManager",
    "DialogManager",
    "EventBus",
    "GameContext",
    "GameSaveData",
    "GameView",
    "InputManager",
    "InteractionManager",
    "InteractiveObject",
    "InventoryItem",
    "InventoryManager",
    "MenuView",
    "NPCManager",
    "ParticleManager",
    "PathfindingManager",
    "Portal",
    "PortalManager",
    "SaveManager",
    "ScriptManager",
    "ViewManager",
    "__version__",
    "create_game",
    "run_game",
    "settings",
]
