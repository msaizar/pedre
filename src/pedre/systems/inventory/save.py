"""Inventory save provider for persisting inventory state."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, cast

from pedre.saves.base import BaseSaveProvider
from pedre.saves.registry import SaveRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext
    from pedre.systems.inventory import InventoryManager

logger = logging.getLogger(__name__)


@dataclass
class InventoryState:
    """State for inventory.

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


@SaveRegistry.register
class InventorySaveProvider(BaseSaveProvider):
    """Save provider for inventory state persistence."""

    name: ClassVar[str] = "inventory"
    priority: ClassVar[int] = 140

    def __init__(self) -> None:
        """Initialize the inventory save provider."""
        self._state: InventoryState | None = None

    def gather(self, context: GameContext) -> None:
        """Gather inventory state from the inventory manager."""
        inventory_manager = cast("InventoryManager | None", context.get_system("inventory"))
        if not inventory_manager:
            return

        self._state = InventoryState(
            items=inventory_manager.to_dict(),
            has_been_accessed=inventory_manager.has_been_accessed,
        )
        logger.debug("Gathered inventory state with %d items", len(self._state.items))

    def restore(self, context: GameContext) -> bool:
        """Restore inventory state to the inventory manager."""
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
        """Serialize inventory state for save files."""
        if self._state:
            return self._state.to_dict()
        return {}

    def from_dict(self, data: dict[str, Any]) -> None:
        """Restore inventory state from save file data."""
        if data:
            self._state = InventoryState.from_dict(data)
        else:
            self._state = None

    def clear(self) -> None:
        """Clear cached inventory state."""
        self._state = None
