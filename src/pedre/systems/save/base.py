"""Base class for SaveManager."""

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any

from pedre.systems.base import BaseSystem


@dataclass
class GameSaveData:
    """Complete game save state.

    This data class represents a snapshot of the entire game state at a moment in time.
    It contains player position, current map, and all state from save providers.

    State categories:
    3. Save states: All state from configured save providers
    4. Metadata: When the save was created and what format version

    The save_version field enables future migration if the save format needs to change.

    Attributes:
        save_states: Dictionary mapping save provider names to their serialized state.
        save_timestamp: Unix timestamp when save was created (seconds since epoch).
        save_version: Save format version string for future compatibility.
    """

    # All state from save providers
    save_states: dict[str, Any] = field(default_factory=dict)

    # Metadata
    save_timestamp: float = 0.0
    save_version: str = "2.0"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation with all save data fields as key-value pairs.
        """
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GameSaveData:
        """Create from dictionary loaded from JSON.

        Args:
            data: Dictionary loaded from JSON save file.

        Returns:
            New GameSaveData instance with values from the dictionary.
        """
        return cls(
            save_states=data.get("save_states", {}),
            save_timestamp=data.get("save_timestamp", 0.0),
            save_version=data.get("save_version", "2.0"),
        )


class SaveBaseManager(BaseSystem, ABC):
    """Base class for SaveManager."""

    role = "save_manager"

    @abstractmethod
    def restore_game_data(self, save_data: GameSaveData) -> None:
        """Restore all state from save data to save providers."""
        ...

    @abstractmethod
    def load_auto_save(self) -> GameSaveData | None:
        """Load from auto-save slot."""
        ...

    @abstractmethod
    def load_game(self, slot: int) -> GameSaveData | None:
        """Load game from a slot."""
        ...

    @abstractmethod
    def get_save_info(self, slot: int) -> dict[str, Any] | None:
        """Get basic info about a save file without fully loading it."""
        ...

    @abstractmethod
    def save_exists(self, slot: int) -> bool:
        """Check if a save file exists in a slot."""
        ...

    @abstractmethod
    def save_game(self, slot: int) -> bool:
        """Save game to a slot."""
        ...

    @abstractmethod
    def apply_entity_states(self) -> None:
        """Phase 2: Apply entity-specific state after sprites exist."""
        ...
