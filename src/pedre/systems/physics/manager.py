"""Physics system for handling collision detection.

This module provides the PhysicsManager class, which wraps the arcade physics engine
and manages collision handling between the player and walls/objects.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

import arcade

from pedre.systems.physics.base import PhysicsBaseManager
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@SystemRegistry.register
class PhysicsManager(PhysicsBaseManager):
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
        self._needs_recreate: bool = True

    def setup(self, context: GameContext) -> None:
        """Initialize physics engine."""
        self._create_engine(context)

    def invalidate(self) -> None:
        """Mark physics engine for recreation on next update."""
        self._needs_recreate = True

    def update(self, delta_time: float, context: GameContext) -> None:
        """Update physics simulation."""
        if self._needs_recreate:
            self._create_engine(context)

        if self.physics_engine:
            self.physics_engine.update()

    def _create_engine(self, context: GameContext) -> None:
        player_sprite = context.player_manager.get_player_sprite()
        if player_sprite:
            self.physics_engine = arcade.PhysicsEngineSimple(player_sprite, context.scene_manager.get_wall_list())
        self._needs_recreate = False
        logger.debug("Physics engine initialized")
