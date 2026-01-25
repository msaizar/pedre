"""Portal classes."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import arcade


@dataclass
class Portal:
    """Represents a portal/transition zone between maps.

    A Portal is a trigger zone in the game world that publishes a PortalEnteredEvent
    when the player enters it. Scripts subscribe to these events to handle transitions,
    including condition checks, cutscenes, and the actual map change.

    Portals are typically created from Tiled map objects during map loading. The sprite
    represents the physical location and collision area of the portal in the world.

    The portal name is used in script triggers to match specific portals:
        {"trigger": {"event": "portal_entered", "portal": "forest_gate"}}

    Attributes:
        sprite: The arcade Sprite representing the portal's physical location and area.
        name: Unique identifier for this portal (from Tiled object name).
    """

    sprite: arcade.Sprite
    name: str
