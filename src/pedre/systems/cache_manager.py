"""Lightweight cache manager for scene state transitions.

This module provides the CacheManager class, which replaces the previous
CacheRegistry/CacheLoader/BaseCacheProvider pattern with a simpler approach
that directly calls methods on BaseSystem instances.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages scene state cache for transitions.

    The CacheManager holds in-memory state for each scene, allowing systems
    to preserve their state when the player leaves a scene and restore it
    when they return.

    Instead of using separate provider classes, this manager directly calls
    cache_scene_state() and restore_scene_state() on each system.

    Attributes:
        _cache: Nested dictionary mapping scene_name -> system_name -> state dict.

    Example:
        cache_manager = CacheManager()

        # When leaving a scene
        cache_manager.cache_scene("village", context)

        # When returning to a scene
        restored = cache_manager.restore_scene("village", context)
    """

    def __init__(self) -> None:
        """Initialize the cache manager with empty cache."""
        # scene_name -> system_name -> state dict
        self._cache: dict[str, dict[str, Any]] = {}

    def cache_scene(self, scene_name: str, context: GameContext) -> None:
        """Cache all system states for a scene.

        Iterates through all systems and calls cache_scene_state() on each,
        storing the returned state dictionaries.

        Args:
            scene_name: Name of the scene being left.
            context: Game context providing access to all systems.
        """
        scene_state: dict[str, Any] = {}
        for system in context.get_systems().values():
            state = system.cache_scene_state(scene_name)
            if state:
                scene_state[system.name] = state
                logger.debug("Cached state for system '%s' in scene '%s'", system.name, scene_name)

        self._cache[scene_name] = scene_state
        logger.info("Cached state for %d systems in scene '%s'", len(scene_state), scene_name)

    def restore_scene(self, scene_name: str, context: GameContext) -> bool:
        """Restore cached system states for a scene.

        Iterates through all systems and calls restore_scene_state() on each
        with their previously cached state.

        Args:
            scene_name: Name of the scene being entered.
            context: Game context providing access to all systems.

        Returns:
            True if cached state was found and restored, False if no cache exists.
        """
        scene_state = self._cache.get(scene_name)
        if not scene_state:
            logger.debug("No cached state found for scene '%s'", scene_name)
            return False

        restored_count = 0
        for system in context.get_systems().values():
            if system.name in scene_state:
                system.restore_scene_state(scene_name, scene_state[system.name])
                restored_count += 1
                logger.debug("Restored state for system '%s' in scene '%s'", system.name, scene_name)

        logger.info("Restored state for %d systems in scene '%s'", restored_count, scene_name)
        return True

    def has_cached_state(self, scene_name: str) -> bool:
        """Check if a scene has cached state.

        Args:
            scene_name: Name of the scene to check.

        Returns:
            True if cached state exists for the scene.
        """
        return scene_name in self._cache

    def to_dict(self) -> dict[str, Any]:
        """Serialize cache state for save files.

        Returns:
            Dictionary mapping scene names to their cached system states.
        """
        return self._cache.copy()

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore cache state from save file data.

        Args:
            data: Previously serialized cache state from to_dict().
        """
        self._cache = data.copy()
        logger.debug("Restored cache for %d scenes from save data", len(self._cache))

    def clear(self) -> None:
        """Clear all cached state.

        Called when starting a new game or when cache should be reset.
        """
        scene_count = len(self._cache)
        self._cache.clear()
        logger.debug("Cleared cache for %d scenes", scene_count)
