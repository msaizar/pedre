"""Pluggable cache providers for scene state persistence.

This package provides a registry-based system for caching game state
across scene transitions. Cache providers handle specific aspects of
state (NPCs, scripts, interactions, etc.) and can be configured via
GameSettings.installed_caches.

Example:
    # Create a custom cache provider
    from pedre.caches.base import BaseCacheProvider
    from pedre.caches.registry import CacheRegistry

    @CacheRegistry.register
    class QuestCacheProvider(BaseCacheProvider):
        name = "quest"

        def cache(self, scene_name, context):
            # Store quest state...
            pass

        def restore(self, scene_name, context):
            # Restore quest state...
            return False

        def to_dict(self):
            return {}

        def from_dict(self, data):
            pass

    # Configure in settings
    settings = GameSettings(
        installed_caches=[
            "pedre.caches.npc",
            "pedre.caches.script",
            "mygame.caches.quest",
        ],
    )
"""

from pedre.caches.base import BaseCacheProvider
from pedre.caches.loader import CacheLoader
from pedre.caches.registry import CacheRegistry

__all__ = [
    "BaseCacheProvider",
    "CacheLoader",
    "CacheRegistry",
]
