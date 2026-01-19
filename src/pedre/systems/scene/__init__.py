"""Scene management system.

This module provides the SceneManager class, which handles scene transitions,
map loading from Tiled files, and system updates during scene changes.
"""

from pedre.systems.scene.manager import SceneManager, TransitionState, event_handler

__all__ = ["SceneManager", "TransitionState", "event_handler"]
