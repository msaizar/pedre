"""Portal manager for handling map transitions via events.

This module provides a system for creating and managing portals that allow the player
to transition between different maps or scenes in the game. Portals are trigger zones
that publish events when the player enters them, allowing scripts to handle transitions
with full control over conditions, cutscenes, and effects.

The portal system consists of:
- Portal: Data class representing a single portal with its properties
- PortalManager: Coordinates portal registration and event publishing

Key features:
- Proximity-based portal activation (player must be within interaction distance)
- Event-driven transitions via PortalEnteredEvent
- Integration with Tiled map editor via custom properties
- Cooldown to prevent rapid re-triggering
- Full flexibility through script system (conditions, actions, change_scene)

Portal properties from Tiled:
- name: Unique identifier for the portal (used in script triggers)

Workflow:
1. Portals are created in Tiled map editor as objects with a name
2. During map loading, portal sprites are registered with the PortalManager
3. Each frame, the manager checks if player is near any portal
4. When player enters a portal zone, PortalEnteredEvent is published
5. Scripts respond to the event with conditions, actions, and change_scene

Integration with other systems:
- Map loading system registers portals during initialization
- EventBus receives PortalEnteredEvent when player enters portal
- Script system handles transitions via change_scene action
- Full condition system from scripts applies to portal transitions

Example Tiled setup:
    Create a portal object in the "Portals" layer with name: "forest_gate"

Example script:
    {
        "forest_gate_portal": {
            "trigger": {"event": "portal_entered", "portal": "forest_gate"},
            "actions": [
                {"type": "change_scene", "target_map": "Forest.tmx", "spawn_waypoint": "entrance"}
            ]
        }
    }

Example conditional portal:
    {
        "tower_gate_open": {
            "trigger": {"event": "portal_entered", "portal": "tower_gate"},
            "conditions": [{"check": "npc_dialog_level", "npc": "guard", "gte": 2}],
            "actions": [
                {"type": "change_scene", "target_map": "Tower.tmx", "spawn_waypoint": "entrance"}
            ]
        },
        "tower_gate_locked": {
            "trigger": {"event": "portal_entered", "portal": "tower_gate"},
            "conditions": [{"check": "npc_dialog_level", "npc": "guard", "lt": 2}],
            "actions": [
                {"type": "dialog", "speaker": "Narrator", "text": ["The gate is locked..."]}
            ]
        }
    }
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar

from pedre.systems.base import BaseSystem
from pedre.systems.portal.events import PortalEnteredEvent
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    import arcade

    from pedre.config import GameSettings
    from pedre.systems.events import EventBus
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


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


@SystemRegistry.register
class PortalManager(BaseSystem):
    """Manages portals and publishes events when player enters them.

    The PortalManager coordinates all portal-related functionality in the game. It maintains
    a registry of portals loaded from map data, checks for player proximity to portals,
    and publishes PortalEnteredEvent when the player enters a portal zone.

    The manager uses distance-based activation: portals only trigger when the player
    sprite is within the configured interaction_distance. This prevents accidental activations
    and gives players control over when to transition.

    Responsibilities:
    - Register portals from Tiled map data during map loading
    - Track all portals in the current map
    - Check player distance to each portal every frame
    - Publish PortalEnteredEvent when player enters a portal zone
    - Track which portals player is inside to only fire on entry
    - Clear portals when changing maps

    The manager does NOT handle the actual map loading/transition - it only publishes
    events. Scripts respond to PortalEnteredEvent and use change_scene action to
    trigger transitions with full control over conditions and sequences.

    Attributes:
        portals: List of all registered Portal objects in the current map.
        interaction_distance: Maximum distance in pixels for portal activation.
        event_bus: EventBus for publishing PortalEnteredEvent.
    """

    name: ClassVar[str] = "portal"
    dependencies: ClassVar[list[str]] = []

    def __init__(self) -> None:
        """Initialize portal manager with default values.

        Creates an empty portal manager ready to register portals. The interaction
        distance and event_bus are configured during setup().
        """
        self.event_bus: EventBus | None = None
        self.portals: list[Portal] = []
        self.interaction_distance: float = 64.0
        self._portals_player_inside: set[str] = set()

    def setup(self, context: GameContext, settings: GameSettings) -> None:
        """Initialize the portal system with game context and settings.

        This method is called by the SystemLoader after all systems have been
        instantiated. It configures the manager with the event bus and settings.

        Args:
            context: Game context providing access to event bus.
            settings: Game configuration containing portal_interaction_distance.
        """
        self.event_bus = context.event_bus

        if hasattr(settings, "portal_interaction_distance"):
            self.interaction_distance = settings.portal_interaction_distance

        logger.debug("PortalManager setup complete (interaction_distance=%.1f)", self.interaction_distance)

    def cleanup(self) -> None:
        """Clean up portal resources when the scene unloads.

        Clears all registered portals and resets state.
        """
        self.clear()
        logger.debug("PortalManager cleanup complete")

    def get_state(self) -> dict[str, Any]:
        """Return serializable state for saving.

        Portal state is transient and not saved.

        Returns:
            Empty dictionary as portal state is transient.
        """
        return {}

    def restore_state(self, state: dict[str, Any]) -> None:
        """Restore state from save data.

        Portal state is transient and not restored.

        Args:
            state: Previously saved state dictionary (unused).
        """

    def register_portal(self, sprite: arcade.Sprite, name: str) -> None:
        """Register a portal from Tiled map data.

        Creates a Portal object from Tiled map editor data and adds it to the manager's
        portal list. This method is called during map loading for each portal object
        found in the Tiled map.

        The portal name is used in script triggers to match specific portals.

        Tiled editor setup:
        1. Create an object in the "Portals" layer
        2. Set the object name (used as portal identifier in scripts)

        Args:
            sprite: The arcade Sprite representing the portal's location and collision area.
            name: Unique name for this portal (from Tiled object name).
        """
        portal = Portal(sprite=sprite, name=name)
        self.portals.append(portal)
        logger.info("Registered portal '%s'", name)

    def check_portals(self, player_sprite: arcade.Sprite) -> None:
        """Check if player is near any portal and publish events.

        Checks all registered portals to see if the player is within activation range.
        When the player enters a portal zone (transitions from outside to inside),
        publishes a PortalEnteredEvent that scripts can respond to.

        This method should be called every frame by the game view. It tracks which
        portals the player is currently inside to only fire events on entry, not
        while the player remains standing on a portal.

        Distance calculation uses Euclidean distance (straight-line) from player
        center to portal center. This creates a circular activation zone around
        each portal.

        Args:
            player_sprite: The player's arcade Sprite for position checking.
        """
        if not self.event_bus:
            return

        currently_inside: set[str] = set()

        for portal in self.portals:
            # Check distance
            dx = player_sprite.center_x - portal.sprite.center_x
            dy = player_sprite.center_y - portal.sprite.center_y
            distance = (dx**2 + dy**2) ** 0.5

            if distance >= self.interaction_distance:
                continue

            # Player is inside this portal zone
            currently_inside.add(portal.name)

            # Only fire event if player just entered (wasn't inside before)
            if portal.name not in self._portals_player_inside:
                logger.debug(
                    "Portal '%s': player entered (distance=%.1f, max=%.1f)",
                    portal.name,
                    distance,
                    self.interaction_distance,
                )
                self.event_bus.publish(PortalEnteredEvent(portal_name=portal.name))

        # Update tracking for next frame
        self._portals_player_inside = currently_inside

    def clear(self) -> None:
        """Clear all registered portals.

        Removes all portals from the manager's registry. This should be called when
        changing maps to ensure portals from the previous map don't persist.

        The map loading system typically calls this before loading a new map, then
        re-registers portals from the new map data.

        After calling clear(), the manager has an empty portal list and no events
        will be published until new portals are registered.
        """
        self.portals.clear()
        self._portals_player_inside.clear()
