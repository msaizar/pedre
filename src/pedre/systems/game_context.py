"""Game context for passing state to actions and scripts.

This module provides the GameContext class, which serves as a central registry
for all game systems and state. The context is passed to all actions and scripts,
giving them access to the systems and resources they need to interact with the
game world.

The GameContext pattern enables:
- Actions to be reusable and testable by providing dependencies explicitly
- Scripts to interact with any game system without tight coupling
- Easy mocking and testing by swapping out individual systems
- Centralized access to shared resources like sprite lists and waypoints
- Pluggable architecture where custom systems can be added without modifying core code

Key components stored in the context:
- Systems registry: All pluggable systems accessed via get_system()
- Game state: Player sprite, wall list, current scene
- Map data: Waypoints, interacted objects
- View references: Game view for accessing view-specific functionality

Example usage:
    # Create context with game state
    context = GameContext(
        event_bus=event_bus,
        player_sprite=player,
        current_scene="town"
    )

    # Register systems (done by SystemLoader)
    context.register_system("dialog", dialog_manager)
    context.register_system("npc", npc_manager)

    # Actions access systems by name
    dialog = context.dialog_manager
    if dialog:
        dialog.show_dialog("Hello!")
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import arcade

    from pedre.events import EventBus
    from pedre.systems.audio.base import AudioBaseManager
    from pedre.systems.base import BaseSystem
    from pedre.systems.camera.base import CameraBaseManager
    from pedre.systems.dialog.base import DialogBaseManager
    from pedre.systems.input.base import InputBaseManager
    from pedre.systems.interaction.base import InteractionBaseManager
    from pedre.systems.inventory.base import InventoryBaseManager
    from pedre.systems.npc.base import NPCBaseManager
    from pedre.systems.particle.base import ParticleBaseManager
    from pedre.systems.pathfinding.base import PathfindingBaseManager
    from pedre.systems.physics.base import PhysicsBaseManager
    from pedre.systems.save.base import SaveBaseManager
    from pedre.systems.scene.base import SceneBaseManager
    from pedre.systems.script.base import ScriptBaseManager


class GameContext:
    """Central context object providing access to all game systems.

    The GameContext acts as a system registry and state container that holds
    references to all game systems and essential state. It's passed to every
    action's execute() method and every system's lifecycle methods.

    Systems are accessed by name using get_system(), which returns the system
    or None if not registered. This allows for a fully pluggable architecture
    where custom systems can be added without modifying the context class.

    This design pattern provides several benefits:
    - **Pluggability**: Any system can be registered and accessed by name
    - **Testability**: Systems can be mocked by registering test implementations
    - **Flexibility**: Systems are decoupled from how they're created/configured
    - **Extensibility**: Custom systems integrate the same way as built-in ones

    Attributes:
        event_bus: Publish/subscribe event system for decoupled communication.
        window: Reference to the arcade Window instance.
        player_sprite: Reference to the player's sprite (or None if not spawned).
        current_scene: Name of the currently loaded map/scene.
        waypoints: Dictionary mapping waypoint names to (tile_x, tile_y) coordinates.
        interacted_objects: Set of object names that the player has interacted with.
        next_spawn_waypoint: Waypoint name for next spawn (portal transitions).
    """

    audio_manager: AudioBaseManager
    save_manager: SaveBaseManager
    npc_manager: NPCBaseManager
    scene_manager: SceneBaseManager
    camera_manager: CameraBaseManager
    dialog_manager: DialogBaseManager
    inventory_manager: InventoryBaseManager
    interaction_manager: InteractionBaseManager
    pathfinding_manager: PathfindingBaseManager
    particle_manager: ParticleBaseManager
    input_manager: InputBaseManager
    physics_manager: PhysicsBaseManager
    script_manager: ScriptBaseManager

    def __init__(
        self,
        event_bus: EventBus,
        window: arcade.Window,
        player_sprite: arcade.Sprite | None = None,
        current_scene: str = "",
        waypoints: dict[str, tuple[int, int]] | None = None,
        next_spawn_waypoint: str | None = None,
    ) -> None:
        """Initialize game context with game state.

        Creates a new GameContext instance with essential game state. Systems
        are registered separately via register_system() after instantiation,
        typically by the SystemLoader.

        Args:
            event_bus: Central event system for publishing and subscribing to game events.
                      Actions can publish events to trigger scripts or notify other systems.
            window: Reference to the arcade Window instance. Used by systems that need
                   to access window properties (size, rendering context, etc).
            player_sprite: Reference to the player's sprite. May be None if player hasn't
                         spawned yet. Updated via update_player() when player is created.
            current_scene: Name of the currently loaded map/scene (e.g., "town", "forest").
                         Used to track which map is active for conditional logic.
            waypoints: Dictionary mapping waypoint names to (tile_x, tile_y) coordinates.
                      NPCs use these to navigate to named locations.
            next_spawn_waypoint: Waypoint name for next spawn (set by SceneManager for
                               portal transitions). Read by PlayerManager and cleared after use.
        """
        self.event_bus = event_bus
        self.window = window
        self.player_sprite = player_sprite
        self.current_scene = current_scene
        self.waypoints = waypoints or {}
        self.next_spawn_waypoint = next_spawn_waypoint

        # Registry for all pluggable systems (accessed via get_system)
        self._systems: dict[str, BaseSystem] = {}

    def update_player(self, player_sprite: arcade.Sprite | None) -> None:
        """Update the player sprite reference in the context.

        This method is called when the player sprite is created or changes, such as when
        spawning into a new map or respawning after a game over. Actions that need to
        access the player sprite (for positioning, collision checks, etc.) will use the
        updated reference.

        Setting player_sprite to None is valid and indicates that no player is currently
        spawned in the game world.

        Args:
            player_sprite: The new player sprite reference, or None if no player exists.
        """
        self.player_sprite = player_sprite

    def update_scene(self, scene_name: str) -> None:
        """Update the current scene/map name in the context.

        This method is called when transitioning between different maps or areas in the game
        world. The scene name is used by scripts and conditions to execute map-specific logic.

        Args:
            scene_name: The name identifier of the new scene/map being entered.
        """
        self.current_scene = scene_name

    def update_waypoints(self, waypoints: dict[str, tuple[int, int]]) -> None:
        """Update the waypoints dictionary for the current map.

        This method is called when loading a new map that contains waypoint objects.
        Waypoints are named locations in the map that NPCs can navigate to.

        Args:
            waypoints: Dictionary mapping waypoint names to (tile_x, tile_y) coordinates.
        """
        self.waypoints = waypoints

    def register_system(self, name: str, system: BaseSystem) -> None:
        """Register a pluggable system with the context.

        This method is called by the SystemLoader to register systems that have been
        instantiated. Once registered, the system can be accessed by name using
        get_system().

        Args:
            name: Unique identifier for the system (e.g., "audio", "dialog", "npc").
            system: The system instance to register.

        Example:
            # SystemLoader calls this for each instantiated system
            context.register_system("weather", weather_manager)
            context.register_system("dialog", dialog_manager)
        """
        self._systems[name] = system

        if system.role:
            setattr(self, system.role, system)

    def get_system(self, name: str) -> BaseSystem | None:
        """Get a registered system by name.

        This is the primary method for accessing game systems. All systems (built-in
        and custom) are accessed this way, enabling a fully pluggable architecture.

        Args:
            name: The system's unique identifier (e.g., "audio", "dialog", "npc").

        Returns:
            The system instance if found, None otherwise.

        Example:
            # Get systems by name
            dialog = context.get_system("dialog")
            if dialog:
                dialog.show_dialog("Hello!")

            # Custom systems work the same way
            weather = context.get_system("weather")
            if weather:
                weather.set_rain(intensity=0.7)
        """
        return self._systems.get(name)

    def get_systems(self) -> dict[str, BaseSystem]:
        """Get all registered systems."""
        return self._systems
