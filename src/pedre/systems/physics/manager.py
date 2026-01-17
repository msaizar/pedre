"""Physics system for handling collision detection.

This module provides the PhysicsManager class, which wraps the arcade physics engine
and manages collision handling between the player and walls/objects.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

import arcade

from pedre.systems.base import BaseSystem
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    from pedre.config import GameSettings
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@SystemRegistry.register
class PhysicsManager(BaseSystem):
    """Manages physics engine and collision updates.

    Responsibilities:
    - Initialize PhysicsEngineSimple with player and wall list
    - Update physics engine every frame
    - Handle recreation of engine if player or walls change (optional, simpler for now)
    """

    name: ClassVar[str] = "physics"
    dependencies: ClassVar[list[str]] = ["player"]

    def __init__(self) -> None:
        """Initialize the physics manager."""
        self.physics_engine: arcade.PhysicsEngineSimple | None = None

    def setup(self, context: GameContext, settings: GameSettings) -> None:
        """Initialize physics engine."""
        self._create_engine(context)

    def update(self, delta_time: float, context: GameContext) -> None:
        """Update physics simulation."""
        # Ensure engine is created (in case setup ran before player was ready, though dependency should prevent that)
        if not self.physics_engine and context.player_sprite and context.wall_list:
            self._create_engine(context)

        if self.physics_engine:
            self.physics_engine.update()

    def _create_engine(self, context: GameContext) -> None:
        if context.player_sprite and context.wall_list:
            self.physics_engine = arcade.PhysicsEngineSimple(context.player_sprite, context.wall_list)
            logger.debug("Physics engine initialized")
