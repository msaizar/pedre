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
    from pedre import GameSettings, run_game
    from pathlib import Path

    if __name__ == "__main__":
        settings = GameSettings(
            window_title="My RPG",
            screen_width=1920,
            screen_height=1080,
        )
        run_game(settings)
"""

__version__ = "0.0.1"

from pedre.config import GameSettings
from pedre.helpers import run_game
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
    "GameSettings",
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
    "run_game",
]
