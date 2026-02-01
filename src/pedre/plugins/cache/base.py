"""Base class for cache plugin."""

from abc import ABC, abstractmethod

from pedre.plugins.base import BasePlugin


class CacheBasePlugin(BasePlugin, ABC):
    """Base class for cache plugin."""

    role = "cache_plugin"

    @abstractmethod
    def cache_scene(self, scene_name: str) -> None:
        """Cache all plugin states for a scene.

        Args:
            scene_name: Name of the scene being left.
        """
        ...

    @abstractmethod
    def restore_scene(self, scene_name: str) -> bool:
        """Restore cached plugin states for a scene.

        Args:
            scene_name: Name of the scene being entered.

        Returns:
            True if cached state was found and restored, False if no cache exists.
        """
        ...
