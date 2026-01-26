"""Game context for passing state to actions and scripts.

This module provides the GameContext class, which serves as a central registry
for all game systems and state. The context is passed to all actions and scripts,
giving them access to the systems and resources they need to interact with the
game world.

The GameContext pattern enables:
- Actions to be reusable and testable by providing dependencies explicitly
- Scripts to interact with any game system without tight coupling
- Easy mocking and testing by swapping out individual systems
- Pluggable architecture where custom systems can be added without modifying core code

Key components stored in the context:
- Systems registry: All pluggable systems accessed via get_system()
- View references: Game view for accessing view-specific functionality

Example usage:
    # Create context with game state
    context = GameContext(
        event_bus=event_bus
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
    from pedre.systems.player.base import PlayerBaseManager
    from pedre.systems.save.base import SaveBaseManager
    from pedre.systems.scene.base import SceneBaseManager
    from pedre.systems.script.base import ScriptBaseManager
    from pedre.systems.waypoint.base import WaypointBaseManager


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
    player_manager: PlayerBaseManager
    waypoint_manager: WaypointBaseManager

    def __init__(
        self,
        event_bus: EventBus,
        window: arcade.Window,
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

        """
        self.event_bus = event_bus
        self.window = window

        # Registry for all pluggable systems (accessed via get_system)
        self._systems: dict[str, BaseSystem] = {}

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
