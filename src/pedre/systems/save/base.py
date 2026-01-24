"""Base class for SaveManager."""

from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

from pedre.systems.base import BaseSystem

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext


@dataclass
class GameSaveData:
    """Complete game save state.

    This data class represents a snapshot of the entire game state at a moment in time.
    It contains player position, current map, and all state from save providers.

    State categories:
    1. Player state: Physical location in the world
    2. World state: Which map the player is currently in
    3. Save states: All state from configured save providers
    4. Metadata: When the save was created and what format version

    The save_version field enables future migration if the save format needs to change.

    Attributes:
        player_x: Player's X position in pixel coordinates.
        player_y: Player's Y position in pixel coordinates.
        current_map: Filename of the current map (e.g., "village.tmx").
        save_states: Dictionary mapping save provider names to their serialized state.
        save_timestamp: Unix timestamp when save was created (seconds since epoch).
        save_version: Save format version string for future compatibility.
    """

    # Player state
    player_x: float
    player_y: float
    current_map: str

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
            player_x=data["player_x"],
            player_y=data["player_y"],
            current_map=data["current_map"],
            save_states=data.get("save_states", {}),
            save_timestamp=data.get("save_timestamp", 0.0),
            save_version=data.get("save_version", "2.0"),
        )


class SaveBaseManager(BaseSystem):
    """Base class for SaveManager."""

    def restore_game_data(self, save_data: GameSaveData, context: GameContext) -> None:
        """Restore all state from save data to save providers."""
        return

    def load_auto_save(self) -> GameSaveData | None:
        """Load from auto-save slot."""
        return

    def load_game(self, slot: int) -> GameSaveData | None:
        """Load game from a slot."""
        return

    def get_save_info(self, slot: int) -> dict[str, Any] | None:
        """Get basic info about a save file without fully loading it."""
        return

    def save_exists(self, slot: int) -> bool:
        """Check if a save file exists in a slot."""
        return False

    def save_game(self, slot: int, context: GameContext) -> bool:
        """Save game to a slot."""
        return False
