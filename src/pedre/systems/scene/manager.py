"""Scene management system for handling scene transitions and lifecycle.

This module provides the SceneManager class, which manages the high-level state of the game
scenes, including:
- Tracking the current scene information
- Handling visual transitions (fade in/out) between scenes
- Orchestrating the loading of new maps via MapManager
- Coordinating system updates during transitions
"""

from __future__ import annotations

import logging
from enum import Enum, auto
from typing import TYPE_CHECKING, ClassVar

import arcade

from pedre.systems.base import BaseSystem
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    from pedre.config import GameSettings
    from pedre.systems.game_context import GameContext
    from pedre.systems.portal.events import PortalEnteredEvent

logger = logging.getLogger(__name__)


class TransitionState(Enum):
    """Enum for scene transition states."""

    NONE = auto()  # No transition happening
    FADING_OUT = auto()  # Fading out old scene
    LOADING = auto()  # Loading new scene (internal state)
    FADING_IN = auto()  # Fading in new scene


@SystemRegistry.register
class SceneManager(BaseSystem):
    """Manages scene transitions and lifecycle.

    Responsibilities:
    - Handle request_transition(map_file, waypoint)
    - Manage transition state machine (FADING_OUT -> LOADING -> FADING_IN -> NONE)
    - Render transition overlay
    - Trigger GameView.load_level() when screen is black
    """

    name: ClassVar[str] = "scene"
    dependencies: ClassVar[list[str]] = ["map"]

    def __init__(self) -> None:
        """Initialize the scene manager."""
        self.current_scene: str = "default"

        # Transition state
        self.transition_state: TransitionState = TransitionState.NONE
        self.transition_alpha: float = 0.0  # 0.0 = transparent, 1.0 = opaque
        self.transition_speed: float = 3.0  # Alpha change per second

        # Pending transition data
        self.pending_map_file: str | None = None
        self.pending_spawn_waypoint: str | None = None

    def setup(self, context: GameContext, settings: GameSettings) -> None:
        """Initialize with context."""
        if context.current_scene:
            self.current_scene = context.current_scene

    def request_transition(self, map_file: str, spawn_waypoint: str | None = None) -> None:
        """Request a transition to a new map.

        Args:
            map_file: The .tmx filename of the new map.
            spawn_waypoint: Optional waypoint name to spawn at.
        """
        if self.transition_state != TransitionState.NONE:
            logger.warning("Transition already in progress, ignoring request to %s", map_file)
            return

        logger.info("Starting scene transition to %s (waypoint: %s)", map_file, spawn_waypoint)
        self.pending_map_file = map_file
        self.pending_spawn_waypoint = spawn_waypoint
        self.transition_state = TransitionState.FADING_OUT
        self.transition_alpha = 0.0

    def on_draw(self, context: GameContext) -> None:
        """Draw transition overlay."""
        if self.transition_state != TransitionState.NONE:
            self._draw_transition_overlay(context)

    def _draw_transition_overlay(self, context: GameContext) -> None:
        """Draw the black fade overlay."""
        camera_manager = context.get_system("camera")
        if camera_manager:
            pass

        # Ideally we use arcade.camera.Camera2D() (default identity)
        window = arcade.get_window()
        default_cam = arcade.camera.Camera2D()
        default_cam.use()

        alpha = int(self.transition_alpha * 255)
        # alpha clamped 0-255
        alpha = max(0, min(255, alpha))

        arcade.draw_lrbt_rectangle_filled(
            0,
            window.width,
            0,
            window.height,
            (0, 0, 0, alpha),
        )

    def update(self, delta_time: float, context: GameContext) -> None:
        """Update transition state."""
        if self.transition_state == TransitionState.NONE:
            return

        if self.transition_state == TransitionState.FADING_OUT:
            self.transition_alpha += self.transition_speed * delta_time
            if self.transition_alpha >= 1.0:
                self.transition_alpha = 1.0
                self.transition_state = TransitionState.LOADING

                # Perform the map switch
                self._perform_map_switch(context)

                self.transition_state = TransitionState.FADING_IN

        elif self.transition_state == TransitionState.FADING_IN:
            self.transition_alpha -= self.transition_speed * delta_time
            if self.transition_alpha <= 0.0:
                self.transition_alpha = 0.0
                self.transition_state = TransitionState.NONE
                logger.info("Transition complete")

    def _perform_map_switch(self, context: GameContext) -> None:
        """Execute the logic to switch maps while screen is black."""
        if not self.pending_map_file:
            return

        game_view = context.game_view
        if not game_view:
            logger.error("SceneManager: No GameView in context, cannot switch map")
            return

        # Use the pending data
        map_file = self.pending_map_file
        waypoint = self.pending_spawn_waypoint

        if hasattr(game_view, "load_level"):
            game_view.load_level(map_file, waypoint)

        # Update current scene tracker
        self.current_scene = map_file.replace(".tmx", "").lower()

        # Clear pending
        self.pending_map_file = None
        self.pending_spawn_waypoint = None

    def draw_overlay(self) -> None:
        """Draw the transition overlay (called from UI phase)."""
        if self.transition_state == TransitionState.NONE:
            return

        window = arcade.get_window()
        alpha = int(self.transition_alpha * 255)
        arcade.draw_lrbt_rectangle_filled(
            0,
            window.width,
            0,
            window.height,
            (0, 0, 0, alpha),
        )


def event_handler(event: PortalEnteredEvent, context: GameContext) -> None:
    """Handle portal entry events to trigger scene transitions.

    This is a placeholder event handler for portal entry events.
    The actual transition logic is handled by the script system.
    """
