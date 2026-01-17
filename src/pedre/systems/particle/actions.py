"""Script actions for particle system operations.

These actions allow scripts to emit particle effects at specific
locations or following NPCs.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Self

from pedre.systems.action_registry import ActionRegistry
from pedre.systems.actions import Action

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@ActionRegistry.register("emit_particles")
class EmitParticlesAction(Action):
    """Emit particle effects.

    This action creates visual particle effects at a specified location. Particles can
    be emitted at fixed coordinates or follow an NPC's position. Available particle types
    include hearts, sparkles, and colored bursts.

    When using npc_name, the particles will be emitted at the NPC's current center position,
    which is useful for effects that should appear on or around a character.

    Example usage:
        # Fixed position burst
        {
            "type": "emit_particles",
            "particle_type": "burst",
            "x": 512,
            "y": 384
        }

        # Hearts around an NPC
        {
            "type": "emit_particles",
            "particle_type": "hearts",
            "npc": "yema"
        }
    """

    def __init__(
        self,
        particle_type: str,
        x: float | None = None,
        y: float | None = None,
        npc_name: str | None = None,
    ) -> None:
        """Initialize particle emission action.

        Args:
            particle_type: Type of particles (hearts, sparkles, burst).
            x: X coordinate (if not using NPC position).
            y: Y coordinate (if not using NPC position).
            npc_name: NPC name to emit particles at (overrides x, y).
        """
        self.particle_type = particle_type
        self.x = x
        self.y = y
        self.npc_name = npc_name
        self.executed = False

    def execute(self, context: GameContext) -> bool:
        """Emit the particles."""
        if not self.executed:
            # Determine position
            emit_x = self.x
            emit_y = self.y

            if self.npc_name:
                npc_state = context.npc_manager.npcs.get(self.npc_name)
                if npc_state:
                    emit_x = npc_state.sprite.center_x
                    emit_y = npc_state.sprite.center_y

            if emit_x is None or emit_y is None:
                logger.warning("EmitParticlesAction: No valid position to emit particles")
                return True

            # Emit particles
            if self.particle_type == "hearts":
                context.particle_manager.emit_hearts(emit_x, emit_y)
            elif self.particle_type == "sparkles":
                context.particle_manager.emit_sparkles(emit_x, emit_y)
            elif self.particle_type == "burst":
                context.particle_manager.emit_burst(emit_x, emit_y, color=(255, 215, 0))

            self.executed = True
            logger.debug("EmitParticlesAction: Emitted %s at (%s, %s)", self.particle_type, emit_x, emit_y)

        return True

    def reset(self) -> None:
        """Reset the action."""
        self.executed = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        """Create EmitParticlesAction from a dictionary."""
        return cls(
            particle_type=data.get("particle_type", "burst"),
            x=data.get("x"),
            y=data.get("y"),
            npc_name=data.get("npc"),
        )
