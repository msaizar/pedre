"""Loader for cache providers, similar to SystemLoader."""

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING, Any

from pedre.caches.registry import CacheRegistry

if TYPE_CHECKING:
    from pedre.caches.base import BaseCacheProvider
    from pedre.config import GameSettings
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


class CacheLoader:
    """Loads and manages cache provider instances.

    The CacheLoader handles:
    1. Importing cache modules to trigger registration
    2. Instantiating cache providers
    3. Coordinating cache/restore operations across all providers
    4. Serializing/deserializing all caches for save files
    """

    def __init__(self, settings: GameSettings) -> None:
        """Initialize the cache loader.

        Args:
            settings: Game configuration containing installed_caches list.
        """
        self.settings = settings
        self._instances: dict[str, BaseCacheProvider] = {}
        self._load_order: list[str] = []

    def load_modules(self) -> None:
        """Import all configured cache modules to trigger registration."""
        installed_caches = self.settings.installed_caches or []
        for module_path in installed_caches:
            try:
                importlib.import_module(module_path)
                logger.debug("Loaded cache module: %s", module_path)
            except ImportError:
                logger.exception("Could not load cache module '%s'", module_path)
                raise

    def instantiate_all(self) -> dict[str, BaseCacheProvider]:
        """Create instances of all registered cache providers.

        Returns:
            Dictionary mapping cache names to their instances.
        """
        self.load_modules()

        all_caches = CacheRegistry.get_all()
        if not all_caches:
            logger.warning("No cache providers registered")
            return {}

        # Sort by priority (lower = earlier)
        sorted_caches = sorted(all_caches.items(), key=lambda x: x[1].priority)

        self._load_order = [name for name, _ in sorted_caches]

        for name in self._load_order:
            cache_class = all_caches[name]
            self._instances[name] = cache_class()
            logger.debug("Instantiated cache provider: %s", name)

        logger.info("Instantiated %d cache providers", len(self._instances))
        return self._instances

    def cache_all(self, scene_name: str, context: GameContext) -> None:
        """Call cache() on all providers.

        Args:
            scene_name: Name of the scene being left.
            context: Game context.
        """
        for name in self._load_order:
            cache = self._instances.get(name)
            if cache:
                cache.cache(scene_name, context)
                logger.debug("Cached state for %s in scene %s", name, scene_name)

    def restore_all(self, scene_name: str, context: GameContext) -> bool:
        """Call restore() on all providers.

        Args:
            scene_name: Name of the scene being entered.
            context: Game context.

        Returns:
            True if any cache had state to restore.
        """
        any_restored = False
        for name in self._load_order:
            cache = self._instances.get(name)
            if cache and cache.restore(scene_name, context):
                any_restored = True
                logger.debug("Restored state for %s in scene %s", name, scene_name)
        return any_restored

    def clear_all(self) -> None:
        """Clear all cache providers."""
        for cache in self._instances.values():
            cache.clear()
        logger.debug("Cleared all cache providers")

    def to_dict(self) -> dict[str, Any]:
        """Serialize all caches for save files.

        Returns:
            Dictionary mapping cache names to their serialized state.
        """
        result: dict[str, Any] = {}
        for name, cache in self._instances.items():
            result[name] = cache.to_dict()
        return result

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore all caches from save file data.

        Args:
            data: Dictionary mapping cache names to their serialized state.
        """
        for name, cache_data in data.items():
            cache = self._instances.get(name)
            if cache:
                cache.from_dict(cache_data)
                logger.debug("Restored cache %s from save data", name)
            else:
                logger.warning("Unknown cache in save data: %s", name)

    def get_cache(self, name: str) -> BaseCacheProvider | None:
        """Get a cache provider instance by name."""
        return self._instances.get(name)
