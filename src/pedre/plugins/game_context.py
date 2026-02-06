"""Game context for passing state to actions and scripts.

This module provides the GameContext class, which serves as a central registry
for all game plugins and state. The context is passed to all actions and scripts,
giving them access to the plugins and resources they need to interact with the
game world.

The GameContext pattern enables:
- Actions to be reusable and testable by providing dependencies explicitly
- Scripts to interact with any game plugin without tight coupling
- Easy mocking and testing by swapping out individual plugins
- Pluggable architecture where custom plugins can be added without modifying core code

Key components stored in the context:
- Plugins registry: All pluggable plugins accessed via get_plugin()
- View references: Game view for accessing view-specific functionality

Example usage:
    # Create context with game state
    context = GameContext(
        event_bus=event_bus
    )

    # Register plugins (done by PluginLoader)
    context.register_plugin("dialog", dialog_plugin)
    context.register_plugin("npc", npc_plugin)

    # Actions access plugins by name
    dialog = context.dialog_plugin
    if dialog:
        dialog.show_dialog("Hello!")
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import arcade

    from pedre.events import EventBus
    from pedre.plugins.audio import AudioBasePlugin
    from pedre.plugins.base import BasePlugin
    from pedre.plugins.cache import CacheBasePlugin
    from pedre.plugins.camera import CameraBasePlugin
    from pedre.plugins.dialog import DialogBasePlugin
    from pedre.plugins.input import InputBasePlugin
    from pedre.plugins.interaction import InteractionBasePlugin
    from pedre.plugins.inventory import InventoryBasePlugin
    from pedre.plugins.npc import NPCBasePlugin
    from pedre.plugins.particle import ParticleBasePlugin
    from pedre.plugins.pathfinding import PathfindingBasePlugin
    from pedre.plugins.pause_menu import PauseMenuBasePlugin
    from pedre.plugins.physics import PhysicsBasePlugin
    from pedre.plugins.player import PlayerBasePlugin
    from pedre.plugins.save import GameSaveData, SaveBasePlugin
    from pedre.plugins.scene import SceneBasePlugin
    from pedre.plugins.script import ScriptBasePlugin
    from pedre.plugins.waypoint import WaypointBasePlugin


class GameContext:
    """Central context object providing access to all game plugins.

    The GameContext acts as a plugin registry and state container that holds
    references to all game plugins and essential state. It's passed to every
    action's execute() method and every plugin's lifecycle methods.

    Plugins are accessed by name using get_plugin(), which returns the plugin
    or None if not registered. This allows for a fully pluggable architecture
    where custom plugins can be added without modifying the context class.

    This design pattern provides several benefits:
    - **Pluggability**: Any plugin can be registered and accessed by name
    - **Testability**: Plugins can be mocked by registering test implementations
    - **Flexibility**: Plugins are decoupled from how they're created/configured
    - **Extensibility**: Custom plugins integrate the same way as built-in ones

    Attributes:
        event_bus: Publish/subscribe event plugin for decoupled communication.
        window: Reference to the arcade Window instance.
    """

    audio_plugin: AudioBasePlugin
    cache_plugin: CacheBasePlugin
    save_plugin: SaveBasePlugin
    npc_plugin: NPCBasePlugin
    scene_plugin: SceneBasePlugin
    camera_plugin: CameraBasePlugin
    dialog_plugin: DialogBasePlugin
    pause_menu_plugin: PauseMenuBasePlugin
    inventory_plugin: InventoryBasePlugin
    interaction_plugin: InteractionBasePlugin
    pathfinding_plugin: PathfindingBasePlugin
    particle_plugin: ParticleBasePlugin
    input_plugin: InputBasePlugin
    physics_plugin: PhysicsBasePlugin
    script_plugin: ScriptBasePlugin
    player_plugin: PlayerBasePlugin
    waypoint_plugin: WaypointBasePlugin

    def __init__(
        self,
        event_bus: EventBus,
        window: arcade.Window,
    ) -> None:
        """Initialize game context with game state.

        Creates a new GameContext instance with essential game state. Plugins
        are registered separately via register_plugin() after instantiation,
        typically by the PluginLoader.

        Args:
            event_bus: Central event plugin for publishing and subscribing to game events.
                      Actions can publish events to trigger scripts or notify other plugins.
            window: Reference to the arcade Window instance. Used by plugins that need
                   to access window properties (size, rendering context, etc).

        """
        self.event_bus = event_bus
        self.window = window

        # Registry for all pluggable plugins (accessed via get_plugin)
        self._plugins: dict[str, BasePlugin] = {}

        # Pending save data for two-phase restoration
        self._pending_save_data: GameSaveData | None = None

    def register_plugin(self, name: str, plugin: BasePlugin) -> None:
        """Register a pluggable plugin with the context.

        This method is called by the PluginLoader to register plugins that have been
        instantiated. Once registered, the plugin can be accessed by name using
        get_plugin().

        Args:
            name: Unique identifier for the plugin (e.g., "audio", "dialog", "npc").
            plugin: The plugin instance to register.

        Example:
            # PluginLoader calls this for each instantiated plugin
            context.register_plugin("weather", weather_plugin)
            context.register_plugin("dialog", dialog_plugin)
        """
        self._plugins[name] = plugin

        if plugin.role:
            setattr(self, plugin.role, plugin)

    def get_plugin(self, name: str) -> BasePlugin | None:
        """Get a registered plugin by name.

        This is the primary method for accessing game plugins. All plugins (built-in
        and custom) are accessed this way, enabling a fully pluggable architecture.

        Args:
            name: The plugin's unique identifier (e.g., "audio", "dialog", "npc").

        Returns:
            The plugin instance if found, None otherwise.

        Example:
            # Get plugins by name
            dialog = context.get_plugin("dialog")
            if dialog:
                dialog.show_dialog("Hello!")

            # Custom plugins work the same way
            weather = context.get_plugin("weather")
            if weather:
                weather.set_rain(intensity=0.7)
        """
        return self._plugins.get(name)

    def get_plugins(self) -> dict[str, BasePlugin]:
        """Get all registered plugins."""
        return self._plugins

    def set_pending_save_data(self, save_data: GameSaveData | None) -> None:
        """Store save data for Phase 2 restoration after sprites exist."""
        self._pending_save_data = save_data

    def get_pending_save_data(self) -> GameSaveData | None:
        """Get pending save data for Phase 2 restoration."""
        return self._pending_save_data

    def clear_pending_save_data(self) -> None:
        """Clear pending save data after restoration is complete."""
        self._pending_save_data = None

    def start_new_game(self) -> None:
        """Start a new game with fresh state.

        Facade method that delegates to the game coordinator. This provides
        a cleaner API for plugins to start new games without accessing the
        window directly.

        Side effects:
            - Calls game.start_new_game() via window
        """
        if hasattr(self.window, "game"):
            self.window.game.start_new_game()

    def load_game(self, save_data: GameSaveData) -> None:
        """Load a game from save data.

        Facade method that delegates to the game coordinator. This provides
        a cleaner API for plugins to load games without accessing the window
        directly.

        Args:
            save_data: GameSaveData instance containing all saved game state.

        Side effects:
            - Calls game.load_game() via window
        """
        if hasattr(self.window, "game"):
            self.window.game.load_game(save_data)

    def continue_game(self) -> None:
        """Continue/resume the current game.

        Facade method that delegates to the game coordinator.

        Side effects:
            - Calls game.continue_game() via window
        """
        if hasattr(self.window, "game"):
            self.window.game.continue_game()
