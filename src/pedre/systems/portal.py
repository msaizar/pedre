"""Portal manager for handling map transitions.

This module provides a system for creating and managing portals that allow the player
to transition between different maps or scenes in the game. Portals are trigger zones
that activate when the player enters them, optionally checking conditions before allowing
the transition.

The portal system consists of:
- Portal: Data class representing a single portal with its properties
- PortalManager: Coordinates portal registration, activation checks, and condition validation

Key features:
- Proximity-based portal activation (player must be within interaction distance)
- Conditional portals that only activate when requirements are met
- Integration with Tiled map editor via custom properties
- Support for custom spawn points in target maps
- NPC state-based conditions (e.g., portal opens after NPC disappears)

Portal properties from Tiled:
- name: Unique identifier for the portal
- target_map: Name of the map file to transition to (required)
- spawn_waypoint: Name of waypoint in target map for player spawn (optional)
- condition_type: Type of condition to check (e.g., "npc_disappeared")
- condition_value: Value for the condition (e.g., NPC name)

Workflow:
1. Portals are created in Tiled map editor as objects with custom properties
2. During map loading, portal sprites are registered with the PortalManager
3. Each frame, the manager checks if player is near any portal
4. If player is within range and conditions are met, portal becomes active
5. Game view handles the actual map transition when portal is activated

Integration with other systems:
- Map loading system registers portals during initialization
- Game view polls get_active_portal() to detect transitions
- NPC manager provides state for conditional portals
- Waypoint system determines spawn position in target map

Example usage:
    # Create portal manager
    portal_manager = PortalManager(interaction_distance=64.0)

    # Register portal from Tiled object
    portal_manager.register_portal(
        sprite=portal_sprite,
        name="forest_entrance",
        properties={
            "target_map": "forest.tmx",
            "spawn_waypoint": "forest_start",
            "condition_type": "npc_disappeared",
            "condition_value": "guard"
        }
    )

    # Check for active portal each frame
    active_portal = portal_manager.get_active_portal(player, npc_manager)
    if active_portal:
        # Trigger map transition
        load_map(active_portal.target_map, active_portal.spawn_waypoint)
"""

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pedre.sprites import AnimatedNPC

if TYPE_CHECKING:
    import arcade

    from pedre.systems.npc import NPCManager

logger = logging.getLogger(__name__)


@dataclass
class Portal:
    """Represents a portal/transition between maps.

    A Portal is a trigger zone in the game world that initiates a map transition when
    the player enters it. Portals can be unconditional (always active) or conditional
    (requiring specific game state before activating).

    Portals are typically created from Tiled map objects during map loading. The sprite
    represents the physical location and collision area of the portal in the world.

    Conditional portals support various condition types:
    - "npc_disappeared": Portal activates after specified AnimatedNPC completes disappear animation
    - Additional condition types can be added by extending _check_conditions()

    The spawn_waypoint determines where the player appears in the target map. If not
    specified, the target map's default spawn point is used.

    Attributes:
        sprite: The arcade Sprite representing the portal's physical location and area.
        name: Unique identifier for this portal (from Tiled object name).
        target_map: Filename of the target map to load (e.g., "forest.tmx").
        spawn_waypoint: Optional waypoint name in target map for player spawn position.
                       If None, uses the target map's default spawn.
        condition_type: Optional condition type that must be met for portal to activate.
                       Currently supports "npc_disappeared".
        condition_value: Value associated with condition_type (e.g., NPC name for
                        "npc_disappeared" condition).
    """

    sprite: arcade.Sprite
    name: str
    target_map: str
    spawn_waypoint: str | None = None
    condition_type: str | None = None
    condition_value: str | None = None


class PortalManager:
    """Manages portals and map transitions.

    The PortalManager coordinates all portal-related functionality in the game. It maintains
    a registry of portals loaded from map data, checks for player proximity to portals,
    validates activation conditions, and provides information about which portal (if any)
    should trigger a map transition.

    The manager uses distance-based activation: portals only become active when the player
    sprite is within the configured interaction_distance. This prevents accidental activations
    and gives players control over when to transition.

    Responsibilities:
    - Register portals from Tiled map data during map loading
    - Track all active portals in the current map
    - Check player distance to each portal every frame
    - Validate portal activation conditions (e.g., NPC state requirements)
    - Return active portal information for map transition handling
    - Clear portals when changing maps

    The manager does NOT handle the actual map loading/transition - it only identifies
    when a portal should activate. The game view is responsible for triggering the map
    transition based on the active portal information.

    Conditional portal system:
    Portals can have conditions that must be met before activation. This enables
    progression-gated areas where players must complete certain actions (like making
    an NPC disappear) before accessing new areas.

    Attributes:
        portals: List of all registered Portal objects in the current map.
        interaction_distance: Maximum distance in pixels for portal activation.
    """

    def __init__(self, interaction_distance: float = 64.0) -> None:
        """Initialize portal manager.

        Creates an empty portal manager ready to register portals. The interaction
        distance determines how close the player must be to activate a portal.

        A typical value is 64.0 pixels (2 tiles for 32px tiles), which requires the
        player to be on or very near the portal sprite to activate it.

        Args:
            interaction_distance: Maximum distance in pixels between player and portal
                                 for activation (default 64.0).
        """
        self.portals: list[Portal] = []
        self.interaction_distance = interaction_distance

    def register_portal(self, sprite: arcade.Sprite, name: str, properties: dict) -> None:
        """Register a portal from Tiled map data.

        Creates a Portal object from Tiled map editor data and adds it to the manager's
        portal list. This method is called during map loading for each portal object
        found in the Tiled map.

        Required properties:
        - target_map: The map file to transition to (e.g., "forest.tmx")

        Optional properties:
        - spawn_waypoint: Where to spawn player in target map
        - condition_type: Type of activation condition (e.g., "npc_disappeared")
        - condition_value: Value for the condition (e.g., NPC name)

        If target_map is missing, the portal is rejected and a warning is logged.
        All other properties are optional and will be None if not specified.

        Tiled editor setup:
        1. Create an object in the "Portals" layer
        2. Set the object name (used for identification)
        3. Add custom properties with the above keys

        Args:
            sprite: The arcade Sprite representing the portal's location and collision area.
            name: Unique name for this portal (from Tiled object name).
            properties: Dictionary of custom properties from Tiled object.
        """
        target_map = properties.get("target_map")
        if not target_map:
            logger.warning("Portal '%s' missing target_map property", name)
            return

        spawn_waypoint = properties.get("spawn_waypoint")
        condition_type = properties.get("condition_type")
        condition_value = properties.get("condition_value")

        portal = Portal(
            sprite=sprite,
            name=name,
            target_map=target_map,
            spawn_waypoint=spawn_waypoint,
            condition_type=condition_type,
            condition_value=condition_value,
        )

        self.portals.append(portal)
        logger.info(
            "Registered portal '%s' -> %s (spawn: %s)",
            name,
            target_map,
            spawn_waypoint or "default",
        )

    def get_active_portal(
        self,
        player_sprite: arcade.Sprite,
        npc_manager: NPCManager | None = None,
    ) -> Portal | None:
        """Get the active portal the player is standing on.

        Checks all registered portals to see if the player is within activation range
        of any portal. For each nearby portal, validates that its activation conditions
        (if any) are met.

        This method should be called every frame by the game view to detect when the
        player enters a portal. Only one portal can be active at a time - the first
        portal found that meets all criteria is returned.

        Activation criteria:
        1. Player must be within interaction_distance of portal sprite center
        2. Portal conditions (if any) must be satisfied
        3. First matching portal is returned (portal order matters)

        Distance calculation uses Euclidean distance (straight-line) from player
        center to portal center. This creates a circular activation zone around
        each portal.

        The npc_manager parameter is required for portals with NPC-based conditions.
        If a portal has an NPC condition but npc_manager is None, that portal will
        not activate.

        Args:
            player_sprite: The player's arcade Sprite for position checking.
            npc_manager: Optional NPC manager for validating NPC-based conditions.
                        Required if any portals have "npc_disappeared" condition.

        Returns:
            The first Portal that the player is near and whose conditions are met,
            or None if no portals are active.
        """
        for portal in self.portals:
            # Check distance
            dx = player_sprite.center_x - portal.sprite.center_x
            dy = player_sprite.center_y - portal.sprite.center_y
            distance = (dx**2 + dy**2) ** 0.5

            if distance >= self.interaction_distance:
                continue

            # Only log when player is actually near a portal
            logger.debug(
                "Portal '%s': player at (%.1f, %.1f), portal at (%.1f, %.1f), distance=%.1f (max=%.1f)",
                portal.name,
                player_sprite.center_x,
                player_sprite.center_y,
                portal.sprite.center_x,
                portal.sprite.center_y,
                distance,
                self.interaction_distance,
            )

            # Check conditions
            conditions_met = self._check_conditions(portal, npc_manager)
            logger.debug("Portal '%s': conditions_met=%s", portal.name, conditions_met)

            if not conditions_met:
                continue

            return portal

        return None

    def _check_conditions(self, portal: Portal, npc_manager: NPCManager | None) -> bool:
        """Check if portal conditions are met.

        Internal method that validates whether a portal's activation conditions are satisfied.
        Different condition types require different validation logic.

        Supported condition types:
        - None: Portal is always active (no conditions)
        - "npc_disappeared": Requires an AnimatedNPC to have completed its disappear animation

        For "npc_disappeared" condition:
        - condition_value must specify the NPC name
        - NPC must exist in npc_manager
        - NPC sprite must be an AnimatedNPC (not a regular sprite)
        - AnimatedNPC.disappear_complete must be True

        This method is called internally by get_active_portal() and should not be called
        directly. It's marked as private with the _ prefix.

        Adding new condition types:
        To add a new condition type, extend this method with a new elif branch that
        checks the condition_type string and validates accordingly.

        Args:
            portal: The Portal object whose conditions to validate.
            npc_manager: NPC manager for accessing NPC state. Required for NPC-based
                        conditions, can be None for other condition types.

        Returns:
            True if the portal's conditions are met (or if it has no conditions),
            False otherwise.
        """
        if not portal.condition_type:
            logger.debug("Portal '%s': No conditions, allowing activation", portal.name)
            return True  # No conditions

        if portal.condition_type == "npc_disappeared":
            if not npc_manager:
                logger.debug("Portal '%s': No NPC manager provided", portal.name)
                return False

            if not portal.condition_value:
                logger.debug("Portal '%s': No condition_value specified", portal.name)
                return False

            npc_state = npc_manager.npcs.get(portal.condition_value)
            if not npc_state:
                logger.debug(
                    "Portal '%s': NPC '%s' not found in manager",
                    portal.name,
                    portal.condition_value,
                )
                return False

            # Check if NPC has disappear_complete attribute (animated NPCs)
            if isinstance(npc_state.sprite, AnimatedNPC):
                disappear_complete = npc_state.sprite.disappear_complete
                logger.debug(
                    "Portal '%s': NPC '%s' disappear_complete=%s",
                    portal.name,
                    portal.condition_value,
                    disappear_complete,
                )
                return disappear_complete

            logger.debug(
                "Portal '%s': NPC '%s' is not an AnimatedNPC",
                portal.name,
                portal.condition_value,
            )
            return False

        logger.warning("Unknown portal condition type: %s", portal.condition_type)
        return False

    def clear(self) -> None:
        """Clear all registered portals.

        Removes all portals from the manager's registry. This should be called when
        changing maps to ensure portals from the previous map don't persist.

        The map loading system typically calls this before loading a new map, then
        re-registers portals from the new map data.

        After calling clear(), the manager has an empty portal list and get_active_portal()
        will always return None until new portals are registered.
        """
        self.portals.clear()
