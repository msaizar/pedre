"""Player management system for handling player controls and state.

This module provides the PlayerManager class, which handles player spawning,
movement processing, and animation updates. It decouples the player logic
from the main GameView.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

import arcade

from pedre.conf import settings
from pedre.constants import BASE_ANIMATION_PROPERTIES, asset_path
from pedre.sprites import AnimatedPlayer
from pedre.systems.player.base import PlayerBaseManager
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@SystemRegistry.register
class PlayerManager(PlayerBaseManager):
    """Manages player spawning, movement, and animation.

    Responsibilities:
    - Spawn player sprite based on map data (Tiled 'Player' layer)
    - Handle player movement based on InputManager state
    - Update player animation state
    - Update GameContext with player sprite reference
    """

    name: ClassVar[str] = "player"
    dependencies: ClassVar[list[str]] = ["input", "waypoint"]

    def __init__(self) -> None:
        """Initialize the player manager."""
        self.player_sprite: AnimatedPlayer | None = None
        self.player_list: arcade.SpriteList | None = None

    def setup(self, context: GameContext) -> None:
        """Initialize player system for the current scene."""
        self.context = context

    def get_player_sprite(self) -> AnimatedPlayer | None:
        """Get the player sprite."""
        return self.player_sprite

    def load_from_tiled(
        self,
        tile_map: arcade.TileMap,
        arcade_scene: arcade.Scene,
    ) -> None:
        """Load player from Tiled map object layer."""
        # Get Player object layer
        player_layer = tile_map.object_lists.get("Player")
        if not player_layer:
            logger.warning("No 'Player' object layer found in map")
            return

        # Use first player object
        player_obj = player_layer[0]

        # Determine spawn position
        spawn_x = float(player_obj.shape[0])
        spawn_y = float(player_obj.shape[1])

        # Check for portal spawn override (defaults to True)
        spawn_at_portal = player_obj.properties.get("spawn_at_portal", True)
        next_spawn_waypoint = self.context.scene_manager.get_next_spawn_waypoint()
        logger.debug(
            "PlayerManager: spawn_at_portal=%s, next_spawn_waypoint=%s",
            spawn_at_portal,
            next_spawn_waypoint,
        )
        if spawn_at_portal and next_spawn_waypoint:
            waypoints = self.context.waypoint_manager.get_waypoints()
            logger.debug(
                "PlayerManager: Available waypoints: %s",
                list(waypoints.keys()) if waypoints else [],
            )
            if waypoints and next_spawn_waypoint in waypoints:
                tile_x, tile_y = waypoints[next_spawn_waypoint]
                spawn_x = tile_x * settings.TILE_SIZE + settings.TILE_SIZE / 2
                spawn_y = tile_y * settings.TILE_SIZE + settings.TILE_SIZE / 2
                logger.debug(
                    "PlayerManager: Spawning at waypoint '%s': tile (%d, %d) -> pixel (%.1f, %.1f), tile_size=%d",
                    next_spawn_waypoint,
                    tile_x,
                    tile_y,
                    spawn_x,
                    spawn_y,
                    settings.TILE_SIZE,
                )
                # Clear the spawn waypoint
                self.context.scene_manager.clear_next_spawn_waypoint()
            else:
                logger.warning(
                    "PlayerManager: Waypoint '%s' not found in available waypoints",
                    next_spawn_waypoint,
                )

        # Get sprite sheet properties
        sprite_sheet = player_obj.properties.get("sprite_sheet")
        tile_size = player_obj.properties.get("tile_size")

        if not sprite_sheet or not tile_size:
            logger.error("Player object missing 'sprite_sheet' or 'tile_size' properties")
            return

        sprite_sheet_path = asset_path(sprite_sheet, settings.ASSETS_HANDLE)

        # Helper to extract animation props
        anim_props = self._get_animation_properties(player_obj.properties)

        # Create sprite
        self.player_sprite = AnimatedPlayer(
            sprite_sheet_path,
            tile_size=tile_size,
            columns=12,
            scale=1.0,
            center_x=spawn_x,
            center_y=spawn_y,
            **anim_props,
        )

        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player_sprite)

        # Add to scene
        if arcade_scene:
            if "Player" in arcade_scene:
                arcade_scene.remove_sprite_list_by_name("Player")
            arcade_scene.add_sprite_list("Player", sprite_list=self.player_list)

        logger.info("Player loaded at (%.1f, %.1f)", spawn_x, spawn_y)

    def update(self, delta_time: float) -> None:
        """Update player movement and animation."""
        if not self.player_sprite:
            return

        # Check if dialog is showing (blocking movement)
        dialog_manager = self.context.dialog_manager
        dialog_showing = dialog_manager.is_showing() if dialog_manager else False

        # Get input manager
        input_manager = self.context.input_manager

        # Determine movement
        dx, dy = 0.0, 0.0
        moving = False

        if input_manager and not dialog_showing:
            dx, dy = input_manager.get_movement_vector()
            moving = dx != 0 or dy != 0

        # Apply movement
        self.player_sprite.change_x = dx
        self.player_sprite.change_y = dy

        # Update direction state logic
        if isinstance(self.player_sprite, AnimatedPlayer):
            # Determine direction based on movement
            new_direction = self.player_sprite.current_direction

            if dx > 0:
                new_direction = "right"
            elif dx < 0:
                new_direction = "left"
            elif dy > 0:
                new_direction = "up"
            elif dy < 0:
                new_direction = "down"

            # Only change direction when it actually changes
            if new_direction != self.player_sprite.current_direction:
                self.player_sprite.set_direction(new_direction)

            # Update animation
            self.player_sprite.update_animation(delta_time, moving=moving)

    def get_save_state(self) -> dict[str, Any]:
        """Get save state."""
        return self.to_dict()

    def restore_save_state(self, state: dict[str, Any]) -> None:
        """Phase 1: No metadata to restore for player."""

    def apply_entity_state(self, state: dict[str, Any]) -> None:
        """Phase 2: Apply saved player position after sprite exists."""
        self.from_dict(state)
        if self.player_sprite and "player_x" in state:
            logger.info(
                "Applied saved player position (%.1f, %.1f)",
                self.player_sprite.center_x,
                self.player_sprite.center_y,
            )

    def reset(self) -> None:
        """Reset player manager state for new game."""
        self.player_sprite = None
        self.player_list = None

    def from_dict(self, data: dict[str, float]) -> None:
        """Apply position to sprite if it exists."""
        if "player_x" not in data or "player_y" not in data:
            return
        if self.player_sprite:
            self.player_sprite.center_x = float(data["player_x"])
            self.player_sprite.center_y = float(data["player_y"])

    def to_dict(self) -> dict[str, float]:
        """Load player coordinates from saved dictionary data."""
        if self.player_sprite:
            return {"player_x": self.player_sprite.center_x, "player_y": self.player_sprite.center_y}
        return {}

    def _get_animation_properties(self, properties: dict) -> dict[str, int]:
        """Extract animation properties from dictionary."""
        animation_props: dict[str, int] = {}
        if not properties:
            return animation_props

        for key in BASE_ANIMATION_PROPERTIES:
            if key in properties and isinstance(properties[key], int):
                animation_props[key] = properties[key]

        return animation_props
