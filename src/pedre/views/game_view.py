"""Main gameplay view for the game.

This module provides the GameView class.

Key responsibilities:
- Load and render Tiled maps with layers (floor, walls, NPCs, interactive objects)
- Initialize and coordinate all game systems (managers for dialog, NPCs, audio, etc.)
- Handle player input and movement with physics

Example usage:
    # Create and show game view
    view_manager = ViewManager(window)
    game_view = GameView(view_manager)
    view_manager.show_view(game_view)

    # Game loop happens automatically via arcade.View callbacks:
    # - on_update() called each frame
    # - on_draw() renders the game
    # - on_key_press/release() handle input
"""

import logging
from typing import TYPE_CHECKING

import arcade

from pedre.conf import settings
from pedre.systems.scene import TransitionState

if TYPE_CHECKING:
    from pedre.view_manager import ViewManager


logger = logging.getLogger(__name__)


class GameView(arcade.View):
    """Main gameplay view coordinating all game systems.

    The GameView is the primary view during active gameplay. It loads Tiled maps, initializes
    all game systems (managers), handles player input, updates game logic, and renders the
    game world. It serves as the central integration point for all gameplay functionality.

    The view follows arcade's View pattern with lifecycle callbacks:
    - on_show_view(): Called when becoming active
    - on_update(): Called each frame to update game logic
    - on_draw(): Called each frame to render
    - on_key_press/release(): Handle keyboard input
    - cleanup(): Called before transitioning away

    Architecture highlights:
    - Lazy initialization: setup() is called on first show, not in __init__

    Instance attributes:
        view_manager: Reference to ViewManager for view transitions.

        State tracking:
        initialized: Whether setup() has been called.
    """

    def __init__(self, view_manager: ViewManager) -> None:
        """Initialize the game view.

        Initializes state, but does NOT load the map yet. Actual setup happens in setup() when the view is first shown.

        This lazy initialization pattern allows the view to be created without immediately
        loading heavy assets, and enables the map to be changed before setup() runs.

        Args:
            view_manager: ViewManager instance for handling view transitions (menu, inventory, etc.).
        """
        super().__init__()
        self.view_manager = view_manager

        # Track if game has been initialized
        self.initialized: bool = False

    def setup(self) -> None:
        """Set up the game. Called on first show or when resetting the game state.

        For new games, loads the initial map from settings. For loaded games,
        loads the map that was stored in current_map by save game restoration.
        """
        scene_manager = self.view_manager.game_context.scene_manager

        # Get the map to load (either from saved state or initial map)
        current_map = scene_manager.get_current_map()

        if current_map:
            # Map name was restored from save game - load this map
            logger.info("Loading saved map from save game: %s", current_map)
            scene_manager.load_level(current_map, initial=True)
        else:
            # No map loaded yet - this is a new game, load the initial map
            logger.info("Loading initial map for new game: %s", settings.INITIAL_MAP)
            scene_manager.load_level(settings.INITIAL_MAP, initial=True)

    def on_show_view(self) -> None:
        """Called when this view becomes active (arcade lifecycle callback).

        Handles first-time initialization and displays the initial game dialog. Only runs
        setup() and intro sequence on the first call (when initialized is False).

        Side effects:
            - Sets background color to black
            - Calls setup() if not yet initialized
            - Sets initialized flag to True
        """
        arcade.set_background_color(arcade.color.BLACK)

        # Only run setup and intro sequence on first show
        if not self.initialized:
            self.setup()
            self.initialized = True

    def on_update(self, delta_time: float) -> None:
        """Update game logic each frame (arcade lifecycle callback).

        Called automatically by arcade each frame. Updates all game systems in order.
        """
        if not self.view_manager.game_context:
            return

        # Handle scene transitions
        scene_manager = self.view_manager.game_context.scene_manager
        if scene_manager and scene_manager.get_transition_state() != TransitionState.NONE:
            scene_manager.update(delta_time)
            # During transition, skip other game logic
            return

        # Update ALL systems generically via system_loader
        self.view_manager.system_loader.update_all(delta_time)

    def on_draw(self) -> None:
        """Render the game world (arcade lifecycle callback).

        Draws all game elements in proper order with camera transformations.
        """
        self.clear()

        if not self.view_manager.game_context:
            return

        # Activate game camera for world rendering
        camera_manager = self.view_manager.game_context.camera_manager
        if camera_manager:
            camera_manager.use()

        # Draw ALL systems (world coordinates) via system_loader
        self.view_manager.system_loader.draw_all()

        # Draw UI in screen coordinates
        arcade.camera.Camera2D().use()

        # Draw ALL systems (screen coordinates) via system_loader
        self.view_manager.system_loader.draw_ui_all()

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        """Handle key presses (arcade lifecycle callback).

        Processes keyboard input. Most input handling is delegated to specific systems
        via the SystemLoader. This view handles global hotkeys (like menus).
        """
        if not self.view_manager.system_loader:
            return None

        # Delegate to systems first (e.g., Dialog might consume input)
        if self.view_manager.system_loader.on_key_press_all(symbol, modifiers):
            return True

        return None

    def on_key_release(self, symbol: int, modifiers: int) -> bool | None:
        """Handle key releases (arcade lifecycle callback)."""
        if self.view_manager.system_loader:
            self.view_manager.system_loader.on_key_release_all(symbol, modifiers)
        return None

    def cleanup(self) -> None:
        """Clean up resources when transitioning away from this view.

        Performs cleanup including
        resetting managers, and clearing the initialized flag. Called before switching
        to another view (menu, inventory, etc.).

        Cleanup process:
            - Clear all managers
            - Reset initialized flag so game will set up again on next show

        Side effects:
            - Resets all managers to empty state
            - Sets initialized = False
        """
        # Cache state for this scene before clearing (for scene transitions)
        scene_manager = self.view_manager.game_context.scene_manager
        current_map = scene_manager.get_current_map()

        if current_map:
            cache_manager = scene_manager.get_cache_manager()
            if cache_manager:
                cache_manager.cache_scene(current_map, self.view_manager.game_context)

        # Reset ALL pluggable systems generically (clears session state but keeps wiring)
        self.view_manager.system_loader.reset_all()

        # Reset initialization flag so game will be set up again on next show
        self.initialized = False
