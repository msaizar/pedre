"""Scene management system.

This module provides the SceneManager class, which handles scene transitions,
map loading from Tiled files, and system updates during scene changes.
"""

from pedre.systems.scene.actions import ChangeSceneAction
from pedre.systems.scene.events import SceneStartEvent
from pedre.systems.scene.manager import SceneManager, TransitionState

__all__ = ["ChangeSceneAction", "SceneManager", "SceneStartEvent", "TransitionState"]
