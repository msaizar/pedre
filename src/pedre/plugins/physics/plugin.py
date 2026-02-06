"""Physics plugin for handling collision detection.

This module provides the PhysicsPlugin class, which wraps the arcade physics engine
and manages collision handling between the player and walls/objects.
"""

import logging
from typing import TYPE_CHECKING, ClassVar

import arcade

from pedre.plugins.physics.base import PhysicsBasePlugin
from pedre.plugins.registry import PluginRegistry

if TYPE_CHECKING:
    from pedre.plugins.game_context import GameContext

logger = logging.getLogger(__name__)


@PluginRegistry.register
class PhysicsPlugin(PhysicsBasePlugin):
    """Manages physics engine and collision updates.

    Responsibilities:
    - Initialize PhysicsEngineSimple with player and wall list
    - Update physics engine every frame
    - Handle recreation of engine if player or walls change (optional, simpler for now)
    """

    name: ClassVar[str] = "physics"
    dependencies: ClassVar[list[str]] = ["player"]

    def __init__(self) -> None:
        """Initialize the physics plugin."""
        self.physics_engine: arcade.PhysicsEngineSimple | None = None
        self._needs_recreate: bool = True

    def setup(self, context: GameContext) -> None:
        """Initialize physics engine."""
        super().setup(context)
        self._create_engine()

    def invalidate(self) -> None:
        """Mark physics engine for recreation on next update."""
        self._needs_recreate = True

    def update(self, delta_time: float) -> None:
        """Update physics simulation."""
        if self._needs_recreate:
            self._create_engine()

        if self.physics_engine:
            self.physics_engine.update()

    def _create_engine(self) -> None:
        player_sprite = self.context.player_plugin.get_player_sprite()
        if player_sprite:
            self.physics_engine = arcade.PhysicsEngineSimple(player_sprite, self.context.scene_plugin.get_wall_list())
        self._needs_recreate = False
        logger.debug("Physics engine initialized")
