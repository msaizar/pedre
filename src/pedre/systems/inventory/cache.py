"""Inventory cache provider for persisting inventory state."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, cast

from pedre.caches.base import BaseCacheProvider
from pedre.caches.registry import CacheRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext
    from pedre.systems.inventory import InventoryManager

logger = logging.getLogger(__name__)


@dataclass
class InventoryState:
    """State for inventory.

    Inventory is global (not per-scene), so we store a single state.

    Attributes:
        items: Dictionary mapping item IDs to acquired status.
        has_been_accessed: Whether the player has opened the inventory view.
    """

    items: dict[str, bool] = field(default_factory=dict)
    has_been_accessed: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "items": self.items,
            "has_been_accessed": self.has_been_accessed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InventoryState:
        """Create from dictionary loaded from save file."""
        return cls(
            items=dict(data.get("items", {})),
            has_been_accessed=bool(data.get("has_been_accessed", False)),
        )


@CacheRegistry.register
class InventoryCacheProvider(BaseCacheProvider):
    """Cache provider for inventory state persistence.

    Inventory is global (not per-scene), so this cache stores
    a single state rather than per-scene states.
    """

    name: ClassVar[str] = "inventory"
    priority: ClassVar[int] = 140

    def __init__(self) -> None:
        """Initialize the inventory cache provider."""
        self._state: InventoryState | None = None

    def cache(self, scene_name: str, context: GameContext) -> None:
        """Cache inventory state (ignores scene_name since inventory is global)."""
        inventory_manager = cast("InventoryManager | None", context.get_system("inventory"))
        if not inventory_manager:
            return

        self._state = InventoryState(
            items=inventory_manager.to_dict(),
            has_been_accessed=inventory_manager.has_been_accessed,
        )
        logger.debug("Cached inventory state with %d items", len(self._state.items))

    def restore(self, scene_name: str, context: GameContext) -> bool:
        """Restore inventory state (ignores scene_name since inventory is global)."""
        if not self._state:
            return False

        inventory_manager = cast("InventoryManager | None", context.get_system("inventory"))
        if not inventory_manager:
            return False

        inventory_manager.from_dict(self._state.items)
        inventory_manager.has_been_accessed = self._state.has_been_accessed

        logger.debug("Restored inventory state with %d items", len(self._state.items))
        return True

    def to_dict(self) -> dict[str, Any]:
        """Serialize inventory cache state for save files."""
        if self._state:
            return self._state.to_dict()
        return {}

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore inventory cache state from save file data."""
        if data:
            self._state = InventoryState.from_dict(data)
        else:
            self._state = None

    def clear(self) -> None:
        """Clear cached inventory state."""
        self._state = None

    def has_cached_state(self, scene_name: str) -> bool:
        """Check if inventory state is cached (ignores scene_name)."""
        return self._state is not None
