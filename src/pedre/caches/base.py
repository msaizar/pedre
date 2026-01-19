"""Base class for pluggable cache providers.

Cache providers handle scene-level state persistence for specific aspects
of the game (NPCs, scripts, inventory, quests, etc.). Each provider manages
its own storage and serialization format.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext


class BaseCacheProvider(ABC):
    """Base class for all cache providers.

    Cache providers persist state when transitioning between scenes and
    restore it when returning. They also support save/load serialization.

    Attributes:
        name: Unique identifier for this cache provider.
        priority: Order in which caches are processed (lower = earlier).
                 Default is 100. Use lower values for caches that others depend on.

    Example:
        @CacheRegistry.register
        class QuestCacheProvider(BaseCacheProvider):
            name = "quest"
            priority = 50  # Process before default caches

            def cache(self, scene_name, context):
                # Store quest state for this scene
                pass
    """

    name: ClassVar[str]
    priority: ClassVar[int] = 100

    @abstractmethod
    def cache(self, scene_name: str, context: GameContext) -> None:
        """Cache state before leaving a scene.

        Called by CacheLoader when transitioning away from a scene.
        The provider should extract and store relevant state from
        the game context.

        Args:
            scene_name: Name of the scene being left.
            context: Game context with access to all systems.
        """

    @abstractmethod
    def restore(self, scene_name: str, context: GameContext) -> bool:
        """Restore cached state when returning to a scene.

        Called by CacheLoader after a scene's systems are set up.
        The provider should apply any previously cached state.

        Args:
            scene_name: Name of the scene being entered.
            context: Game context with access to all systems.

        Returns:
            True if cached state was found and restored, False otherwise.
        """

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Serialize cache state for save files.

        Returns:
            Dictionary containing all cached state, suitable for JSON serialization.
        """

    @abstractmethod
    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore cache state from save file data.

        Args:
            data: Previously serialized state from to_dict().
        """

    def clear(self) -> None:  # noqa: B027
        """Clear all cached state.

        Called when starting a new game or when cache should be reset.
        Default implementation does nothing - override if needed.
        """

    def has_cached_state(self, scene_name: str) -> bool:
        """Check if a scene has cached state.

        Args:
            scene_name: Name of the scene to check.

        Returns:
            True if cached state exists for the scene.
        """
        return False
