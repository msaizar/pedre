"""Script actions for particle system operations.

These actions allow scripts to emit particle effects at specific
locations or following NPCs.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self, cast

from pedre.actions import Action
from pedre.actions.registry import ActionRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext
    from pedre.systems.interaction.manager import InteractionBaseManager
    from pedre.systems.npc.base import NPCBaseManager
    from pedre.systems.particle.manager import ParticleManager

logger = logging.getLogger(__name__)


@ActionRegistry.register("emit_particles")
class EmitParticlesAction(Action):
    """Emit particle effects.

    This action creates visual particle effects at a specified location. Particles can
    be emitted at an NPC's position, the player's position, or an interactive object's
    position. Available particle types include hearts, sparkles, and colored bursts.

    Exactly one location parameter must be provided (npc_name, player, or interactive_object).

    Example usage:
        # Hearts at NPC location
        {
            "type": "emit_particles",
            "particle_type": "hearts",
            "npc": "yema"
        }

        # Sparkles at player location
        {
            "type": "emit_particles",
            "particle_type": "sparkles",
            "player": true
        }

        # Burst at interactive object location
        {
            "type": "emit_particles",
            "particle_type": "burst",
            "interactive_object": "treasure_chest"
        }
    """

    def __init__(
        self,
        particle_type: str,
        npc_name: str | None = None,
        *,
        player: bool = False,
        interactive_object: str | None = None,
    ) -> None:
        """Initialize particle emission action.

        Args:
            particle_type: Type of particles (hearts, sparkles, burst).
            npc_name: NPC name to emit particles at (mutually exclusive).
            player: If True, emit at player location (mutually exclusive).
            interactive_object: Interactive object name to emit at (mutually exclusive).

        Note:
            Exactly one location parameter must be provided.
        """
        self.particle_type = particle_type
        self.npc_name = npc_name
        self.player = player
        self.interactive_object = interactive_object
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
                if context.player_sprite:
                    emit_x = context.player_sprite.center_x
                    emit_y = context.player_sprite.center_y
                else:
                    logger.warning("EmitParticlesAction: Player sprite not available")
                    return True

            elif self.npc_name:
                npc_manager = cast("NPCBaseManager", context.get_system("npc"))
                if npc_manager:
                    npc_state = npc_manager.npcs.get(self.npc_name)
                    if npc_state:
                        emit_x = npc_state.sprite.center_x
                        emit_y = npc_state.sprite.center_y
                    else:
                        logger.warning("EmitParticlesAction: NPC '%s' not found", self.npc_name)
                        return True
                else:
                    logger.warning("EmitParticlesAction: NPC system not available")
                    return True

            elif self.interactive_object:
                interaction_manager = cast("InteractionBaseManager", context.get_system("interaction"))
                if interaction_manager:
                    # Lowercase for case-insensitive matching
                    obj_name = self.interactive_object.lower()
                    interactive_obj = interaction_manager.get_interactive_objects().get(obj_name)
                    if interactive_obj:
                        emit_x = interactive_obj.sprite.center_x
                        emit_y = interactive_obj.sprite.center_y
                    else:
                        logger.warning(
                            "EmitParticlesAction: Interactive object '%s' not found", self.interactive_object
                        )
                        return True
                else:
                    logger.warning("EmitParticlesAction: Interaction system not available")
                    return True

            # Emit particles
            if emit_x is not None and emit_y is not None:
                particle_manager = cast("ParticleManager", context.get_system("particle"))
                if particle_manager:
                    if self.particle_type == "hearts":
                        particle_manager.emit_hearts(emit_x, emit_y)
                    elif self.particle_type == "sparkles":
                        particle_manager.emit_sparkles(emit_x, emit_y)
                    elif self.particle_type == "burst":
                        particle_manager.emit_burst(emit_x, emit_y, color=(255, 215, 0))

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
        """
        return cls(
            particle_type=data.get("particle_type", "burst"),
            npc_name=data.get("npc"),
            player=data.get("player", False),
            interactive_object=data.get("interactive_object"),
        )
