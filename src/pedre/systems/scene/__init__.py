"""Scene management system.

This module provides the SceneManager class, which handles scene transitions
and orchestrates map loading (via MapManager) and system updates during scene changes.
"""

from pedre.systems.scene.manager import SceneManager, event_handler

__all__ = ["SceneManager", "event_handler"]
