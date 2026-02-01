"""Scene management plugin.

This module provides the ScenePlugin class, which handles scene transitions,
map loading from Tiled files, and plugin updates during scene changes.

Actions (registered via INSTALLED_ACTIONS):
- ChangeSceneAction

Events (registered via INSTALLED_EVENTS):
- SceneStartEvent
"""

from pedre.plugins.scene.base import SceneBasePlugin, TransitionState
from pedre.plugins.scene.plugin import ScenePlugin

__all__ = ["SceneBasePlugin", "ScenePlugin", "TransitionState"]
