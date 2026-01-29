"""Scene management system.

This module provides the SceneManager class, which handles scene transitions,
map loading from Tiled files, and system updates during scene changes.

Actions (registered via INSTALLED_ACTIONS):
- ChangeSceneAction

Events (registered via INSTALLED_EVENTS):
- SceneStartEvent
"""

from pedre.systems.scene.manager import SceneManager, TransitionState

__all__ = ["SceneManager", "TransitionState"]
