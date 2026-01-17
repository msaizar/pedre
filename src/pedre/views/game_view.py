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

import json
import logging
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, cast

import arcade

from pedre.constants import asset_path
from pedre.systems import (
    DialogManager,
    EventBus,
    GameContext,
    SceneStateCache,
    SystemLoader,
)

# These imports are used for cast() type annotations only
if TYPE_CHECKING:
    from pedre.config import GameSettings
    from pedre.systems import (
        CameraManager,
        MapManager,
        PathfindingManager,
        SceneManager,
        ScriptManager,
    )
    from pedre.systems.npc import NPCDialogConfig, NPCManager
    from pedre.types import SceneStateCacheDict
    from pedre.view_manager import ViewManager

from pedre.systems.events import (
    GameStartEvent,
    SceneStartEvent,
)

logger = logging.getLogger(__name__)


class TransitionState(Enum):
    """Enum for scene transition states."""

    NONE = auto()  # No transition happening
    FADING_OUT = auto()  # Fading out old scene
    LOADING = auto()  # Loading new scene
    FADING_IN = auto()  # Fading in new scene


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

    # Class-level cache for per-scene dialog data (lazy loaded).
    # Maps scene name to dialog data: scene_name -> npc_name -> dialog_level -> dialog_data
    _dialog_cache: ClassVar[dict[str, dict[str, dict[int | str, NPCDialogConfig]]]] = {}

    # Class-level cache for per-scene script JSON data (lazy loaded).
    # Maps scene name to raw JSON data loaded from script files.
    _script_cache: ClassVar[dict[str, dict[str, Any]]] = {}

    # Class-level cache for NPC state per scene (persists across scene transitions).
    # Stores NPC positions, visibility, and dialog levels for each visited scene.
    _scene_state_cache: ClassVar[SceneStateCache] = SceneStateCache()

    @classmethod
    def restore_scene_state_cache(cls, scene_states: SceneStateCacheDict) -> None:
        """Restore the scene state cache from saved data.

        Args:
            scene_states: Dictionary of scene states from a save file.
        """
        cls._scene_state_cache.from_dict(scene_states)

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

        # Core systems that need direct fast access (affect control flow)
        # All other systems accessed via self.game_context.get_system()
        self.dialog_manager: DialogManager | None = None

        # Sprite lists
        self.player_sprite: arcade.Sprite | None = None
        self.player_list: arcade.SpriteList | None = None
        self.wall_list: arcade.SpriteList | None = None
        self.npc_list: arcade.SpriteList | None = None

        # Tile map
        self.tile_map: arcade.TileMap | None = None
        self.scene: arcade.Scene | None = None

        # Camera for scrolling
        self.camera: arcade.camera.Camera2D | None = None

        # Track current NPC for post-dialog actions
        self.current_npc_name: str = ""
        self.current_npc_dialog_level: int = 0

        # Portal tracking
        self.spawn_waypoint: str | None = None

        # Track if game has been initialized
        self.initialized: bool = False

        # Text objects for UI (created on first draw)
        self.instructions_text: arcade.Text | None = None

    def setup(self) -> None:
        """Set up the game. Called on first show or when resetting the game state."""
        # Ensure systems are initialized
        if not hasattr(self, "system_loader") or not self.system_loader:
            self._init_systems()

        # Load the initial map
        target_map = self.map_file or self.settings.initial_map
        if target_map:
            self.load_level(target_map, self.spawn_waypoint)

    def _init_systems(self) -> None:
        """Initialize all game systems (run once)."""
        if self.settings is None:
            self.settings = self.window.settings

        # Initialize pluggable systems via SystemLoader
        self.system_loader = SystemLoader(self.settings)
        system_instances = self.system_loader.instantiate_all()

        # Keep only core system references for fast access
        self.dialog_manager = cast("DialogManager", system_instances.get("dialog"))

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

    def load_level(self, map_file: str, spawn_waypoint: str | None = None) -> None:
        """Load a new level/map.

        Args:
            map_file: The .tmx map file.
            spawn_waypoint: Waypoint to spawn at (optional).
        """
        logger.info("Loading level: %s (waypoint: %s)", map_file, spawn_waypoint)
        self.map_file = map_file
        self.spawn_waypoint = spawn_waypoint

        # Ensure systems are initialized
        if not hasattr(self, "system_loader") or not self.system_loader:
            logger.warning("load_level called before init_systems, initializing now")
            self._init_systems()

        self.current_scene = map_file.replace(".tmx", "").lower()

        # Update context
        if self.game_context:
            self.game_context.current_scene = self.current_scene

        # Get managers
        map_manager = cast("MapManager", self.game_context.get_system("map"))
        npc_manager = cast("NPCManager", self.game_context.get_system("npc"))
        script_manager = cast("ScriptManager", self.game_context.get_system("script"))

        # Clean up old sprites
        self.wall_list = arcade.SpriteList()
        # Note: player_list is recreated below

        # Load map via MapManager
        if map_manager and self.settings and self.game_context:
            map_manager.load_map(map_file, self.game_context, self.settings)

            # Update View references from MapManager
            self.tile_map = map_manager.tile_map
            self.scene = map_manager.scene
            self.wall_list = self.game_context.wall_list

            # Sync NPC list
            self.npc_list = arcade.SpriteList()
            if self.scene and "NPCs" in self.scene:
                for sprite in self.scene["NPCs"]:
                    self.npc_list.append(sprite)
                    # 애니메이션이 필요한지 확인
                    if "sprite_sheet" in sprite.properties:
                        # Constants and AnimatedNPC should ideally be at top-level
                        # but leaving here to minimize logic changes if they are already here.

                        sprite.properties["sprite_sheet"]
                        # ... rest of sheet logic (assuming it follows)

        # Player setup is triggered by MapManager calls (PlayerManager._spawn_player)
        # Update local player sprite ref
        if self.game_context and self.game_context.player_sprite:
            self.player_sprite = self.game_context.player_sprite
            self.player_list = arcade.SpriteList()
            self.player_list.append(self.player_sprite)

            # Setup Camera
            camera_manager = cast("CameraManager", self.game_context.get_system("camera"))
            if camera_manager:
                self.camera = arcade.camera.Camera2D(
                    position=(self.player_sprite.center_x, self.player_sprite.center_y)
                )
                camera_manager.set_camera(self.camera)
                if self.tile_map:
                    map_width = self.tile_map.width * self.tile_map.tile_width
                    map_height = self.tile_map.height * self.tile_map.tile_height
                    camera_manager.set_bounds(map_width, map_height, self.window.width, self.window.height)

        # Scripts and Dialogs loading
        # Load scene-specific dialog data from JSON (with per-scene caching)
        if npc_manager and self.settings:
            if self.current_scene in GameView._dialog_cache:
                npc_manager.dialogs[self.current_scene] = GameView._dialog_cache[self.current_scene]
            else:
                try:
                    scene_dialog_file = asset_path(
                        f"dialogs/{self.current_scene}_dialogs.json", self.settings.assets_handle
                    )
                    if (
                        npc_manager.load_dialogs_from_json(scene_dialog_file)
                        and self.current_scene in npc_manager.dialogs
                    ):
                        GameView._dialog_cache[self.current_scene] = npc_manager.dialogs[self.current_scene]
                except Exception:  # noqa: BLE001
                    # No dialogs found or failed to load
                    pass

        # Load Scripts
        if script_manager and self.settings:
            npc_dialogs_data = npc_manager.dialogs if npc_manager else {}

            if self.current_scene in GameView._script_cache:
                script_manager.load_scripts_from_data(GameView._script_cache[self.current_scene], npc_dialogs_data)
            else:
                try:
                    scene_script_file = asset_path(
                        f"scripts/{self.current_scene}_scripts.json", self.settings.assets_handle
                    )
                    script_manager.load_scripts(scene_script_file, npc_dialogs_data)
                    # Cache
                    with Path(scene_script_file).open() as f:
                        GameView._script_cache[self.current_scene] = json.load(f)
                except Exception:  # noqa: BLE001
                    pass

        # Restore Scene State
        if (
            self.map_file
            and self._scene_state_cache.restore_scene_state(self.map_file, npc_manager, script_manager)
            and self.wall_list
            and npc_manager
        ):
            # Sync wall_list with NPC visibility after restore
            for npc_state in npc_manager.npcs.values():
                if not npc_state.sprite.visible and npc_state.sprite in self.wall_list:
                    self.wall_list.remove(npc_state.sprite)
                elif npc_state.sprite.visible and npc_state.sprite not in self.wall_list:
                    self.wall_list.append(npc_state.sprite)

        # Configure pathfinding
        pathfinding_manager = cast("PathfindingManager", self.game_context.get_system("pathfinding"))
        if self.wall_list and pathfinding_manager:
            pathfinding_manager.set_wall_list(self.wall_list)

        # Publish Scene Start Event
        if self.event_bus:
            self.event_bus.publish(SceneStartEvent(self.current_scene))

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

        # Check scene transition status
        scene_manager = cast("SceneManager", self.game_context.get_system("scene"))
        if scene_manager and scene_manager.state != TransitionState.NONE:
            scene_manager.update(delta_time, self.game_context)
            # During transition, don't update other game logic
            return

        # Update ALL systems generically via system_loader
        if self.system_loader:
            self.system_loader.update_all(delta_time, self.game_context)

    def on_draw(self) -> None:
        """Render the game each frame (arcade lifecycle callback)."""
        self.clear()

        if self.camera:
            self.camera.use()

        # Draw the scene
        if self.scene:
            self.scene.draw()

        # Draw ALL systems (world coordinates) via system_loader
        if self.system_loader and self.game_context:
            self.system_loader.draw_all(self.game_context)

        # Draw UI in screen coordinates
        arcade.camera.Camera2D().use()

        # Create instructions text if not already created
        if self.instructions_text is None:
            instructions = (
                "Arrow keys to move | SPACE to interact | I for inventory\n"
                "ESC to menu | Shift+D debug | F5 save | F9 load"
            )
            self.instructions_text = arcade.Text(
                instructions,
                10,
                10,
                arcade.color.WHITE,
                font_size=12,
            )

        # Draw instructions
        self.instructions_text.draw()

        # Draw ALL systems (screen coordinates) via system_loader
        if self.system_loader and self.game_context:
            self.system_loader.draw_ui_all(self.game_context)

        # Draw transition overlay
        if self.game_context:
            scene_manager = cast("SceneManager", self.game_context.get_system("scene"))
            if scene_manager:
                scene_manager.draw_overlay()

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

        # Global GameView Hotkeys

        # Menu / Pause
        if symbol == arcade.key.ESCAPE:
            # Check blockers first
            dialog_manager = self.game_context.get_system("dialog")
            if dialog_manager and dialog_manager.showing:
                # Dialog should have handled ESC if it closes it?
                # Usually Escape opens menu, but if dialog is open, maybe close dialog or ignore?
                # Current logic allowed ESC to open menu even if dialog showing, but let's check blockers.
                pass

            # Pause game (preserve game view for quick resume)
            self.view_manager.show_menu(from_game_pause=True)
            return True

            # Quick save
        if symbol == arcade.key.F5:
            self.quick_save()
            return True
        # Quick load
        if symbol == arcade.key.F9:
            self.quick_load()
            return True
        # Inventory
        if symbol == arcade.key.I:
            self.view_manager.show_inventory()
            return True

        return None

    def on_key_release(self, symbol: int, modifiers: int) -> bool | None:
        """Handle key releases (arcade lifecycle callback)."""
        if self.system_loader and self.game_context:
            self.system_loader.on_key_release_all(symbol, modifiers, self.game_context)
        return None

    def quick_save(self) -> None:
        """Quick save game state to auto-save slot (triggered by F5).

        Saves current player position, map, NPC dialog levels, and inventory to the
        auto-save slot. Plays a save sound effect on success.

        Side effects:
            - Writes save file to disk
            - Plays save.wav sound effect on success
            - Logs save status
        """
        if not self.player_sprite or not self.map_file or not self.game_context:
            return

        # Get systems for save
        save_manager = self.game_context.get_system("save")
        npc_manager = self.game_context.get_system("npc")
        inventory_manager = self.game_context.get_system("inventory")
        audio_manager = self.game_context.get_system("audio")
        script_manager = self.game_context.get_system("script")

        if not save_manager:
            logger.warning("Quick save failed: save_manager not available")
            return

        success = save_manager.auto_save(
            player_x=self.player_sprite.center_x,
            player_y=self.player_sprite.center_y,
            current_map=self.map_file,
            npc_manager=npc_manager,
            inventory_manager=inventory_manager,
            audio_manager=audio_manager,
            script_manager=script_manager,
        )

        if success:
            if audio_manager:
                audio_manager.play_sfx("save.wav")
            logger.info("Quick save completed")
        else:
            logger.warning("Quick save failed")

    def quick_load(self) -> None:
        """Quick load game state from auto-save slot (triggered by F9).

        Loads player position, map, NPC dialog levels, and inventory from the auto-save
        file. If the saved map differs from current, reloads the map. Plays a load sound
        effect on success.

        Side effects:
            - May reload map via setup() if map changed
            - Updates player position
            - Restores NPC dialog levels
            - Restores inventory contents
            - Plays load.wav sound effect on success
            - Logs load status and timestamp
        """
        if not self.game_context:
            logger.warning("Quick load failed: no game context")
            return

        # Get systems for load
        save_manager = self.game_context.get_system("save")
        if not save_manager:
            logger.warning("Quick load failed: save_manager not available")
            return

        save_data = save_manager.load_auto_save()

        if not save_data:
            logger.warning("No auto-save found")
            return

        # Reload the map if different
        if save_data.current_map != self.map_file:
            self.map_file = save_data.current_map
            self.setup()

        # Restore player position
        if self.player_sprite:
            self.player_sprite.center_x = save_data.player_x
            self.player_sprite.center_y = save_data.player_y

        # Get systems for state restore
        npc_manager = self.game_context.get_system("npc")
        inventory_manager = self.game_context.get_system("inventory")
        audio_manager = self.game_context.get_system("audio")
        script_manager = self.game_context.get_system("script")

        # Restore all manager states using the convenience method
        restored_objects, scene_states = save_manager.restore_all_state(
            save_data, npc_manager, inventory_manager, audio_manager, script_manager
        )

        # Update script manager's interacted_objects
        if script_manager:
            script_manager.interacted_objects = restored_objects

        # Restore scene state cache for NPC persistence across scene transitions
        if scene_states:
            self._scene_state_cache.from_dict(scene_states)

        if audio_manager:
            audio_manager.play_sfx("load.wav")
        logger.info("Quick load completed from %s", save_data.save_timestamp)

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
        # Get systems from context for cleanup operations
        npc_manager = self.game_context.get_system("npc") if self.game_context else None
        script_manager = self.game_context.get_system("script") if self.game_context else None
        save_manager = self.game_context.get_system("save") if self.game_context else None
        inventory_manager = self.game_context.get_system("inventory") if self.game_context else None
        audio_manager = self.game_context.get_system("audio") if self.game_context else None

        # Cache NPC and script state for this scene before clearing (for scene transitions)
        if self.map_file and npc_manager:
            self._scene_state_cache.cache_scene_state(self.map_file, npc_manager, script_manager)

        # Auto-save on cleanup (includes cached scene states for persistence)
        if self.player_sprite and self.map_file and save_manager:
            save_manager.auto_save(
                player_x=self.player_sprite.center_x,
                player_y=self.player_sprite.center_y,
                current_map=self.map_file,
                npc_manager=npc_manager,
                inventory_manager=inventory_manager,
                audio_manager=audio_manager,
                script_manager=script_manager,
                scene_states=self._scene_state_cache.to_dict(),
            )

        # Cleanup ALL pluggable systems generically (includes AudioManager cleanup)
        if self.system_loader:
            self.system_loader.cleanup_all()

        # Clear sprite lists
        if self.player_list:
            self.player_list.clear()
        if self.wall_list:
            self.wall_list.clear()
        if self.npc_list:
            self.npc_list.clear()

        # Clear references
        self.player_sprite = None
        self.scene = None
        self.tile_map = None
        self.camera = None

        # Close dialog (core system)
        if self.dialog_manager:
            self.dialog_manager.close_dialog()

        # Clear event bus
        self.event_bus.clear()

        # Reset initialization flag so game will be set up again on next show
        self.initialized = False
