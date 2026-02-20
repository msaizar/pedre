"""Script actions for particle plugin operations.

These actions allow scripts to emit particle effects at specific
locations or following NPCs.
"""

import logging
from typing import TYPE_CHECKING, Any, Self, cast

from pedre.actions import Action
from pedre.actions.registry import ActionParseError, ActionRegistry
from pedre.types import EntityReference

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext

logger = logging.getLogger(__name__)


@ActionRegistry.register
class EmitParticlesAction(Action):
    """Emit particle effects.

    This action creates visual particle effects at a specified location. Particles can
    be emitted at an NPC's position, the player's position, or an interactive object's
    position. Available particle types include hearts, sparkles, trail, and colored bursts.

    Exactly one location parameter must be provided (npc_name, player, or interactive_object).

    Example usage:
        # Hearts at NPC location
        {
            "name": "emit_particles",
            "particle_type": "hearts",
            "npc": "yema"
        }

        # Sparkles at player location
        {
            "name": "emit_particles",
            "particle_type": "sparkles",
            "player": true
        }

        # Trail at interactive object location
        {
            "name": "emit_particles",
            "particle_type": "trail",
            "interactive_object": "waypoint"
        }

        # Burst at interactive object location with custom color
        {
            "name": "emit_particles",
            "particle_type": "burst",
            "interactive_object": "treasure_chest",
            "color": [255, 215, 0]
        }
    """

    name = "emit_particles"

    def __init__(
        self,
        particle_type: str,
        npc_name: str | None = None,
        *,
        player: bool = False,
        interactive_object: str | None = None,
        color: tuple[int, int, int] | None = None,
    ) -> None:
        """Initialize particle emission action.

        Args:
            particle_type: Type of particles (hearts, sparkles, trail, burst).
            npc_name: NPC name to emit particles at (mutually exclusive).
            player: If True, emit at player location (mutually exclusive).
            interactive_object: Interactive object name to emit at (mutually exclusive).
            color: Optional RGB color tuple to override default particle color.

        Note:
            Exactly one location parameter must be provided.
        """
        self.particle_type = particle_type
        self.npc_name = npc_name
        self.player = player
        self.interactive_object = interactive_object
        self.color = color
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Emit the particles."""
        if not self.executed:
            # Validate mutual exclusivity
            location_count = sum(
                [
                    self.npc_name is not None,
                    self.player,
                    self.interactive_object is not None,
                ]
            )

            if location_count == 0:
                logger.warning(
                    "EmitParticlesAction: No location specified. "
                    "Must provide one of: npc, player, or interactive_object"
                )
                return True

            if location_count > 1:
                logger.warning(
                    "EmitParticlesAction: Multiple locations specified. "
                    "Only one of npc, player, or interactive_object can be used"
                )
                return True

            # Determine position based on location type
            emit_x: float | None = None
            emit_y: float | None = None

            if self.player:
                player_sprite = context.player_plugin.get_player_sprite()
                if player_sprite:
                    emit_x = player_sprite.center_x
                    emit_y = player_sprite.center_y
                else:
                    logger.warning("EmitParticlesAction: Player sprite not available")
                    return True

            elif self.npc_name:
                npc_plugin = context.npc_plugin
                npc_state = npc_plugin.get_npcs().get(self.npc_name)
                if npc_state:
                    emit_x = npc_state.sprite.center_x
                    emit_y = npc_state.sprite.center_y
                else:
                    logger.warning("EmitParticlesAction: NPC '%s' not found", self.npc_name)
                    return True

            else:  # self.interactive_object
                interaction_plugin = context.interaction_plugin
                # Lowercase for case-insensitive matching
                # At this point, validation guarantees interactive_object is a string
                obj_name = cast("str", self.interactive_object).lower()
                interactive_obj = interaction_plugin.get_interactive_objects().get(obj_name)
                if interactive_obj:
                    emit_x = interactive_obj.sprite.center_x
                    emit_y = interactive_obj.sprite.center_y
                else:
                    logger.warning("EmitParticlesAction: Interactive object '%s' not found", self.interactive_object)
                    return True

            # Emit particles - emit_x and emit_y are guaranteed to be set here
            # because all paths above either set them or return early
            particle_plugin = context.particle_plugin
            if self.particle_type == "hearts":
                if self.color:
                    particle_plugin.emit_hearts(emit_x, emit_y, color=self.color)
                else:
                    particle_plugin.emit_hearts(emit_x, emit_y)
            elif self.particle_type == "sparkles":
                if self.color:
                    particle_plugin.emit_sparkles(emit_x, emit_y, color=self.color)
                else:
                    particle_plugin.emit_sparkles(emit_x, emit_y)
            elif self.particle_type == "trail":
                if self.color:
                    particle_plugin.emit_trail(emit_x, emit_y, color=self.color)
                else:
                    particle_plugin.emit_trail(emit_x, emit_y)
            elif self.particle_type == "burst":
                if self.color:
                    particle_plugin.emit_burst(emit_x, emit_y, color=self.color)
                else:
                    particle_plugin.emit_burst(emit_x, emit_y)

            self.executed = True
            logger.debug("EmitParticlesAction: Emitted %s at (%s, %s)", self.particle_type, emit_x, emit_y)

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create EmitParticlesAction from a dictionary.

        Accepts exactly one of: 'npc', 'player', or 'interactive_object'.
        Optionally accepts 'color' as a list of 3 integers [R, G, B].
        """
        color_data = data.get("color")
        color = tuple(color_data) if color_data else None

        # Validate particle_type enum
        valid_types = {"hearts", "sparkles", "trail", "burst"}
        particle_type = data.get("particle_type")
        if not particle_type:
            msg = "missing required 'particle_type' field"
            raise ActionParseError(msg)
        if not isinstance(particle_type, str):
            msg = "'particle_type' must be a string"
            raise ActionParseError(msg)
        if particle_type not in valid_types:
            msg = f"unknown particle_type '{particle_type}' (valid: {', '.join(sorted(valid_types))})"
            raise ActionParseError(msg)

        # Validate exactly one location is specified
        has_npc = "npc" in data
        has_player = data.get("player", False)
        has_object = "interactive_object" in data
        locations = sum([has_npc, bool(has_player), has_object])

        if locations == 0:
            msg = "must specify one location (npc, player, or interactive_object)"
            raise ActionParseError(msg)
        if locations > 1:
            msg = "only one location allowed (npc, player, or interactive_object)"
            raise ActionParseError(msg)

        # Type checks for location fields
        if has_npc and not isinstance(data["npc"], str):
            msg = "'npc' must be a string"
            raise ActionParseError(msg)

        if has_player and not isinstance(data["player"], bool):
            msg = "'player' must be a bool"
            raise ActionParseError(msg)

        if has_object and not isinstance(data["interactive_object"], str):
            msg = "'interactive_object' must be a string"
            raise ActionParseError(msg)

        # Type check for color
        if color_data:
            is_valid_color = (
                isinstance(color_data, list)
                and len(color_data) == 3
                and all(isinstance(c, int) and not isinstance(c, bool) for c in color_data)
            )
            if not is_valid_color:
                msg = "'color' must be a list of 3 integers"
                raise ActionParseError(msg)

        return cls(
            particle_type=particle_type,
            npc_name=data.get("npc"),
            player=data.get("player", False),
            interactive_object=data.get("interactive_object"),
            color=color,
        )

    def get_references(self) -> set[EntityReference]:
        """Extract references for validation."""
        refs = set()
        if self.npc_name:
            refs.add(EntityReference(type="npc", name=self.npc_name))
        elif self.interactive_object:
            refs.add(EntityReference(type="interactive_object", name=self.interactive_object))
        return refs
