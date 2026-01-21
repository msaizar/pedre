"""Main gameplay view for the game.

This module provides the GameView class, which serves as the central hub for all gameplay
systems during active play. It coordinates map loading, player control, NPC interactions,
dialog systems, scripting, physics, rendering, and save/load functionality.

Key responsibilities:
- Load and render Tiled maps with layers (floor, walls, NPCs, interactive objects)
- Initialize and coordinate all game systems (managers for dialog, NPCs, audio, etc.)
- Handle player input and movement with physics
- Process NPC pathfinding and animations
- Manage dialog sequences and scripted events via the event bus
- Handle portal transitions between maps
- Provide save/load functionality (quick save/load)
- Render game world with smooth camera following
- Draw debug information when enabled

System architecture:
The GameView orchestrates multiple manager classes that handle specific subsystems:
- ScriptManager: Executes scripted sequences from JSON
- AudioManager: Plays music and sound effects
- SaveManager: Handles game state persistence
- CameraManager: Smooth camera following

Map loading workflow:
1. Load Tiled .tmx file and extract layers (walls, NPCs, objects, waypoints, portals)
2. Create animated player sprite at spawn position
3. Replace static NPC sprites with AnimatedNPC instances
4. Register NPCs, portals, and interactive objects with their managers
5. Load scene-specific scripts and NPC dialogs
6. Initialize physics engine and camera
7. Create GameContext to provide managers to scripts

Event-driven scripting:
The view integrates with the event bus to enable reactive scripting. When game events
occur (dialog closed, NPC interacted, etc.), scripts can automatically trigger to
create dynamic cutscenes and story progression.

Example usage:
    # Create and show game view
    view_manager = ViewManager(window)
    game_view = GameView(view_manager, map_file="Casa.tmx", debug_mode=False)
    view_manager.show_view(game_view)

    # Game loop happens automatically via arcade.View callbacks:
    # - on_update() called each frame
    # - on_draw() renders the game
    # - on_key_press/release() handle input
"""

import logging
from typing import TYPE_CHECKING, cast

import arcade

from pedre.systems.scene import TransitionState

# These imports are used for cast() type annotations only
if TYPE_CHECKING:
    from pedre.systems import (
        CameraManager,
        SceneManager,
    )
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
    - Per-scene loading: Each map loads its own dialog and script files only when needed
    - Dialog caching: Dialog files cached per-scene to avoid reloading when returning
    - Event-driven: Uses EventBus for decoupled communication between systems
    - State tracking: Maintains current NPC interaction, scene name, portal spawn points

    Class attributes:
        _dialog_cache: Per-scene dialog cache {scene_name: dialog_data} shared across all
                      GameView instances to avoid reloading when transitioning between maps.
        _script_cache: Per-scene script JSON cache {scene_name: script_json_data} shared
                      across all GameView instances to avoid reloading when returning to scenes.

    Instance attributes:
        view_manager: Reference to ViewManager for view transitions.
        map_file: Current Tiled map filename (e.g., "Casa.tmx").
        debug_mode: Whether to display debug overlays (NPC positions, etc.).

        State tracking:
        spawn_waypoint: Waypoint to spawn at (set by portals).
        initialized: Whether setup() has been called.
    """

    def __init__(
        self,
        view_manager: ViewManager,
        map_file: str | None = None,
    ) -> None:
        """Initialize the game view.

        Creates all manager instances and initializes state, but does NOT load the map
        or set up sprites yet. Actual setup happens in setup() when the view is first shown.

        This lazy initialization pattern allows the view to be created without immediately
        loading heavy assets, and enables the map_file to be changed before setup() runs.

        Args:
            view_manager: ViewManager instance for handling view transitions (menu, inventory, etc.).
            map_file: Name of the Tiled .tmx file to load from assets/maps/. If None, uses INITIAL_MAP from config.
        """
        super().__init__()
        self.view_manager = view_manager
        self.map_file = map_file

        # Portal tracking (deprecated - now using context.next_spawn_waypoint)
        self.spawn_waypoint: str | None = None

        # Track if game has been initialized
        self.initialized: bool = False

    def setup(self) -> None:
        """Set up the game. Called on first show or when resetting the game state."""
        # Load the initial map
        target_map = self.map_file or self.window.settings.initial_map
        if target_map and self.view_manager.game_context:
            scene_manager = cast("SceneManager", self.view_manager.game_context.get_system("scene"))
            if scene_manager:
                scene_manager.load_level(target_map, self.spawn_waypoint, self.view_manager.game_context)

    def on_show_view(self) -> None:
        """Called when this view becomes active (arcade lifecycle callback).

        Handles first-time initialization and displays the initial game dialog. Only runs
        setup() and intro sequence on the first call (when initialized is False).

        Side effects:
            - Sets background color to black
            - Calls setup() if not yet initialized
            - Plays background music
            - Shows initial dialog
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
        scene_manager = cast("SceneManager", self.view_manager.game_context.get_system("scene"))
        if scene_manager and scene_manager.transition_state != TransitionState.NONE:
            scene_manager.update(delta_time, self.view_manager.game_context)
            # During transition, skip other game logic
            return

        # Update ALL systems generically via system_loader
        self.view_manager.system_loader.update_all(delta_time, self.view_manager.game_context)

    def on_draw(self) -> None:
        """Render the game world (arcade lifecycle callback).

        Draws all game elements in proper order with camera transformations.
        """
        self.clear()

        if not self.view_manager.game_context:
            return

        # Activate game camera for world rendering
        camera_manager = cast("CameraManager", self.view_manager.game_context.get_system("camera"))
        if camera_manager:
            camera_manager.use()

        # Draw ALL systems (world coordinates) via system_loader
        self.view_manager.system_loader.draw_all(self.view_manager.game_context)

        # Draw UI in screen coordinates
        arcade.camera.Camera2D().use()

        # Draw ALL systems (screen coordinates) via system_loader
        self.view_manager.system_loader.draw_ui_all(self.view_manager.game_context)

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        """Handle key presses (arcade lifecycle callback).

        Processes keyboard input. Most input handling is delegated to specific systems
        via the SystemLoader. This view handles global hotkeys (like menus).
        """
        if not self.view_manager.system_loader or not self.view_manager.game_context:
            return None

        # Delegate to systems first (e.g., Dialog might consume input)
        if self.view_manager.system_loader.on_key_press_all(symbol, modifiers, self.view_manager.game_context):
            return True

        return None

    def on_key_release(self, symbol: int, modifiers: int) -> bool | None:
        """Handle key releases (arcade lifecycle callback)."""
        if self.view_manager.system_loader and self.view_manager.game_context:
            self.view_manager.system_loader.on_key_release_all(symbol, modifiers, self.view_manager.game_context)
        return None

    def cleanup(self) -> None:
        """Clean up resources when transitioning away from this view.

        Performs cleanup including auto-save, stopping audio, clearing sprite lists,
        resetting managers, and clearing the initialized flag. Called before switching
        to another view (menu, inventory, etc.).

        Cleanup process:
            - Stop background music
            - Clear all sprite lists
            - Clear sprite references
            - Clear all managers
            - Reset initialized flag so game will set up again on next show

        Side effects:
            - Stops audio playback
            - Clears all sprite lists and references
            - Resets all managers to empty state
            - Sets initialized = False
        """
        # Cache state for this scene before clearing (for scene transitions)
        scene_manager = (
            cast("SceneManager", self.view_manager.game_context.get_system("scene"))
            if self.view_manager.game_context
            else None
        )
        current_map = getattr(scene_manager, "current_map", "") if scene_manager else ""

        if current_map and scene_manager and self.view_manager.game_context:
            cache_manager = scene_manager.get_cache_manager()
            if cache_manager:
                cache_manager.cache_scene(current_map, self.view_manager.game_context)

        # Cleanup ALL pluggable systems generically (includes AudioManager cleanup)
        self.view_manager.system_loader.cleanup_all()

        # Reset initialization flag so game will be set up again on next show
        self.initialized = False
