"""Player management system for handling player controls and state.

This module provides the PlayerManager class, which handles player spawning,
movement processing, and animation updates. It decouples the player logic
from the main GameView.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar, cast

import arcade

from pedre.constants import asset_path
from pedre.sprites import AnimatedPlayer
from pedre.systems.base import BaseSystem
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    from pedre.config import GameSettings
    from pedre.systems import DialogManager, InputManager
    from pedre.systems.game_context import GameContext
    from pedre.systems.map import MapManager

logger = logging.getLogger(__name__)


@SystemRegistry.register
class PlayerManager(BaseSystem):
    """Manages player spawning, movement, and animation.

    Responsibilities:
    - Spawn player sprite based on map data (Tiled 'Player' layer)
    - Handle player movement based on InputManager state
    - Update player animation state
    - Update GameContext with player sprite reference
    """

    name: ClassVar[str] = "player"
    dependencies: ClassVar[list[str]] = ["input"]

    def __init__(self) -> None:
        """Initialize the player manager."""
        self.player_sprite: AnimatedPlayer | None = None
        self.player_list: arcade.SpriteList | None = None

    def setup(self, context: GameContext, settings: GameSettings) -> None:
        """Initialize player system for the current scene.

        Spawns the player if a map is loaded and contains player data.
        """
        self.spawn_player(context, settings)

    def update(self, delta_time: float, context: GameContext) -> None:
        """Update player movement and animation."""
        if not self.player_sprite:
            return

        # Check if dialog is showing (blocking movement)
        dialog_manager = cast("DialogManager", context.get_system("dialog"))
        dialog_showing = dialog_manager.showing if dialog_manager else False

        # Get input manager
        input_manager = cast("InputManager", context.get_system("input"))

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

    def spawn_player(self, context: GameContext, settings: GameSettings) -> None:
        """Spawn player based on map data."""
        game_view = context.game_view
        map_manager = cast("MapManager", context.get_system("map"))
        if not map_manager or not map_manager.tile_map:
            logger.warning("No tile map available for player spawning")
            return

        tile_map = map_manager.tile_map

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

        # Check for portal spawn override
        spawn_at_portal = player_obj.properties.get("spawn_at_portal", False)
        if spawn_at_portal and game_view.spawn_waypoint:
            waypoints = context.waypoints
            if game_view.spawn_waypoint in waypoints:
                tile_x, tile_y = waypoints[game_view.spawn_waypoint]
                spawn_x = tile_x * settings.tile_size + settings.tile_size / 2
                spawn_y = tile_y * settings.tile_size + settings.tile_size / 2
                # Clear the spawn waypoint
                game_view.spawn_waypoint = None

        # Get sprite sheet properties
        sprite_sheet = player_obj.properties.get("sprite_sheet")
        tile_size = player_obj.properties.get("tile_size")

        if not sprite_sheet or not tile_size:
            logger.error("Player object missing 'sprite_sheet' or 'tile_size' properties")
            return

        sprite_sheet_path = asset_path(sprite_sheet, settings.assets_handle)

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
        if map_manager.scene:
            if "Player" in map_manager.scene:
                map_manager.scene.remove_sprite_list_by_name("Player")
            map_manager.scene.add_sprite_list("Player", sprite_list=self.player_list)

        # Update context
        context.update_player(self.player_sprite)

        # Initialize physics engine if wall list exists
        # NOTE: Physics engine creation is currently in GameView.
        # Ideally, we should trigger a physics system update here,
        # or GameView will handle it via checking context.player_sprite.
        # For now, we update context, and GameView (or PhysicsSystem) picks it up.

    def _get_animation_properties(self, properties: dict) -> dict[str, int]:
        """Extract animation properties from dictionary."""
        animation_props: dict[str, int] = {}
        if not properties:
            return animation_props

        for key in [
            "idle_up_frames",
            "idle_up_row",
            "idle_down_frames",
            "idle_down_row",
            "idle_left_frames",
            "idle_left_row",
            "idle_right_frames",
            "idle_right_row",
            "walk_up_frames",
            "walk_up_row",
            "walk_down_frames",
            "walk_down_row",
            "walk_left_frames",
            "walk_left_row",
            "walk_right_frames",
            "walk_right_row",
        ]:
            if key in properties and isinstance(properties[key], int):
                animation_props[key] = properties[key]

        return animation_props
