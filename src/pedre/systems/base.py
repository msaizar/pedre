"""Base class for pluggable systems.

This module provides the abstract base class that all pluggable systems must inherit from.
Systems are the building blocks of the game engine, each handling a specific aspect
of the game (audio, NPCs, inventory, etc.).

Example:
    Creating a custom system::

        from pedre.systems.base import BaseSystem
        from pedre.systems.registry import SystemRegistry

        @SystemRegistry.register
        class WeatherManager(BaseSystem):
            name = "weather"
            dependencies = ["particle", "audio"]

            def setup(self, context, settings):
                self.current_weather = "clear"

            def update(self, delta_time, context):
                if self.current_weather == "rain":
                    context.get_system("particle").emit("rain")
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from pedre.config import GameSettings
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

            @SystemRegistry.register
            class WeatherManager(BaseSystem):
                name = "weather"
                dependencies = ["particle"]

                def setup(self, context, settings):
                    self.intensity = 0.0

                def set_weather(self, weather_type, intensity):
                    self.current_weather = weather_type
                    self.intensity = intensity
    """

    # System identifier (must be unique across all systems)
    name: ClassVar[str]

    # Other systems this one depends on (by name)
    # Systems are initialized in dependency order
    dependencies: ClassVar[list[str]] = []

    @abstractmethod
    def setup(self, context: GameContext, settings: GameSettings) -> None:
        """Initialize the system when a scene loads.

        This method is called after all systems have been instantiated but before
        the game loop starts. Use it to initialize state, subscribe to events,
        and configure the system based on settings.

        Args:
            context: Game context providing access to other systems via get_system().
            settings: Game configuration settings from GameSettings.

        Example:
            def setup(self, context, settings):
                self.event_bus = context.event_bus
                self.volume = settings.music_volume
                self.event_bus.subscribe(SceneStartEvent, self._on_scene_start)
        """

    def update(self, delta_time: float, context: GameContext) -> None:  # noqa: B027
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

    def on_draw(self, context: GameContext) -> None:  # noqa: B027
        """Called during the draw phase of each frame (world coordinates).

        Override this method to render visual elements managed by this system
        in world coordinates (affected by camera).

        Args:
            context: Game context providing access to other systems.
        """

    def on_draw_ui(self, context: GameContext) -> None:  # noqa: B027
        """Called during the draw phase of each frame (screen coordinates).

        Override this method to render UI elements or overlays in screen coordinates
        (not affected by camera).

        Args:
            context: Game context providing access to other systems.
        """

    def cleanup(self) -> None:  # noqa: B027
        """Called when the scene unloads or the game exits.

        Override this method to release resources, unsubscribe from events,
        and perform any necessary cleanup.

        Example:
            def cleanup(self):
                self.event_bus.unsubscribe(SceneStartEvent, self._on_scene_start)
                self.sound_cache.clear()
        """

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

    def restore_state(self, state: dict[str, Any]) -> None:  # noqa: B027
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
