"""Base class for pluggable systems.

This module provides the abstract base class that all pluggable systems must inherit from.
Systems are the building blocks of the game engine, each handling a specific aspect
of the game (audio, NPCs, inventory, etc.).

Example:
    Creating a custom system::

        from pedre.systems.base import BaseSystem
        from pedre.systems.registry import SystemRegistry
        from pedre.conf import settings

        @SystemRegistry.register
        class WeatherManager(BaseSystem):
            name = "weather"
            dependencies = ["particle", "audio"]

            def setup(self, context):
                self.current_weather = "clear"
                self.update_interval = settings.WEATHER_UPDATE_INTERVAL

            def update(self, delta_time, context):
                if self.current_weather == "rain":
                    context.get_system("particle").emit("rain")
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    import arcade

    from pedre.systems.game_context import GameContext


class BaseSystem(ABC):
    """Base class for all pluggable systems.

    Systems are the building blocks of the game engine. Each system handles
    a specific aspect of the game (audio, NPCs, inventory, etc.).

    To create a custom system, subclass BaseSystem and implement the required
    methods. Use the @SystemRegistry.register decorator to make the system
    available for loading.

    Attributes:
        name: Unique identifier for the system. Must be defined as a class variable.
        dependencies: List of system names this system depends on. Systems are
            initialized in dependency order, ensuring dependencies are available
            when setup() is called.

    Example:
        Creating a weather system::

            from pedre.conf import settings

            @SystemRegistry.register
            class WeatherManager(BaseSystem):
                name = "weather"
                dependencies = ["particle"]

                def setup(self, context):
                    self.intensity = 0.0
                    self.update_interval = settings.WEATHER_UPDATE_INTERVAL

                def set_weather(self, weather_type, intensity):
                    self.current_weather = weather_type
                    self.intensity = intensity
    """

    # System identifier (must be unique across all systems)
    name: ClassVar[str]
    role: str | None = None
    # Other systems this one depends on (by name)
    # Systems are initialized in dependency order
    dependencies: ClassVar[list[str]] = []

    @abstractmethod
    def setup(self, context: GameContext) -> None:
        """Initialize the system when a scene loads.

        This method is called after all systems have been instantiated but before
        the game loop starts. Use it to initialize state, subscribe to events,
        and configure the system based on settings.

        Args:
            context: Game context providing access to other systems via get_system().

        Example:
            from pedre.conf import settings

            def setup(self, context):
                self.event_bus = context.event_bus
                self.volume = settings.MUSIC_VOLUME
                self.event_bus.subscribe(SceneStartEvent, self._on_scene_start)
        """

    def load_from_tiled(
        self,
        tile_map: arcade.TileMap,
        arcade_scene: arcade.Scene,
        context: GameContext,
    ) -> None:
        """Load system-specific data from Tiled map (optional hook).

        This method is called after the tile map and arcade scene have been
        loaded but before physics initialization. Systems should extract their
        data from the Tiled map and register/configure their entities.

        Call order:
        1. SceneManager loads tile_map and arcade_scene
        2. SceneManager extracts collision layers into context.wall_list
        3. load_from_tiled() called on all systems in dependency order
           - WaypointManager populates context.waypoints
           - PortalManager registers portals
           - InteractionManager registers interactive objects
           - PlayerManager creates player sprite (uses waypoints)
           - NPCManager creates NPC sprites (depends on player)
        4. Physics setup, pathfinding setup, camera setup

        Args:
            tile_map: Loaded arcade.TileMap instance.
            arcade_scene: arcade.Scene created from tile_map.
            context: GameContext with wall_list already populated.

        Example:
            from pedre.conf import settings

            def load_from_tiled(self, tile_map, arcade_scene, context):
                portal_layer = tile_map.object_lists.get("Portals")
                if not portal_layer:
                    return

                for portal_obj in portal_layer:
                    sprite = self._create_sprite_from_tiled(portal_obj)
                    self.register_portal(sprite, portal_obj.name)
        """
        return

    def update(self, delta_time: float, context: GameContext) -> None:
        """Called every frame during the game loop.

        Override this method to implement per-frame logic such as animations,
        physics updates, or time-based effects.

        Args:
            delta_time: Time elapsed since the last frame, in seconds.
            context: Game context providing access to other systems.

        Example:
            def update(self, delta_time, context):
                self.animation_timer += delta_time
                if self.animation_timer > self.frame_duration:
                    self.advance_frame()
        """
        return

    def on_draw(self, context: GameContext) -> None:
        """Called during the draw phase of each frame (world coordinates).

        Override this method to render visual elements managed by this system
        in world coordinates (affected by camera).

        Args:
            context: Game context providing access to other systems.
        """
        return

    def on_draw_ui(self, context: GameContext) -> None:
        """Called during the draw phase of each frame (screen coordinates).

        Override this method to render UI elements or overlays in screen coordinates
        (not affected by camera).

        Args:
            context: Game context providing access to other systems.
        """
        return

    def cleanup(self) -> None:
        """Called when the scene unloads or the game exits.

        Override this method to release resources, unsubscribe from events,
        and perform any necessary cleanup.

        Example:
            def cleanup(self):
                self.event_bus.unsubscribe(SceneStartEvent, self._on_scene_start)
                self.sound_cache.clear()
        """
        return

    def reset(self) -> None:
        """Reset system state for a new game session.

        Override this method to clear transient gameplay state (items, flags, etc.)
        while preserving persistent wiring (event bus, references).
        This is called when starting a new game.
        """
        return

    def get_state(self) -> dict[str, Any]:
        """Return serializable state for saving.

        Override this method to return a dictionary of state that should be
        persisted when the game is saved. The dictionary must be JSON-serializable.

        Returns:
            Dictionary containing the system's saveable state.

        Example:
            def get_state(self):
                return {
                    "current_weather": self.current_weather,
                    "intensity": self.intensity,
                }
        """
        return {}

    def restore_state(self, state: dict[str, Any]) -> None:
        """Restore state from save data.

        Override this method to restore the system's state from a previously
        saved dictionary. This is called after setup() when loading a saved game.

        Args:
            state: Previously saved state dictionary from get_state().

        Example:
            def restore_state(self, state):
                self.current_weather = state.get("current_weather", "clear")
                self.intensity = state.get("intensity", 0.0)
        """
        return

    def on_key_press(self, symbol: int, modifiers: int, context: GameContext) -> bool:
        """Handle key press events.

        Override this method to handle keyboard input.

        Args:
            symbol: Arcade key constant for the pressed key.
            modifiers: Bitfield of modifier keys held.
            context: Game context providing access to other systems.

        Returns:
            True if the event was handled and should stop propagating, False otherwise.
        """
        return False

    def on_key_release(self, symbol: int, modifiers: int, context: GameContext) -> bool:
        """Handle key release events.

        Override this method to handle keyboard input.

        Args:
            symbol: Arcade key constant for the released key.
            modifiers: Bitfield of modifier keys held.
            context: Game context providing access to other systems.

        Returns:
            True if the event was handled and should stop propagating, False otherwise.
        """
        return False

    def get_save_state(self) -> dict[str, Any]:
        """Return serializable state for saving to disk.

        Override this method to persist state across game sessions. The returned
        dictionary must be JSON-serializable (strings, numbers, booleans, lists, dicts).

        Returns:
            Dictionary containing the system's saveable state. Default returns empty dict.

        Example:
            def get_save_state(self):
                return {
                    "current_track": self.current_track,
                    "volume": self.volume,
                }
        """
        return {}

    def restore_save_state(self, state: dict[str, Any]) -> None:
        """Restore state from save file.

        Override this method to restore the system's state from a previously
        saved dictionary. This is called after setup() when loading a saved game.

        Args:
            state: Previously saved state dictionary from get_save_state().

        Example:
            def restore_save_state(self, state):
                self.current_track = state.get("current_track", "")
                self.volume = state.get("volume", 1.0)
        """
        return

    def cache_scene_state(self, scene_name: str) -> dict[str, Any]:
        """Return state to cache during scene transitions.

        Override this method to persist state when leaving a scene. The state
        will be restored when returning to the same scene.

        By default, this delegates to get_save_state() since most systems
        don't need scene-specific caching behavior.

        Args:
            scene_name: Name of the scene being left.

        Returns:
            Dictionary containing the system's cacheable state for this scene.

        Example:
            def cache_scene_state(self, scene_name):
                # Cache NPC positions per scene
                return {
                    npc_name: {"x": npc.x, "y": npc.y}
                    for npc_name, npc in self.npcs.items()
                }
        """
        return self.get_save_state()

    def restore_scene_state(self, scene_name: str, state: dict[str, Any]) -> None:
        """Restore cached state when returning to a scene.

        Override this method to restore scene-specific cached state. This is
        called after load_from_tiled() when entering a previously visited scene.

        By default, this delegates to restore_save_state() since most systems
        don't need scene-specific restoration behavior.

        Args:
            scene_name: Name of the scene being entered.
            state: Previously cached state from cache_scene_state().

        Example:
            def restore_scene_state(self, scene_name, state):
                # Restore NPC positions
                for npc_name, npc_state in state.items():
                    if npc := self.npcs.get(npc_name):
                        npc.x = npc_state["x"]
                        npc.y = npc_state["y"]
        """
        self.restore_save_state(state)
