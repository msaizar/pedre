"""Base class for NPCManager."""

from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from pedre.systems.base import BaseSystem

if TYPE_CHECKING:
    import arcade


@dataclass
class NPCState:
    """Runtime state tracking for a single NPC.

    NPCState holds all mutable state for an NPC during gameplay, including their current
    position (via sprite), conversation progress, pathfinding data, and animation status.
    This state persists throughout the game session and is updated as the NPC moves,
    interacts with players, and performs animations.

    The state is stored separately from dialog configuration (NPCDialogConfig) to separate
    what the NPC says (static data) from what the NPC is currently doing (runtime state).

    Attributes:
        sprite: The arcade Sprite representing this NPC visually. Can be a regular Sprite
               or an AnimatedNPC with animation capabilities. Position is tracked via
               sprite.center_x and sprite.center_y.
        name: Unique identifier for this NPC (e.g., "martin", "shopkeeper"). Used for
             lookups, dialog assignment, and event tracking.
        dialog_level: Current conversation progression level (0-based). Increments as
                     player has conversations, determining which dialog text is shown.
                     Default starts at 0 for first conversation.
        path: Queue of (x, y) pixel coordinates representing the NPC's pathfinding route.
             Waypoints are popped from the front as the NPC reaches them. Empty deque
             means no active path.
        is_moving: Whether the NPC is currently traversing a path. True during movement,
                  False when stationary. NPCs cannot be interacted with while moving.
        appear_event_emitted: Tracks if NPCAppearCompleteEvent has been published for this
                            NPC. Reset when starting a new appear animation. Prevents
                            duplicate event emissions.
        disappear_event_emitted: Tracks if NPCDisappearCompleteEvent has been published.
                               Reset when starting a new disappear animation. Prevents
                               duplicate event emissions.
    """

    sprite: arcade.Sprite
    name: str
    dialog_level: int = 0
    path: deque[tuple[float, float]] = field(default_factory=deque)
    is_moving: bool = False
    appear_event_emitted: bool = False
    disappear_event_emitted: bool = False


class NPCBaseManager(BaseSystem, ABC):
    """Base class for NPCManager."""

    role = "npc_manager"

    @abstractmethod
    def get_npcs(self) -> dict[str, NPCState]:
        """Get NPCs."""
        ...

    @abstractmethod
    def load_scene_dialogs(self, scene_name: str) -> dict[str, Any]:
        """Load dialogs for a specific scene."""
        ...

    @abstractmethod
    def get_npc_by_name(self, name: str) -> NPCState | None:
        """Get NPC state by name."""
        ...

    @abstractmethod
    def move_npc_to_tile(self, npc_name: str, tile_x: int, tile_y: int) -> None:
        """Start moving an NPC to a target tile position."""
        ...

    @abstractmethod
    def has_npc_been_interacted_with(self, npc_name: str) -> bool:
        """Check if an NPC has been interacted with."""
        ...

    @abstractmethod
    def advance_dialog(self, npc_name: str) -> int:
        """Advance the dialog level for an NPC."""
        ...

    @abstractmethod
    def show_npcs(self, npc_names: list[str], wall_list: arcade.SpriteList | None = None) -> None:
        """Make hidden NPCs visible and add them to collision."""
        ...
