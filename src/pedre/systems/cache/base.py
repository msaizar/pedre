"""Base class for cache system."""

from abc import ABC, abstractmethod

from pedre.systems.base import BaseSystem


class CacheBaseManager(BaseSystem, ABC):
    """Base class for cache manager."""

    role = "cache_manager"

    @abstractmethod
    def cache_scene(self, scene_name: str) -> None:
        """Cache all system states for a scene.

        Args:
            scene_name: Name of the scene being left.
        """
        ...

    @abstractmethod
    def restore_scene(self, scene_name: str) -> bool:
        """Restore cached system states for a scene.

        Args:
            scene_name: Name of the scene being entered.

        Returns:
            True if cached state was found and restored, False if no cache exists.
        """
        ...
