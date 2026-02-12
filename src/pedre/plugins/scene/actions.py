"""Script actions for scene plugin operations."""

import logging
from typing import TYPE_CHECKING, Any, Self

from pedre.actions import Action
from pedre.actions.registry import ActionRegistry
from pedre.types import EntityReference

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext

logger = logging.getLogger(__name__)


@ActionRegistry.register("change_scene")
class ChangeSceneAction(Action):
    """Transition to a different map/scene.

    This action triggers a map transition through the game view's scene transition
    plugin, complete with fade effects. It allows scripts to control when and where
    map transitions occur, enabling conditional portals, cutscenes before transitions,
    and complex multi-step sequences.

    The target_map should be the filename of the map to load (e.g., "Forest.tmx").
    The optional spawn_waypoint specifies where the player should appear in the new
    map. If not provided, the default spawn point from the map data is used.

    This action is typically used in response to PortalEnteredEvent, allowing scripts
    to handle portal transitions with full control over conditions and sequences.

    Example usage:
        # Simple transition
        {
            "type": "change_scene",
            "target_map": "Forest.tmx"
        }

        # Transition with specific spawn point
        {
            "type": "change_scene",
            "target_map": "Tower.tmx",
            "spawn_waypoint": "tower_entrance"
        }

        # In a portal script with dialog first
        {
            "trigger": {"event": "portal_entered", "portal": "forest_gate"},
            "actions": [
                {"type": "dialog", "speaker": "Narrator", "text": ["The gate opens..."]},
                {"type": "wait_for_dialog_close"},
                {"type": "change_scene", "target_map": "Forest.tmx", "spawn_waypoint": "entrance"}
            ]
        }
    """

    def __init__(self, target_map: str, spawn_waypoint: str | None = None) -> None:
        """Initialize scene change action.

        Args:
            target_map: Filename of the map to transition to (e.g., "Forest.tmx").
            spawn_waypoint: Optional waypoint name for player spawn position in target map.
                           If None, uses the target map's default spawn point.
        """
        self.target_map = target_map
        self.spawn_waypoint = spawn_waypoint
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Trigger the scene transition."""
        if not self.executed:
            scene_plugin = context.scene_plugin
            scene_plugin.request_transition(
                self.target_map,
                self.spawn_waypoint,
            )
            logger.debug(
                "ChangeSceneAction: Transitioning to %s (spawn: %s)",
                self.target_map,
                self.spawn_waypoint or "default",
            )
            self.executed = True

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create ChangeSceneAction from a dictionary."""
        return cls(target_map=data.get("target_map", ""), spawn_waypoint=data.get("spawn_waypoint", ""))

    @classmethod
    def validate_params(cls, data: dict[str, Any]) -> list[str]:
        """Validate change_scene action parameters.

        Returns:
            List of error messages. Empty list means valid.
        """
        errors = []
        target_map = data.get("target_map")
        if not target_map:
            errors.append("missing required 'target_map' field")
        elif not isinstance(target_map, str):
            errors.append("'target_map' must be a string")

        if "spawn_waypoint" in data and not isinstance(data["spawn_waypoint"], str):
            errors.append("'spawn_waypoint' must be a string")

        return errors

    @classmethod
    def extract_references(cls, _data: dict[str, Any]) -> list[EntityReference]:
        """Extract references for validation."""
        refs: list[EntityReference] = []

        target_map = _data.get("target_map")
        if isinstance(target_map, str):
            map_name = target_map.removesuffix(".tmx")

            # Map reference
            refs.append(
                EntityReference(
                    type="map",
                    name=map_name,
                )
            )

            spawn_waypoint = _data.get("spawn_waypoint")
            if isinstance(spawn_waypoint, str):
                refs.append(
                    EntityReference(
                        type="waypoint",
                        name=spawn_waypoint,
                        scope="map",
                        target_map=map_name,
                    )
                )

        return refs
