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
- DialogManager: Shows and manages dialog boxes
- NPCManager: Tracks NPC state, dialog levels, and movement
- InputManager: Processes keyboard input for movement
- ScriptManager: Executes scripted sequences from JSON
- PortalManager: Handles map transitions via portals
- InteractionManager: Manages interactive objects
- AudioManager: Plays music and sound effects
- ParticleManager: Renders visual effects
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

from pedre.systems import (
    EventBus,
    GameContext,
    SystemLoader,
)
from pedre.systems.scene import TransitionState

# These imports are used for cast() type annotations only
if TYPE_CHECKING:
    from pedre.config import GameSettings
    from pedre.systems import (
        SceneManager,
    )
    from pedre.view_manager import ViewManager

from pedre.systems.events import (
    GameStartEvent,
)

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

        Game systems (managers):
        dialog_manager: Manages dialog display and pagination.
        pathfinding_manager: Handles NPC A* pathfinding.
        inventory_manager: Tracks player's inventory.
        event_bus: Pub/sub system for game events.
        script_manager: Loads and executes scripted sequences.
        npc_manager: Manages NPC state, dialogs, and movement.
        interaction_manager: Handles interactive objects.
        portal_manager: Manages map transitions via portals.
        camera_manager: Smooth camera following.
        save_manager: Game state persistence.
        audio_manager: Music and sound effects.
        particle_manager: Visual effects.
        game_context: Bundle of managers passed to scripts.

        Sprite lists and rendering:
        player_sprite: The player's AnimatedPlayer sprite.
        player_list: Arcade sprite list containing player.
        wall_list: All collidable sprites (walls + solid NPCs).
        npc_list: All NPC sprites.
        tile_map: Loaded Tiled map data.
        scene: Arcade Scene generated from tile map.
        physics_engine: Simple physics for player collision.
        camera: 2D camera for scrolling.

        State tracking:
        current_npc_name: Name of NPC currently in dialog.
        current_npc_dialog_level: Dialog level when dialog was opened.
        current_scene: Scene name (lowercase map file without .tmx).
        spawn_waypoint: Waypoint to spawn at (set by portals).
        initialized: Whether setup() has been called.
    """

    def __init__(
        self,
        view_manager: ViewManager,
        map_file: str | None = None,
        *,
        settings: GameSettings | None = None,
    ) -> None:
        """Initialize the game view.

        Creates all manager instances and initializes state, but does NOT load the map
        or set up sprites yet. Actual setup happens in setup() when the view is first shown.

        This lazy initialization pattern allows the view to be created without immediately
        loading heavy assets, and enables the map_file to be changed before setup() runs.

        Args:
            view_manager: ViewManager instance for handling view transitions (menu, inventory, etc.).
            map_file: Name of the Tiled .tmx file to load from assets/maps/. If None, uses INITIAL_MAP from config.
            settings: Game settings. If None, will be retrieved from window.
        """
        super().__init__()
        self.view_manager = view_manager
        self.map_file = map_file
        self.settings = settings

        # Game systems (will be loaded by SystemLoader)
        self.system_loader: SystemLoader | None = None
        self.game_context: GameContext | None = None

        # Event-driven scripting system (created early so it can be passed to context)
        self.event_bus = EventBus()

        # Camera for scrolling
        self.camera: arcade.camera.Camera2D | None = None

        # Portal tracking
        self.spawn_waypoint: str | None = None

        # Track if game has been initialized
        self.initialized: bool = False

    def setup(self) -> None:
        """Set up the game. Called on first show or when resetting the game state."""
        # Ensure systems are initialized
        if not hasattr(self, "system_loader") or not self.system_loader:
            self._init_systems()

        # Load the initial map
        target_map = self.map_file or self.settings.initial_map
        if target_map and self.game_context:
            scene_manager = cast("SceneManager", self.game_context.get_system("scene"))
            if scene_manager:
                scene_manager.load_level(target_map, self.spawn_waypoint, self.game_context)

    def _init_systems(self) -> None:
        """Initialize all game systems (run once)."""
        if self.settings is None:
            self.settings = self.window.settings

        # Initialize pluggable systems via SystemLoader
        self.system_loader = SystemLoader(self.settings)
        system_instances = self.system_loader.instantiate_all()

        # Initialize GameContext
        self.game_context = GameContext(
            event_bus=self.event_bus,
            wall_list=arcade.SpriteList(),
            player_sprite=None,
            game_view=self,
            current_scene="default",
            waypoints={},
            interacted_objects=set(),
        )

        for name, system in system_instances.items():
            self.game_context.register_system(name, system)

        # Setup all systems
        self.system_loader.setup_all(self.game_context)

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

            # Publish game start event to trigger intro script
            if self.event_bus:
                self.event_bus.publish(GameStartEvent())

    def on_update(self, delta_time: float) -> None:
        """Update game logic each frame (arcade lifecycle callback).

        Called automatically by arcade each frame. Updates all game systems in order.
        """
        if not self.game_context:
            return

        # Handle scene transitions
        scene_manager = cast("SceneManager", self.game_context.get_system("scene"))
        if scene_manager and scene_manager.transition_state != TransitionState.NONE:
            scene_manager.update(delta_time, self.game_context)
            # During transition, skip other game logic
            return

        # Update ALL systems generically via system_loader
        if self.system_loader:
            self.system_loader.update_all(delta_time, self.game_context)

        # Draw ALL systems (world coordinates) via system_loader
        if self.system_loader and self.game_context:
            self.system_loader.draw_all(self.game_context)

        # Draw UI in screen coordinates
        arcade.camera.Camera2D().use()

        # Draw ALL systems (screen coordinates) via system_loader
        if self.system_loader and self.game_context:
            self.system_loader.draw_ui_all(self.game_context)

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        """Handle key presses (arcade lifecycle callback).

        Processes keyboard input. Most input handling is delegated to specific systems
        via the SystemLoader. This view handles global hotkeys (like menus).
        """
        if not self.system_loader or not self.game_context:
            return None

        # Delegate to systems first (e.g., Dialog might consume input)
        if self.system_loader.on_key_press_all(symbol, modifiers, self.game_context):
            return True

        return None

    def on_key_release(self, symbol: int, modifiers: int) -> bool | None:
        """Handle key releases (arcade lifecycle callback)."""
        if self.system_loader and self.game_context:
            self.system_loader.on_key_release_all(symbol, modifiers, self.game_context)
        return None

    def cleanup(self) -> None:
        """Clean up resources when transitioning away from this view.

        Performs cleanup including auto-save, stopping audio, clearing sprite lists,
        resetting managers, and clearing the initialized flag. Called before switching
        to another view (menu, inventory, etc.).

        Cleanup process:
        1. Auto-save game state
        2. Stop background music
        3. Clear all sprite lists
        4. Clear sprite references
        5. Close dialog
        6. Clear all managers (NPCs, interactions, portals, particles, scripts, events)
        7. Reset initialized flag so game will set up again on next show

        Side effects:
            - Writes auto-save file
            - Stops audio playback
            - Clears all sprite lists and references
            - Resets all managers to empty state
            - Sets initialized = False
        """
        # Cache NPC and script state for this scene before clearing (for scene transitions)
        scene_manager = self.game_context.get_system("scene") if self.game_context else None
        map_manager = self.game_context.get_system("map") if self.game_context else None
        npc_manager = self.game_context.get_system("npc") if self.game_context else None
        script_manager = self.game_context.get_system("script") if self.game_context else None

        current_map = getattr(map_manager, "current_map", "") if map_manager else ""

        if current_map and npc_manager and hasattr(scene_manager, "cache_scene_state"):
            scene_manager.cache_scene_state(current_map, npc_manager, script_manager)

        # Cleanup ALL pluggable systems generically (includes AudioManager cleanup)
        if self.system_loader:
            self.system_loader.cleanup_all()

        # Clear references
        self.scene = None
        self.tile_map = None
        self.camera = None

        # Clear event bus
        self.event_bus.clear()

        # Reset initialization flag so game will be set up again on next show
        self.initialized = False
