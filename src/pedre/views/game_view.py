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
from pedre.sprites import AnimatedNPC, AnimatedPlayer
from pedre.systems import (
    AudioManager,
    CameraManager,
    DialogManager,
    EventBus,
    GameContext,
    InputManager,
    InteractionManager,
    InventoryManager,
    NPCManager,
    ParticleManager,
    PathfindingManager,
    PortalManager,
    SaveManager,
    SceneStateCache,
    ScriptManager,
)
from pedre.systems.actions import ActionSequence
from pedre.systems.events import (
    DialogClosedEvent,
    GameStartEvent,
    InventoryClosedEvent,
    NPCInteractedEvent,
    ObjectInteractedEvent,
    SceneStartEvent,
)

if TYPE_CHECKING:
    from arcade.types import TiledObject

    from pedre.systems.npc import NPCDialogConfig
    from pedre.view_manager import ViewManager

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
        input_manager: Processes keyboard input for player movement.
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
    def restore_scene_state_cache(cls, scene_states: dict[str, Any]) -> None:
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
        debug_mode: bool = False,
    ) -> None:
        """Initialize the game view.

        Creates all manager instances and initializes state, but does NOT load the map
        or set up sprites yet. Actual setup happens in setup() when the view is first shown.

        This lazy initialization pattern allows the view to be created without immediately
        loading heavy assets, and enables the map_file to be changed before setup() runs.

        Args:
            view_manager: ViewManager instance for handling view transitions (menu, inventory, etc.).
            map_file: Name of the Tiled .tmx file to load from assets/maps/. If None, uses INITIAL_MAP from config.
            debug_mode: If True, displays debug overlays showing NPC positions and tile coordinates.
        """
        super().__init__()
        self.view_manager = view_manager
        self.map_file = map_file
        self.debug_mode = debug_mode

        # Game systems (initialized with None, will be set up in on_show_view)
        self.dialog_manager = DialogManager()
        self.input_manager: InputManager | None = None
        self.pathfinding_manager: PathfindingManager | None = None
        self.inventory_manager = InventoryManager()

        # Event-driven scripting system (created early so it can be passed to managers)
        self.event_bus = EventBus()

        self.script_manager = ScriptManager(self.event_bus)

        self.npc_manager: NPCManager | None = None
        self.interaction_manager: InteractionManager | None = None
        self.portal_manager: PortalManager | None = None
        self.camera_manager: CameraManager | None = None
        self.save_manager = SaveManager()
        self.audio_manager = AudioManager()
        self.particle_manager = ParticleManager()
        self.game_context: GameContext | None = None

        # Sprite lists
        self.player_sprite: arcade.Sprite | None = None
        self.player_list: arcade.SpriteList | None = None
        self.wall_list: arcade.SpriteList | None = None
        self.npc_list: arcade.SpriteList | None = None

        # Tile map
        self.tile_map: arcade.TileMap | None = None
        self.scene: arcade.Scene | None = None

        # Physics engine
        self.physics_engine: arcade.PhysicsEngineSimple | None = None

        # Camera for scrolling
        self.camera: arcade.camera.Camera2D | None = None

        # Track current NPC for post-dialog actions
        self.current_npc_name: str = ""
        self.current_npc_dialog_level: int = 0

        # Portal tracking
        self.spawn_waypoint: str | None = None

        # Track if game has been initialized
        self.initialized: bool = False

        # Scene transition system (simple black fade)
        self.transition_state: TransitionState = TransitionState.NONE
        self.transition_alpha: float = 0.0  # 0.0 = transparent, 1.0 = opaque
        self.transition_speed: float = 3.0  # Alpha change per second
        self.pending_map_file: str | None = None  # Map to load after fade out
        self.pending_spawn_waypoint: str | None = None  # Spawn point for new map

        # Text objects for UI (created on first draw)
        self.instructions_text: arcade.Text | None = None
        self.debug_text_objects: list[arcade.Text] = []

    def setup(self) -> None:
        """Set up the game by loading map, creating sprites, and initializing systems.

        This is the main initialization method that loads all game assets and prepares
        the view for gameplay. Called automatically on first on_show_view(), or manually
        when transitioning to a new map via portals.

        Setup workflow:
        1. Load Tiled map file and extract layers (walls, NPCs, objects, etc.)
        2. Start background music from map properties
        3. Create animated player sprite at spawn position
        4. Register NPCs with NPC manager
        5. Load scene-specific NPC dialogs (with per-scene caching)
        6. Create GameContext with all managers
        7. Load scene-specific scripts
        8. Configure pathfinding with wall list
        9. Initialize physics engine for player collision
        10. Set up camera with smooth following and bounds

        Side effects:
            - Loads map file and populates sprite lists
            - Creates player and NPC sprites
            - Initializes all game systems
            - Starts background music
            - Creates physics engine and camera
        """
        # Initialize managers with settings
        settings = self.window.settings
        self.input_manager = InputManager(movement_speed=settings.player_movement_speed)
        self.pathfinding_manager = PathfindingManager(tile_size=settings.tile_size)
        self.npc_manager = NPCManager(
            pathfinding_manager=self.pathfinding_manager,
            interaction_distance=settings.npc_interaction_distance,
            waypoint_threshold=settings.waypoint_threshold,
            npc_speed=settings.npc_speed,
            inventory_manager=self.inventory_manager,
            event_bus=self.event_bus,
            interacted_objects=self.script_manager.interacted_objects,
        )
        self.interaction_manager = InteractionManager(interaction_distance=settings.interaction_manager_distance)
        self.portal_manager = PortalManager(interaction_distance=settings.portal_interaction_distance)

        # Use initial_map from settings if map_file was not provided
        if self.map_file is None:
            self.map_file = settings.initial_map

        # Load the Tiled map
        map_path = asset_path(f"maps/{self.map_file}", settings.assets_handle)
        self._load_tilemap(map_path)

        # Load background music from map properties
        if self.tile_map and hasattr(self.tile_map, "properties") and self.tile_map.properties:
            props = self.tile_map.properties
            if isinstance(props, dict):
                music_file = props.get("music")
                if music_file and isinstance(music_file, str):
                    self.audio_manager.play_music(music_file, loop=True, volume=0.7)
                    logger.info("Playing background music: %s", music_file)

        # Set up player sprite
        self._setup_player()

        # Register NPCs with the NPC manager
        if self.npc_list:
            for npc_sprite in self.npc_list:
                npc_name = self._get_npc_name(npc_sprite)
                if npc_name:
                    self.npc_manager.register_npc(npc_sprite, npc_name)

        # Restore cached NPC state if returning to a previously visited scene
        if (
            self.map_file
            and self._scene_state_cache.restore_scene_state(self.map_file, self.npc_manager)
            and self.wall_list
            and self.npc_manager
        ):
            # Sync wall_list with NPC visibility after restore
            # NPCs that became invisible need to be removed from wall_list
            for npc_state in self.npc_manager.npcs.values():
                if not npc_state.sprite.visible and npc_state.sprite in self.wall_list:
                    self.wall_list.remove(npc_state.sprite)
                elif npc_state.sprite.visible and npc_state.sprite not in self.wall_list:
                    self.wall_list.append(npc_state.sprite)

        # Extract scene name from map file (e.g., "Casa.tmx" -> "casa")
        self.current_scene = self.map_file.replace(".tmx", "").lower()

        # Load scene-specific dialog data from JSON (with per-scene caching)
        if self.current_scene in GameView._dialog_cache:
            # Reuse cached dialogs for this scene
            self.npc_manager.dialogs[self.current_scene] = GameView._dialog_cache[self.current_scene]
            logger.debug("Reusing cached dialog data for scene: %s", self.current_scene)
        else:
            # First time loading this scene - load and cache the dialogs
            scene_dialog_file = asset_path(f"dialogs/{self.current_scene}_dialogs.json", settings.assets_handle)
            if not self.npc_manager.load_dialogs_from_json(scene_dialog_file):
                logger.warning("Failed to load dialogs for scene %s, NPCs may not have dialog", self.current_scene)
            # Cache only this scene's dialog data
            elif self.current_scene in self.npc_manager.dialogs:
                GameView._dialog_cache[self.current_scene] = self.npc_manager.dialogs[self.current_scene]
                logger.info("Cached dialog data for scene: %s", self.current_scene)

        # Generic dialog config removed - config.json no longer used

        # Initialize game context for script system

        # Get waypoints from loaded map
        waypoints = getattr(self, "_waypoints", {})

        self.game_context = GameContext(
            dialog_manager=self.dialog_manager,
            npc_manager=self.npc_manager,
            inventory_manager=self.inventory_manager,
            particle_manager=self.particle_manager,
            audio_manager=self.audio_manager,
            event_bus=self.event_bus,
            wall_list=self.wall_list or arcade.SpriteList(),
            player_sprite=self.player_sprite,
            game_view=self,
            current_scene=self.current_scene,
            waypoints=waypoints,
            interacted_objects=self.script_manager.interacted_objects,
        )

        # Load scene-specific scripts (with per-scene caching)
        npc_dialogs_data = self.npc_manager.dialogs  # Raw dialog data
        scene_script_file = asset_path(f"scripts/{self.current_scene}_scripts.json", settings.assets_handle)

        if self.current_scene in GameView._script_cache:
            # Reuse cached script JSON data for this scene
            cached_data = GameView._script_cache[self.current_scene]
            self.script_manager.load_scripts_from_data(cached_data, npc_dialogs_data)
            logger.debug("Reusing cached script data for scene: %s", self.current_scene)
        else:
            # First time loading this scene - load, parse, and cache the scripts
            self.script_manager.load_scripts(scene_script_file, npc_dialogs_data)
            # Cache the raw JSON data for future use
            try:
                with Path(scene_script_file).open() as f:
                    GameView._script_cache[self.current_scene] = json.load(f)
                logger.info("Cached script data for scene: %s", self.current_scene)
            except (FileNotFoundError, json.JSONDecodeError):
                logger.warning("Failed to cache script data for scene: %s", self.current_scene)

        # Configure pathfinding
        if self.wall_list:
            self.pathfinding_manager.set_wall_list(self.wall_list)

        # Set up physics engine
        if self.player_sprite and self.wall_list:
            self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.wall_list)

        # Set up camera with smooth following
        if self.player_sprite:
            self.camera = arcade.camera.Camera2D(position=(self.player_sprite.center_x, self.player_sprite.center_y))
            self.camera_manager = CameraManager(self.camera, lerp_speed=0.1)

            # Set camera bounds if we have a tilemap
            if self.tile_map:
                map_width = self.tile_map.width * self.tile_map.tile_width
                map_height = self.tile_map.height * self.tile_map.tile_height
                self.camera_manager.set_bounds(map_width, map_height, self.window.width, self.window.height)

        # Publish scene start event to trigger scene-specific scripts
        if self.event_bus:
            self.event_bus.publish(SceneStartEvent(self.current_scene))

    def _load_tilemap(self, map_path: str) -> None:
        """Load a Tiled map file and extract all layers and objects (internal implementation).

        Loads the .tmx file, creates an arcade Scene, and extracts collision layers, NPCs,
        waypoints, portals, and interactive objects. Handles NPC visibility based on map
        properties (show_all_npcs, show_npcs) and initially_hidden flags.

        Layer extraction:
        - Walls/Collision/Objects layers → wall_list (for collision)
        - NPCs layer → npc_list (also added to wall_list for collision)
        - Waypoints object layer → _waypoints dictionary
        - Portals object layer → registered with portal_manager
        - Interactive tile layer → registered with interaction_manager

        Args:
            map_path: Absolute path to the .tmx Tiled map file.

        Side effects:
            - Sets self.tile_map, self.scene, self.wall_list, self.npc_list
            - Sets self._waypoints dictionary
            - Registers portals and interactive objects with managers
            - Replaces static NPC sprites with AnimatedNPC instances
            - Hides initially_hidden NPCs (unless overridden by map properties)
        """
        self.tile_map = arcade.load_tilemap(map_path, scaling=1.0)
        self.scene = arcade.Scene.from_tilemap(self.tile_map)

        # Get collision layers from the scene
        self.wall_list = arcade.SpriteList()
        self.npc_list = arcade.SpriteList()

        try:
            # Combine multiple layers for collision
            collision_layer_names = ["Walls", "Collision", "Objects"]
            for layer_name in collision_layer_names:
                if layer_name in self.scene:
                    for sprite in self.scene[layer_name]:
                        self.wall_list.append(sprite)

            # Load NPCs from object layer
            self._setup_animated_npcs()

            # Object-layer data
            self._waypoints = self._load_waypoints()
            self._load_portals()
            self._load_interactive_objects()
        except KeyError:
            self._waypoints = {}

    def _setup_player(self) -> None:
        """Set up the player sprite (internal implementation).

        Creates an AnimatedPlayer sprite and places it at the spawn position. Requires a player
        spawn point object to exist in the loaded Tiled map's "Player" object layer with
        sprite_sheet and tile_size properties.

        Player setup workflow:
        1. Create sprite list for player
        2. Load player spawn point from "Player" object layer
        3. Determine spawn position (from portal waypoint or object position)
        4. Extract sprite sheet path, tile size, and animation properties from object
        5. Create AnimatedPlayer with configured sprite sheet
        6. Add player to sprite list and scene

        Required Player object properties in Tiled:
            - sprite_sheet: Path to sprite sheet file (e.g., "images/characters/princess.png")
            - tile_size: Size of each tile in the sprite sheet (typically 64)
            - 4-directional animation configuration (idle_up_frames, idle_up_row, etc.)

        Optional Player object properties:
            - spawn_at_portal (bool): If true, spawn at portal waypoint instead of object position.
              Default is false (spawn at object position).

        Side effects:
            - Sets self.player_list with the player sprite
            - Sets self.player_sprite reference
            - Adds/replaces "Player" layer in scene

        Raises:
            ValueError: If Player object layer doesn't exist or is missing required properties.
        """
        self.player_list = arcade.SpriteList()

        # Load player spawn object from object layer
        player_layer = self._get_object_layer("Player")
        if not player_layer or len(player_layer) == 0:
            msg = "Player object must exist in the 'Player' object layer"
            raise ValueError(msg)

        # Use first player object (should only be one)
        player_obj = player_layer[0]

        # Check if player should spawn at portal waypoint or object position
        spawn_at_portal = player_obj.properties.get("spawn_at_portal", False)

        if spawn_at_portal:
            # Player prefers portal spawn - check if we have a portal waypoint
            portal_position = self._get_spawn_position()
            if portal_position:
                spawn_x, spawn_y = portal_position
            else:
                # No portal waypoint, use object position as fallback
                spawn_x = float(player_obj.shape[0])
                spawn_y = float(player_obj.shape[1])
        else:
            # Use the object's position (point object x,y in pixels)
            spawn_x = float(player_obj.shape[0])
            spawn_y = float(player_obj.shape[1])

        # Get sprite sheet and tile size from properties (required)
        if not player_obj.properties:
            msg = "Player object must have properties defined in Tiled"
            raise ValueError(msg)

        sprite_sheet = player_obj.properties.get("sprite_sheet")
        if not sprite_sheet:
            msg = "Player object must have 'sprite_sheet' property defined in Tiled"
            raise ValueError(msg)

        tile_size = player_obj.properties.get("tile_size")
        if not tile_size:
            msg = "Player object must have 'tile_size' property defined in Tiled"
            raise ValueError(msg)

        settings = self.window.settings
        sprite_sheet_path = asset_path(sprite_sheet, settings.assets_handle)

        # Get animation properties from object
        anim_props = self._get_animation_properties_from_dict(player_obj.properties)

        # Create animated player sprite
        self.player_sprite = AnimatedPlayer(
            sprite_sheet_path,
            tile_size=tile_size,
            columns=12,
            scale=1.0,
            center_x=spawn_x,
            center_y=spawn_y,
            **anim_props,
        )

        self.player_list.append(self.player_sprite)

        # Add player to scene
        if self.scene:
            # Remove old player sprite list if it exists to avoid override warning
            if "Player" in self.scene:
                self.scene.remove_sprite_list_by_name("Player")
            self.scene.add_sprite_list("Player", sprite_list=self.player_list)

    def _get_spawn_position(self) -> tuple[float, float] | None:
        """Get the portal waypoint spawn position for the player (internal implementation).

        Checks if a spawn waypoint was set by a portal transition and returns its pixel
        coordinates. This is only used when spawn_at_portal is true on the Player object.

        The spawn waypoint is cleared after being used to prevent it affecting subsequent
        map loads.

        Returns:
            Tuple of (x, y) pixel coordinates for portal waypoint, or None if no waypoint set.

        Side effects:
            - Clears self.spawn_waypoint after using it for spawn position
        """
        # Check if we have a spawn waypoint from portal transition
        if self.spawn_waypoint:
            waypoints = getattr(self, "_waypoints", {})
            if self.spawn_waypoint in waypoints:
                settings = self.window.settings
                tile_x, tile_y = waypoints[self.spawn_waypoint]
                spawn_x = tile_x * settings.tile_size + settings.tile_size / 2
                spawn_y = tile_y * settings.tile_size + settings.tile_size / 2
                logger.info("Spawning player at waypoint '%s': (%d, %d)", self.spawn_waypoint, tile_x, tile_y)
                # Clear the spawn waypoint after using it
                self.spawn_waypoint = None
                return spawn_x, spawn_y

        return None

    def _get_npc_name(self, npc_sprite: arcade.Sprite) -> str | None:
        """Get the name of an NPC from its properties (internal implementation).

        Extracts the "name" property from a sprite's Tiled properties dictionary. The name
        is converted to lowercase and returned. If the sprite has no properties, or the name
        is empty/missing, returns None.

        This is used to identify NPCs loaded from Tiled maps, where the name property is
        set in the map editor.

        Args:
            npc_sprite: The NPC sprite with Tiled properties.

        Returns:
            Lowercase NPC name string, or None if no name property found.
        """
        if hasattr(npc_sprite, "properties") and npc_sprite.properties and isinstance(npc_sprite.properties, dict):
            return npc_sprite.properties.get("name", "").lower() or None
        return None

    def _get_object_name(self, sprite: arcade.Sprite) -> str | None:
        """Get the name of an object from its properties (internal implementation).

        Extracts the object name from a sprite loaded from Tiled, trying two approaches:
        1. Check sprite.properties["name"] (most common for custom properties)
        2. Check sprite.name attribute directly (some Tiled versions)

        The name is converted to lowercase before returning. If neither approach finds
        a name, returns None.

        Args:
            sprite: The interactive object sprite from Tiled.

        Returns:
            Lowercase object name string, or None if no name found.
        """
        # First try to get name from sprite properties (Tiled object name attribute)
        if hasattr(sprite, "properties") and sprite.properties and isinstance(sprite.properties, dict):
            name = sprite.properties.get("name")
            if name:
                return name.lower()

        # Fallback: try getting name directly from sprite (some Tiled versions)
        if hasattr(sprite, "name") and sprite.name and isinstance(sprite.name, str):
            return sprite.name.lower()

        return None

    def _get_object_layer(self, layer_name: str) -> list[TiledObject] | None:
        """Return an object layer from the tile map, or None (internal implementation).

        Retrieves an object layer by name from the loaded Tiled map. Object layers contain
        points, rectangles, polygons, and other geometric shapes defined in the map editor,
        commonly used for waypoints, portals, and spawn points.

        Args:
            layer_name: Name of the object layer (e.g., "Waypoints", "Portals").

        Returns:
            List of TiledObject instances from the layer, or None if layer doesn't exist
            or no tile map is loaded.
        """
        if not self.tile_map or not hasattr(self.tile_map, "object_lists"):
            return None
        return self.tile_map.object_lists.get(layer_name)

    def _load_portals(self) -> None:
        """Load portals from Tiled object layer (internal implementation).

        Extracts portal objects from the "Portals" object layer and registers them with
        the portal manager. Portals are defined as rectangles or polygons in Tiled with
        custom properties specifying the target map and spawn waypoint.

        For each portal object:
        1. Validates it has a name, properties, and shape
        2. Calculates bounding box from shape (supports polygons and points)
        3. Creates an invisible sprite at the portal location
        4. Registers with portal_manager with name and properties

        Side effects:
            - Registers portals with self.portal_manager
            - Logs portal loading info and warnings
        """
        portal_layer = self._get_object_layer("Portals")
        if not portal_layer:
            logger.info("No Portals object layer found")
            return

        for portal in portal_layer:
            if not portal.name or not portal.properties:
                logger.warning("Portal missing name or properties")
                continue

            if not portal.shape:
                logger.warning("Portal '%s' has no shape", portal.name)
                continue

            # Polygon or rectangle → bounding box
            # Shape can be a sequence of points (list/tuple of tuples) or a single point
            if isinstance(portal.shape, (list, tuple)) and len(portal.shape) > 0:
                # Check if it's a sequence of points or a single point tuple
                first_elem = portal.shape[0]
                if isinstance(first_elem, (tuple, list)):
                    # It's a sequence of points - cast to help type checker
                    shape_seq = cast("list[tuple[float, float]]", portal.shape)
                    xs = [float(p[0]) for p in shape_seq]
                    ys = [float(p[1]) for p in shape_seq]
                else:
                    # It's a single point (x, y) or (x, y, z, w)
                    xs = [float(portal.shape[0])]
                    ys = [float(portal.shape[1])]
            else:
                logger.warning("Portal '%s' has invalid shape format", portal.name)
                continue

            sprite = arcade.Sprite()
            sprite.center_x = (min(xs) + max(xs)) / 2
            sprite.center_y = (min(ys) + max(ys)) / 2
            sprite.width = max(xs) - min(xs)
            sprite.height = max(ys) - min(ys)

            if self.portal_manager:
                self.portal_manager.register_portal(
                    sprite=sprite,
                    name=portal.name,
                    properties=portal.properties,
                )

            logger.info("Registered portal '%s'", portal.name)

    def _load_interactive_objects(self) -> None:
        """Load interactive objects from Tiled tile layer (internal implementation).

        Extracts interactive objects from the "Interactive" tile layer and registers them
        with the interaction manager. Interactive objects are regular tiles marked with
        custom properties that define their behavior when the player interacts with them.

        For each interactive tile:
        1. Gets object name from tile properties
        2. Validates it has both a name and properties
        3. Registers the tile sprite with interaction_manager

        Interactive objects can trigger dialogs, toggle state, or emit events when the
        player presses the interaction key nearby.

        Side effects:
            - Registers objects with self.interaction_manager
            - Logs object registration info and warnings
        """
        # Check if Interactive layer exists in scene (tile layer)
        if not self.scene or "Interactive" not in self.scene:
            logger.info("No Interactive tile layer found")
            return

        for sprite in self.scene["Interactive"]:
            # Get object name from tile properties
            obj_name = self._get_object_name(sprite)

            if not obj_name:
                logger.warning("Interactive tile at (%f, %f) missing name property", sprite.center_x, sprite.center_y)
                continue

            # Get properties from tile
            properties = sprite.properties if hasattr(sprite, "properties") and sprite.properties else {}

            if not properties:
                logger.warning("Interactive object '%s' has no properties", obj_name)
                continue

            # Register the actual tile sprite with interaction manager
            if self.interaction_manager:
                self.interaction_manager.register_object(
                    sprite=sprite,
                    name=obj_name,
                    properties=properties,
                )

            logger.info("Registered interactive object '%s' at (%f, %f)", obj_name, sprite.center_x, sprite.center_y)

    def _load_waypoints(self) -> dict[str, tuple[int, int]]:
        """Load waypoints from the Tiled map (internal implementation).

        Extracts waypoint objects from the "Waypoints" object layer and converts them to
        tile coordinates. Waypoints are point objects in Tiled that mark important locations
        like spawn points, NPC destinations, or portal targets.

        For each waypoint object:
        1. Validates it has a name and shape
        2. Extracts (x, y) pixel coordinates from shape
        3. Converts to tile coordinates (dividing by tile_size)
        4. Stores in dictionary with name as key

        Returns:
            Dictionary mapping waypoint names to (tile_x, tile_y) integer coordinates.
            Returns empty dict if no "Waypoints" layer exists.

        Side effects:
            - Logs waypoint loading info and warnings
        """
        waypoints: dict[str, tuple[int, int]] = {}

        waypoint_layer = self._get_object_layer("Waypoints")
        if not waypoint_layer:
            return waypoints

        settings = self.window.settings
        for obj in waypoint_layer:
            if not obj.name or not obj.shape:
                continue

            # Point objects: shape = (x, y) or (x, y, z)
            if isinstance(obj.shape, (tuple, list)) and len(obj.shape) >= 2:
                x = float(obj.shape[0])
                y = float(obj.shape[1])
                tile_x = int(x // settings.tile_size)
                tile_y = int(y // settings.tile_size)
            else:
                logger.warning("Waypoint '%s' has invalid shape format", obj.name)
                continue

            waypoints[obj.name] = (tile_x, tile_y)
            logger.info("Loaded waypoint '%s' at tile (%d, %d)", obj.name, tile_x, tile_y)

        return waypoints

    def _get_animation_properties(self, sprite: arcade.Sprite) -> dict[str, int]:
        """Extract animation properties from sprite properties (internal implementation).

        Parses animation configuration from a sprite's Tiled custom properties. These
        properties define which sprite sheet rows and frame counts to use for different
        animation states (idle, walk, appear, interact) in all four directions.

        Supported properties:
        - 4-directional idle/walk: idle_up_frames, idle_up_row, idle_down_frames, etc.
        - NPC-specific: appear_frames, appear_row, interact_up_frames, interact_up_row, etc.

        Only integer-valued properties are extracted. Non-integer or missing properties
        are silently skipped.

        Args:
            sprite: Sprite with Tiled custom properties.

        Returns:
            Dictionary with animation properties, empty if no properties found.
            Keys are property names like "idle_up_frames", values are integers.
        """
        animation_props: dict[str, int] = {}

        if hasattr(sprite, "properties") and sprite.properties:
            for key in [
                # 4-directional idle properties
                "idle_up_frames",
                "idle_up_row",
                "idle_down_frames",
                "idle_down_row",
                "idle_left_frames",
                "idle_left_row",
                "idle_right_frames",
                "idle_right_row",
                # 4-directional walk properties
                "walk_up_frames",
                "walk_up_row",
                "walk_down_frames",
                "walk_down_row",
                "walk_left_frames",
                "walk_left_row",
                "walk_right_frames",
                "walk_right_row",
                # NPC-specific properties
                "appear_frames",
                "appear_row",
                # 4-directional interact
                "interact_up_frames",
                "interact_up_row",
                "interact_down_frames",
                "interact_down_row",
                "interact_left_frames",
                "interact_left_row",
                "interact_right_frames",
                "interact_right_row",
            ]:
                if key in sprite.properties:
                    value = sprite.properties[key]
                    if isinstance(value, int):
                        animation_props[key] = value

        return animation_props

    def _get_animation_properties_from_dict(self, properties: dict) -> dict[str, int]:
        """Extract animation properties from a properties dictionary (internal implementation).

        Parses animation configuration from a Tiled object's custom properties dictionary.
        These properties define which sprite sheet rows and frame counts to use for different
        animation states (idle, walk, appear, interact) and directions (up, down, left, right).

        Supported properties:
        - 4-directional: idle_up_frames, idle_down_frames, idle_left_frames, idle_right_frames,
                        idle_up_row, idle_down_row, idle_left_row, idle_right_row,
                        walk_up_frames, walk_down_frames, walk_left_frames, walk_right_frames,
                        walk_up_row, walk_down_row, walk_left_row, walk_right_row
        - NPC-specific: appear_frames, appear_row, interact_up_frames, interact_up_row, etc.

        Only integer-valued properties are extracted. Non-integer or missing properties
        are silently skipped.

        Args:
            properties: Dictionary of Tiled custom properties.

        Returns:
            Dictionary with animation properties, empty if no properties found.
            Keys are property names like "idle_up_frames", values are integers.
        """
        animation_props: dict[str, int] = {}

        if properties:
            for key in [
                # 4-directional idle properties
                "idle_up_frames",
                "idle_up_row",
                "idle_down_frames",
                "idle_down_row",
                "idle_left_frames",
                "idle_left_row",
                "idle_right_frames",
                "idle_right_row",
                # 4-directional walk properties
                "walk_up_frames",
                "walk_up_row",
                "walk_down_frames",
                "walk_down_row",
                "walk_left_frames",
                "walk_left_row",
                "walk_right_frames",
                "walk_right_row",
                # NPC-specific properties
                "appear_frames",
                "appear_row",
                # 4-directional interact
                "interact_up_frames",
                "interact_up_row",
                "interact_down_frames",
                "interact_down_row",
                "interact_left_frames",
                "interact_left_row",
                "interact_right_frames",
                "interact_right_row",
            ]:
                if key in properties:
                    value = properties[key]
                    if isinstance(value, int):
                        animation_props[key] = value

        return animation_props

    def _setup_animated_npcs(self) -> None:
        """Load NPCs from object layer and create AnimatedNPC sprites (internal implementation).

        Loads NPC spawn points from the "NPCs" object layer and creates AnimatedNPC instances
        for each one. Each NPC object should have properties defining its sprite sheet,
        name, and animation configuration.

        NPC loading process:
        1. Load NPC objects from "NPCs" object layer
        2. For each NPC object, extract position and properties
        3. Create AnimatedNPC with sprite sheet and animation properties
        4. Handle visibility based on initially_hidden and map properties
        5. Add to npc_list, scene, and wall_list (for collision)

        Required NPC object properties in Tiled:
            - name: Unique identifier for the NPC (lowercase, e.g., "martin")
            - sprite_sheet: Path to sprite sheet file (e.g., "images/characters/martin.png")
            - tile_size: Size of each tile in the sprite sheet (32 or 64)
            - 4-directional animation configuration (idle_up_frames, idle_up_row, etc.)
            - initially_hidden (optional): If true, NPC starts invisible

        Side effects:
            - Populates self.npc_list with AnimatedNPC instances
            - Updates scene "NPCs" layer with NPC sprites
            - Updates wall_list with NPC sprites for collision
            - Loads sprite sheet images into memory
        """
        # Load NPC objects from object layer
        npc_layer = self._get_object_layer("NPCs")
        if not npc_layer:
            logger.debug("No NPCs object layer found in map")
            return

        # Get map-level visibility control properties
        show_all_npcs = False
        show_npcs_list = None
        if self.tile_map and hasattr(self.tile_map, "properties") and self.tile_map.properties:
            show_all_npcs = self.tile_map.properties.get("show_all_npcs", False)
            show_npcs = self.tile_map.properties.get("show_npcs", "")
            if isinstance(show_npcs, str) and show_npcs:
                show_npcs_list = [name.strip().lower() for name in show_npcs.split(",")]

        # Create AnimatedNPC sprite for each object
        for npc_obj in npc_layer:
            # Get required properties
            if not npc_obj.properties:
                logger.warning("NPC object missing properties, skipping")
                continue

            npc_name = npc_obj.properties.get("name")
            if not npc_name:
                logger.warning("NPC object missing 'name' property, skipping")
                continue

            sprite_sheet = npc_obj.properties.get("sprite_sheet")
            if not sprite_sheet:
                logger.warning("NPC '%s' missing 'sprite_sheet' property, skipping", npc_name)
                continue

            tile_size = npc_obj.properties.get("tile_size")
            if not tile_size or not isinstance(tile_size, int):
                logger.warning("NPC '%s' missing or invalid 'tile_size' property, skipping", npc_name)
                continue

            # Get spawn position from object (point object x, y)
            shape = npc_obj.shape
            if not isinstance(shape, tuple) or len(shape) < 2:
                logger.warning("NPC '%s' has invalid shape, skipping", npc_name)
                continue
            spawn_x = float(shape[0])
            spawn_y = float(shape[1])

            # Resolve the sprite sheet path
            if not isinstance(sprite_sheet, str):
                logger.warning("NPC '%s' has invalid sprite_sheet property, skipping", npc_name)
                continue
            settings = self.window.settings
            sprite_sheet_path = asset_path(sprite_sheet, settings.assets_handle)

            # Get animation properties from object
            anim_props = self._get_animation_properties_from_dict(npc_obj.properties)

            # Create animated NPC sprite (loads sprite sheet into memory)
            animated_sprite = AnimatedNPC(
                sprite_sheet_path,
                tile_size=tile_size,
                columns=12,
                scale=1.0,
                center_x=spawn_x,
                center_y=spawn_y,
                **anim_props,
            )

            # Store properties on sprite for later access
            animated_sprite.properties = npc_obj.properties

            # Handle visibility
            initially_hidden = npc_obj.properties.get("initially_hidden", False)
            should_hide = False
            if initially_hidden:
                npc_name_lower = npc_name.lower() if isinstance(npc_name, str) else str(npc_name).lower()
                in_show_list = show_npcs_list is not None and npc_name_lower in show_npcs_list
                should_hide = not (show_all_npcs or in_show_list)

            animated_sprite.visible = not should_hide

            # Add to npc_list (guaranteed to be initialized by setup())
            if self.npc_list is not None:
                self.npc_list.append(animated_sprite)

            # Add to wall_list for collision (only if visible)
            if animated_sprite.visible and self.wall_list is not None:
                self.wall_list.append(animated_sprite)

            logger.info(
                "Loaded NPC '%s' at (%.1f, %.1f) (visible=%s)", npc_name, spawn_x, spawn_y, animated_sprite.visible
            )

        # Add NPCs to scene
        if self.scene and self.npc_list:
            # Remove old NPCs layer if it exists
            if "NPCs" in self.scene:
                self.scene.remove_sprite_list_by_name("NPCs")
            # Create new sprite list and add to scene
            npc_sprite_list = arcade.SpriteList()
            for npc in self.npc_list:
                npc_sprite_list.append(npc)
            self.scene.add_sprite_list("NPCs", sprite_list=npc_sprite_list)

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

        Called automatically by arcade each frame. Updates all game systems in order:
        player movement, physics, NPC behavior, particles, scripts, camera, and portals.

        Update order is important:
        1. Player movement (from input) - only if dialog not showing
        2. Player animation based on movement
        3. Physics engine (collision detection)
        4. NPC movements and pathfinding
        5. Particle effects
        6. Script system (executes active scripts)
        7. Camera smooth following
        8. Portal transition checks

        Args:
            delta_time: Time elapsed since last frame in seconds.

        Side effects:
            - Updates player position and animation
            - Updates NPC positions and animations
            - Updates particle positions
            - Executes script actions
            - Updates camera position
            - May trigger map transitions if player enters portal
        """
        # Handle scene transition states
        if self.transition_state != TransitionState.NONE:
            self._update_transition(delta_time)
            # During transition, don't update game logic
            return

        # Update dialog text reveal animation
        self.dialog_manager.update(delta_time)

        # Update player movement from input
        if self.player_sprite and self.input_manager and not self.dialog_manager.showing:
            dx, dy = self.input_manager.get_movement_vector()
            self.player_sprite.change_x = dx
            self.player_sprite.change_y = dy

            # Update player animation if using animated sprite
            if isinstance(self.player_sprite, AnimatedPlayer):
                moving = dx != 0 or dy != 0

                # Determine direction based on movement (prioritize horizontal over vertical)
                if dx > 0:
                    new_direction = "right"
                elif dx < 0:
                    new_direction = "left"
                elif dy > 0:
                    new_direction = "up"
                elif dy < 0:
                    new_direction = "down"
                else:
                    new_direction = self.player_sprite.current_direction

                # Only change direction when it actually changes (not every frame)
                if new_direction != self.player_sprite.current_direction:
                    self.player_sprite.set_direction(new_direction)

                # Update animation
                self.player_sprite.update_animation(delta_time, moving=moving)

        # Update physics
        if self.physics_engine:
            self.physics_engine.update()

        # Update NPC movements
        if self.npc_manager:
            self.npc_manager.update(delta_time, self.wall_list)

        # Update particles
        self.particle_manager.update(delta_time)

        # Update script system
        if self.game_context:
            self.script_manager.update(delta_time, self.game_context)

        # Smooth camera follow player
        if self.camera_manager and self.player_sprite:
            self.camera_manager.smooth_follow(
                self.player_sprite.center_x,
                self.player_sprite.center_y,
            )

        # Check for automatic portal transitions
        self._check_portal_transitions()

    def on_draw(self) -> None:
        """Render the game each frame (arcade lifecycle callback).

        Called automatically by arcade each frame. Renders in layers with two camera contexts:
        1. World camera: For game world (tiles, sprites, particles)
        2. Screen camera: For UI (instructions, debug info, dialog)

        Rendering order (world camera):
        - Scene layers (floor, walls, NPCs, etc.)
        - Particle effects

        Rendering order (screen camera):
        - Control instructions text
        - Debug info (if enabled)
        - Dialog overlay (if showing)

        Side effects:
            Draws to the window framebuffer.
        """
        self.clear()

        if self.camera:
            self.camera.use()

        # Draw the scene
        if self.scene:
            self.scene.draw()

        # Draw particles (in world coordinates)
        self.particle_manager.draw()

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

        # Draw debug info if enabled
        if self.debug_mode:
            self._draw_debug_info()

        # Draw dialog overlay
        self.dialog_manager.draw(self.window)

        # Draw transition overlay (crossfade effect)
        if self.transition_state != TransitionState.NONE:
            self._draw_transition_overlay()

    def _draw_transition_overlay(self) -> None:
        """Draw the transition overlay for scene fade (internal implementation).

        Draws a simple black overlay during scene transitions:
        - FADING_OUT: Black overlay fades in (alpha increases from 0 to 1)
        - FADING_IN: Black overlay fades out (alpha decreases from 1 to 0)

        This creates a fade-to-black effect when changing scenes.

        Side effects:
            - Draws a black rectangle overlay to the screen
        """
        arcade.camera.Camera2D().use()  # Draw in screen space

        # Draw black overlay with current alpha for both fade out and fade in
        # During fade out: alpha goes 0→1 (gets darker)
        # During fade in: alpha goes 1→0 (gets lighter)
        arcade.draw_lrbt_rectangle_filled(
            0,
            self.window.width,
            0,
            self.window.height,
            (0, 0, 0, int(self.transition_alpha * 255)),
        )

    def _draw_debug_info(self) -> None:
        """Draw debug information (internal implementation).

        Renders debug overlay showing player and NPC positions in tile coordinates and
        dialog levels. This is displayed in screen coordinates (not world coordinates)
        and is only shown when debug_mode is True.

        Debug info includes:
        - Player tile coordinates (if player exists)
        - For each visible NPC:
          - Name
          - Tile coordinates
          - Current dialog level

        Side effects:
            - Draws text to screen using arcade.Text objects
        """
        # Build debug text content
        debug_lines = []
        y_offset = 30

        settings = self.window.settings
        # Collect player position
        if self.player_sprite:
            player_tile_x = int(self.player_sprite.center_x / settings.tile_size)
            player_tile_y = int(self.player_sprite.center_y / settings.tile_size)
            debug_lines.append((f"Player: tile ({player_tile_x}, {player_tile_y})", arcade.color.GREEN))

        # Collect NPC positions
        if self.npc_manager:
            for npc_name, npc_state in self.npc_manager.npcs.items():
                if npc_state.sprite.visible:
                    tile_x = int(npc_state.sprite.center_x / settings.tile_size)
                    tile_y = int(npc_state.sprite.center_y / settings.tile_size)
                    debug_lines.append(
                        (f"{npc_name}: tile ({tile_x}, {tile_y}) level {npc_state.dialog_level}", arcade.color.YELLOW)
                    )

        # Create or update text objects
        num_needed = len(debug_lines)
        num_existing = len(self.debug_text_objects)

        # Remove extra text objects if we have too many
        if num_existing > num_needed:
            self.debug_text_objects = self.debug_text_objects[:num_needed]

        # Update or create text objects
        for i, (text, color) in enumerate(debug_lines):
            if i < len(self.debug_text_objects):
                # Update existing text object
                self.debug_text_objects[i].text = text
                self.debug_text_objects[i].color = color
                self.debug_text_objects[i].y = y_offset
            else:
                # Create new text object
                text_obj = arcade.Text(
                    text,
                    10,
                    y_offset,
                    color,
                    font_size=12,
                )
                self.debug_text_objects.append(text_obj)

            y_offset += 20

        # Draw all text objects
        for text_obj in self.debug_text_objects:
            text_obj.draw()

    def on_key_press(self, symbol: int, modifiers: int) -> bool | None:
        """Handle keyboard input (arcade lifecycle callback).

        Processes all keyboard input for the game including movement, menu navigation,
        interaction, debug toggles, and save/load. Dialog is advanced or NPCs are
        interacted with via SPACE.

        Supported keys:
        - ESC: Show menu (blocked during dialog, active scripts, or NPC movement)
        - Shift+D: Toggle debug mode
        - F5: Quick save
        - F9: Quick load
        - I: Show inventory
        - SPACE: Advance dialog OR interact with NPC/object
        - Arrow keys / WASD: Player movement (registered with input_manager)

        Menu access protection:
        The menu cannot be accessed while a dialog is showing, during active script
        sequences, or when NPCs are moving. This prevents save/load operations during
        transient game states and ensures clean state transitions.

        Args:
            symbol: Arcade key constant (e.g., arcade.key.SPACE).
            modifiers: Bitfield of modifier keys held (e.g., arcade.key.MOD_SHIFT).

        Returns:
            None to allow other handlers to process the key.

        Side effects:
            - May show menu/inventory view (if not blocked)
            - May toggle debug_mode
            - May save/load game state
            - May advance dialog or interact with NPCs
            - Registers movement keys with input_manager
            - Logs debug messages when menu access is blocked
        """
        # Menu (disabled during dialog, active scripts, or NPC movement)
        if symbol == arcade.key.ESCAPE:
            # Don't allow menu access during dialog or active script sequences
            if self.dialog_manager.showing:
                logger.debug("Menu access blocked: dialog is active")
                return None
            if self.script_manager.active_sequences:
                logger.debug("Menu access blocked: script sequence is active")
                return None
            if self.npc_manager and self.npc_manager.has_moving_npcs():
                logger.debug("Menu access blocked: NPCs are moving")
                return None
            # Auto-save before pausing
            if self.player_sprite and self.map_file:
                self.save_manager.auto_save(
                    player_x=self.player_sprite.center_x,
                    player_y=self.player_sprite.center_y,
                    current_map=self.map_file,
                    npc_manager=self.npc_manager,
                    inventory_manager=self.inventory_manager,
                    audio_manager=self.audio_manager,
                    script_manager=self.script_manager,
                )
            # Pause game (preserve game view for quick resume)
            self.view_manager.show_menu(from_game_pause=True)
        # Debug toggle
        elif symbol == arcade.key.D and (modifiers & arcade.key.MOD_SHIFT):
            self.debug_mode = not self.debug_mode
        # Quick save
        elif symbol == arcade.key.F5:
            self.quick_save()
        # Quick load
        elif symbol == arcade.key.F9:
            self.quick_load()
        # Inventory
        elif symbol == arcade.key.I:
            self.view_manager.show_inventory()
        # Interaction with NPCs
        elif symbol == arcade.key.SPACE and self.player_sprite:
            if self.dialog_manager.showing:
                # Handle dialog advancement or closing
                dialog_closed = self.dialog_manager.advance_page()
                if dialog_closed:
                    self._publish_dialog_closed_event()
            else:
                self._try_interact_with_npc()
        # Movement controls - register with input manager
        elif self.input_manager and symbol in (
            arcade.key.UP,
            arcade.key.DOWN,
            arcade.key.LEFT,
            arcade.key.RIGHT,
            arcade.key.W,
            arcade.key.A,
            arcade.key.S,
            arcade.key.D,
        ):
            self.input_manager.on_key_press(symbol)

        return None

    def on_key_release(self, symbol: int, modifiers: int) -> bool | None:
        """Handle key releases (arcade lifecycle callback).

        Processes keyboard key release events, primarily for movement controls. When the
        player releases a movement key, this unregisters it with the input manager so the
        player stops moving in that direction.

        Args:
            symbol: Arcade key constant for the released key (e.g., arcade.key.W).
            modifiers: Bitfield of modifier keys held (unused).

        Returns:
            None to allow other handlers to process the key.

        Side effects:
            - Unregisters movement keys with input_manager
        """
        # Movement controls - unregister with input manager
        if self.input_manager and symbol in (
            arcade.key.UP,
            arcade.key.DOWN,
            arcade.key.LEFT,
            arcade.key.RIGHT,
            arcade.key.W,
            arcade.key.A,
            arcade.key.S,
            arcade.key.D,
        ):
            self.input_manager.on_key_release(symbol)

        return None

    def _start_scene_transition(self, target_map: str, spawn_waypoint: str | None = None) -> None:
        """Start a scene transition with fade effect (internal implementation).

        Initiates a simple fade-to-black transition to a new map:
        1. Sets up pending map and spawn point
        2. Starts the fade-out state

        Args:
            target_map: Name of the target map file (e.g., "Forest.tmx").
            spawn_waypoint: Optional waypoint name in target map for player spawn.

        Side effects:
            - Sets pending_map_file and pending_spawn_waypoint
            - Changes transition_state to FADING_OUT
            - Resets transition_alpha to 0
        """
        # Don't start a new transition if one is already in progress
        if self.transition_state != TransitionState.NONE:
            logger.warning("Transition already in progress, ignoring new transition request")
            return

        # Store the target map and spawn point
        self.pending_map_file = target_map
        self.pending_spawn_waypoint = spawn_waypoint

        # Start fading out
        self.transition_state = TransitionState.FADING_OUT
        self.transition_alpha = 0.0

        logger.info("Started scene transition to %s", target_map)

    def _update_transition(self, delta_time: float) -> None:
        """Update the scene transition animation (internal implementation).

        Handles the state machine for fade transitions between scenes:
        1. FADING_OUT: Increase alpha (fade to black)
        2. LOADING: Load the new map while screen is black
        3. FADING_IN: Decrease alpha (fade from black to reveal new scene)

        Args:
            delta_time: Time elapsed since last frame in seconds.

        Side effects:
            - Updates transition_alpha
            - May change transition_state
            - May call setup() to load new map
        """
        if self.transition_state == TransitionState.FADING_OUT:
            # Fade out: increase alpha from 0 to 1
            self.transition_alpha += self.transition_speed * delta_time
            logger.debug("FADING_OUT: alpha=%.2f", self.transition_alpha)
            if self.transition_alpha >= 1.0:
                self.transition_alpha = 1.0
                self.transition_state = TransitionState.LOADING
                logger.info("Fade out complete, loading new scene")

        elif self.transition_state == TransitionState.LOADING:
            # Load the new map
            if self.pending_map_file:
                logger.info("Loading new map: %s", self.pending_map_file)
                # Cache NPC state for current scene before transitioning
                if self.map_file and self.npc_manager:
                    self._scene_state_cache.cache_scene_state(self.map_file, self.npc_manager)
                self.map_file = self.pending_map_file
                self.spawn_waypoint = self.pending_spawn_waypoint
                self.pending_map_file = None
                self.pending_spawn_waypoint = None
                self.setup()  # Load the new scene
            self.transition_state = TransitionState.FADING_IN
            logger.info("New scene loaded, starting fade in (alpha=%.2f)", self.transition_alpha)

        elif self.transition_state == TransitionState.FADING_IN:
            # Fade in: decrease alpha from 1 to 0
            self.transition_alpha -= self.transition_speed * delta_time
            logger.debug("FADING_IN: alpha=%.2f", self.transition_alpha)
            if self.transition_alpha <= 0.0:
                self.transition_alpha = 0.0
                self.transition_state = TransitionState.NONE
                logger.info("Fade in complete, transition finished")

    def _check_portal_transitions(self) -> None:
        """Check if player is on an active portal and trigger map transition (internal implementation).

        Tests whether the player sprite is overlapping an active portal. If a portal is
        active (conditions met), starts a fade transition to the target map.

        Portal activation is handled by portal_manager, which checks distance and any
        custom conditions (like required NPC dialog levels).

        Side effects:
            - Starts scene transition with fade-to-black effect
            - Sets pending map and spawn waypoint
            - Logs portal transition info
        """
        if not self.player_sprite or not self.portal_manager:
            return

        active_portal = self.portal_manager.get_active_portal(
            self.player_sprite,
            npc_manager=self.npc_manager,
        )

        if active_portal:
            logger.info(
                "Portal '%s' activated, transitioning to %s",
                active_portal.name,
                active_portal.target_map,
            )

            # Start the crossfade transition
            self._start_scene_transition(
                active_portal.target_map,
                active_portal.spawn_waypoint,
            )

    def _try_interact_with_npc(self) -> None:
        """Try to interact with a nearby NPC or object (internal implementation).

        Checks for interactive objects and NPCs near the player and handles interaction
        when the player presses SPACE. Objects take priority over NPCs.

        Interaction workflow:
        1. Check for nearby interactive objects first
           - Publish ObjectInteractedEvent
           - Handle built-in interaction (message, toggle, etc.)
           - Emit sparkle particles
        2. If no object, check for nearby NPCs
           - Trigger NPC's interact animation
           - Publish NPCInteractedEvent
           - Get dialog for current level and scene
           - Show dialog if conditions met, or execute on_condition_fail actions
           - Play NPC sound effect
           - Emit sparkle particles

        Side effects:
            - Publishes events to event_bus
            - May show dialog via dialog_manager
            - Plays sound effects
            - Emits particle effects
            - Sets current_npc_name and current_npc_dialog_level for event tracking
        """
        if not self.player_sprite:
            return

        # First check for interactive objects
        if self.interaction_manager:
            nearby_object = self.interaction_manager.get_nearby_object(self.player_sprite)
            if nearby_object:
                # Publish object interacted event for script system
                self.event_bus.publish(ObjectInteractedEvent(object_name=nearby_object.name))

                # Handle built-in interaction types (message, toggle, etc.)
                self.interaction_manager.handle_interaction(
                    nearby_object,
                    dialog_manager=self.dialog_manager,
                )
                return

        # Then check for NPCs
        if not self.npc_manager:
            return
        nearby = self.npc_manager.get_nearby_npc(self.player_sprite)
        if not nearby:
            return

        npc_sprite, npc_name, dialog_level = nearby

        # Trigger interact animation if it's an AnimatedNPC
        if isinstance(npc_sprite, AnimatedNPC):
            logger.debug("Starting interact animation for %s", npc_name)
            npc_sprite.start_interact_animation()
        else:
            logger.debug("NPC %s is not an AnimatedNPC, skipping interact animation", npc_name)

        # Publish NPC interacted event for script system
        self.event_bus.publish(NPCInteractedEvent(npc_name=npc_name, dialog_level=dialog_level))

        # Get dialog for this NPC (pass current scene for scene-aware dialogs)
        dialog_config, on_condition_fail_actions = self.npc_manager.get_dialog(
            npc_name, dialog_level, self.current_scene
        )

        if dialog_config:
            # Conditions met - show normal NPC dialog
            self.dialog_manager.show_dialog(npc_name.title(), dialog_config.text)
            self.current_npc_name = npc_name
            self.current_npc_dialog_level = dialog_level

        elif on_condition_fail_actions:
            # Conditions failed - execute on_condition_fail actions
            logger.debug("Executing on_condition_fail actions for %s", npc_name)
            # Parse action dictionaries into Action objects
            npc_dialogs = self.npc_manager.dialogs  # Raw dialog data for parsing
            parsed_actions = self.script_manager.parse_actions(on_condition_fail_actions, npc_dialogs)

            if parsed_actions and self.game_context:
                sequence = ActionSequence(parsed_actions)
                sequence.execute(self.game_context)

    def _publish_dialog_closed_event(self) -> None:
        """Publish dialog closed event to event bus (internal implementation).

        Creates and publishes a DialogClosedEvent with the current NPC's name and actual
        dialog level. The dialog level is fetched from the NPC manager to ensure accuracy
        (it may have changed during the dialog).

        This event is used by the script system to trigger follow-up scripts after dialog
        completes.

        Side effects:
            - Publishes DialogClosedEvent to event_bus
            - Clears current_npc_name and current_npc_dialog_level tracking
            - Logs event publication
        """
        if self.current_npc_name:
            # Get the actual current level from NPC manager (in case it changed during dialog)
            npc_state = self.npc_manager.npcs.get(self.current_npc_name) if self.npc_manager else None
            actual_level = npc_state.dialog_level if npc_state else self.current_npc_dialog_level

            self.event_bus.publish(
                DialogClosedEvent(
                    npc_name=self.current_npc_name,
                    dialog_level=actual_level,
                )
            )
            logger.debug(
                "Published DialogClosedEvent - NPC: %s, Level: %d",
                self.current_npc_name,
                actual_level,
            )

        # Clear tracking
        self.current_npc_name = ""
        self.current_npc_dialog_level = 0

    def quick_save(self) -> None:
        """Quick save game state to auto-save slot (triggered by F5).

        Saves current player position, map, NPC dialog levels, and inventory to the
        auto-save slot. Plays a save sound effect on success.

        Side effects:
            - Writes save file to disk
            - Plays save.wav sound effect on success
            - Logs save status
        """
        if not self.player_sprite or not self.map_file:
            return

        success = self.save_manager.auto_save(
            player_x=self.player_sprite.center_x,
            player_y=self.player_sprite.center_y,
            current_map=self.map_file,
            npc_manager=self.npc_manager,
            inventory_manager=self.inventory_manager,
            audio_manager=self.audio_manager,
            script_manager=self.script_manager,
        )

        if success:
            self.audio_manager.play_sfx("save.wav")
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
        save_data = self.save_manager.load_auto_save()

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

        # Restore all manager states using the convenience method
        restored_objects, scene_states = self.save_manager.restore_all_state(
            save_data, self.npc_manager, self.inventory_manager, self.audio_manager, self.script_manager
        )

        # Update script manager's interacted_objects
        self.script_manager.interacted_objects = restored_objects

        # Restore scene state cache for NPC persistence across scene transitions
        if scene_states:
            self._scene_state_cache.from_dict(scene_states)

        self.audio_manager.play_sfx("load.wav")
        logger.info("Quick load completed from %s", save_data.save_timestamp)

    def trigger_post_inventory_dialog(self) -> None:
        """Publish inventory closed event when returning from inventory view.

        Called by the inventory view when closing to notify scripts that the inventory
        was accessed. Scripts can use this event to trigger story progression based on
        the player opening their inventory.

        Side effects:
            - Publishes InventoryClosedEvent to event_bus
            - Logs event publication
        """
        logger.info("Publishing InventoryClosedEvent")
        self.event_bus.publish(InventoryClosedEvent(has_been_accessed=self.inventory_manager.has_been_accessed))

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
        # Cache NPC state for this scene before clearing (for scene transitions)
        if self.map_file and self.npc_manager:
            self._scene_state_cache.cache_scene_state(self.map_file, self.npc_manager)

        # Auto-save on cleanup (includes cached scene states for persistence)
        if self.player_sprite and self.map_file:
            self.save_manager.auto_save(
                player_x=self.player_sprite.center_x,
                player_y=self.player_sprite.center_y,
                current_map=self.map_file,
                npc_manager=self.npc_manager,
                inventory_manager=self.inventory_manager,
                audio_manager=self.audio_manager,
                script_manager=self.script_manager,
                scene_states=self._scene_state_cache.to_dict(),
            )

        # Stop audio
        self.audio_manager.stop_music()

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
        self.physics_engine = None
        self.camera = None

        # Reset managers
        self.dialog_manager.close_dialog()
        if self.npc_manager:
            self.npc_manager.npcs.clear()
        if self.interaction_manager:
            self.interaction_manager.clear()
        if self.portal_manager:
            self.portal_manager.clear()
        self.particle_manager.clear()
        self.script_manager.clear()
        self.event_bus.clear()

        # Reset initialization flag so game will be set up again on next show
        self.initialized = False
