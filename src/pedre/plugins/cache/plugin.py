"""Cache plugin for scene state transitions.

This module provides the CachePlugin plugin, which manages scene state cache
to preserve plugin states when the player transitions between scenes.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

from pedre.plugins.cache.base import CacheBasePlugin
from pedre.plugins.registry import PluginRegistry

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext

logger = logging.getLogger(__name__)


@PluginRegistry.register
class CachePlugin(CacheBasePlugin):
    """Manages scene state cache for transitions.

    The CachePlugin holds in-memory state for each scene, allowing plugins
    to preserve their state when the player leaves a scene and restore it
    when they return.

    This plugin directly calls cache_scene_state() and restore_scene_state()
    on each plugin to manage their cached state.

    Attributes:
        _cache: Nested dictionary mapping scene_name -> plugin_name -> state dict.

    Example:
        # Access via context
        cache_plugin = context.cache_plugin

        # When leaving a scene
        cache_plugin.cache_scene("village")

        # When returning to a scene
        restored = cache_plugin.restore_scene("village")
    """

    name: ClassVar[str] = "cache"
    dependencies: ClassVar[list[str]] = []

    def __init__(self) -> None:
        """Initialize the cache plugin with empty cache."""
        # scene_name -> plugin_name -> state dict
        self._cache: dict[str, dict[str, Any]] = {}
        self.context: GameContext

    def setup(self, context: GameContext) -> None:
        """Initialize with context.

        Args:
            context: Game context providing access to all plugins.
        """
        self.context = context

    def reset(self) -> None:
        """Reset cache for new game."""
        self.clear()

    def cache_scene(self, scene_name: str) -> None:
        """Cache all plugin states for a scene.

        Iterates through all plugins and calls cache_scene_state() on each,
        storing the returned state dictionaries.

        Args:
            scene_name: Name of the scene being left.
        """
        scene_state: dict[str, Any] = {}
        for plugin in self.context.get_plugins().values():
            state = plugin.cache_scene_state(scene_name)
            if state:
                scene_state[plugin.name] = state
                logger.debug("Cached state for plugin '%s' in scene '%s'", plugin.name, scene_name)

        self._cache[scene_name] = scene_state
        logger.info("Cached state for %d plugins in scene '%s'", len(scene_state), scene_name)

    def restore_scene(self, scene_name: str) -> bool:
        """Restore cached plugin states for a scene.

        Iterates through all plugins and calls restore_scene_state() on each
        with their previously cached state.

        Args:
            scene_name: Name of the scene being entered.

        Returns:
            True if cached state was found and restored, False if no cache exists.
        """
        scene_state = self._cache.get(scene_name)
        if not scene_state:
            logger.debug("No cached state found for scene '%s'", scene_name)
            return False

        restored_count = 0
        for plugin in self.context.get_plugins().values():
            if plugin.name in scene_state:
                plugin.restore_scene_state(scene_name, scene_state[plugin.name])
                restored_count += 1
                logger.debug("Restored state for plugin '%s' in scene '%s'", plugin.name, scene_name)

        logger.info("Restored state for %d plugins in scene '%s'", restored_count, scene_name)
        return True

    def has_cached_state(self, scene_name: str) -> bool:
        """Check if a scene has cached state.

        Args:
            scene_name: Name of the scene to check.

        Returns:
            True if cached state exists for the scene.
        """
        return scene_name in self._cache

    def clear(self) -> None:
        """Clear all cached state.

        Called when starting a new game or when cache should be reset.
        """
        scene_count = len(self._cache)
        self._cache.clear()
        logger.debug("Cleared cache for %d scenes", scene_count)

    def get_save_state(self) -> dict[str, Any]:
        """Get cache state for saving.

        Returns:
            Dictionary mapping scene names to their cached plugin states.
        """
        return self._cache.copy()

    def restore_save_state(self, state: dict[str, Any]) -> None:
        """Restore cache state from save file data.

        Args:
            state: Previously serialized cache state from get_save_state().
        """
        self._cache = state.copy()
        logger.debug("Restored cache for %d scenes from save data", len(self._cache))
