"""Registry for pluggable script actions.

This module provides the ActionRegistry class which tracks all available action types
for the scripting system. Actions register themselves using the @ActionRegistry.register
decorator, enabling users to create custom actions that work in JSON scripts.

Example:
    Registering a custom action::

        from pedre.systems.actions import Action
        from pedre.systems.action_registry import ActionRegistry

        @ActionRegistry.register("set_weather")
        class SetWeatherAction(Action):
            def __init__(self, weather: str, intensity: float = 1.0):
                self.weather = weather
                self.intensity = intensity
                self._executed = False

            @classmethod
            def from_dict(cls, data: dict) -> "SetWeatherAction":
                return cls(
                    weather=data["weather"],
                    intensity=data.get("intensity", 1.0)
                )

            def execute(self, context):
                if not self._executed:
                    context.get_system("weather").set_weather(self.weather, self.intensity)
                    self._executed = True
                return True

            def reset(self):
                self._executed = False

    Using the action in a JSON script::

        {
            "rain_scene": {
                "trigger": {"event": "scene_start", "scene": "forest"},
                "actions": [
                    {"type": "set_weather", "weather": "rain", "intensity": 0.7}
                ]
            }
        }
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from collections.abc import Callable

    from pedre.actions import Action

logger = logging.getLogger(__name__)


class ActionRegistry:
    """Central registry for all available script actions.

    The ActionRegistry maintains a mapping of action type names to their classes
    and parser functions. Actions register themselves using the @ActionRegistry.register
    decorator, which allows the ScriptManager to parse JSON action definitions
    into Action instances without hardcoding every action type.

    This enables users to create custom actions that integrate seamlessly with
    the scripting system.

    Class Attributes:
        _actions: Dictionary mapping action type names to their classes.
        _parsers: Dictionary mapping action type names to parser functions.

    Example:
        Registering and using an action::

            @ActionRegistry.register("flash_screen")
            class FlashScreenAction(Action):
                @classmethod
                def from_dict(cls, data):
                    return cls(color=data.get("color", "white"))
                ...

            # ScriptManager uses the registry to parse:
            action = ActionRegistry.parse({"type": "flash_screen", "color": "red"})
    """

    _actions: ClassVar[dict[str, type[Action]]] = {}
    _parsers: ClassVar[dict[str, Callable[[dict[str, Any]], Action]]] = {}

    @classmethod
    def register(cls, action_type: str) -> Callable[[type[Action]], type[Action]]:
        """Decorator to register an action class with its JSON type name.

        The action class should have a `from_dict` classmethod that creates
        an instance from a dictionary of parameters. If `from_dict` is present,
        it will be automatically registered as the parser for this action type.

        Args:
            action_type: The "type" value used in JSON scripts to identify
                this action.

        Returns:
            Decorator function that registers the action class.

        Example:
            Using the decorator::

                @ActionRegistry.register("play_sfx")
                class PlaySFXAction(Action):
                    @classmethod
                    def from_dict(cls, data: dict) -> "PlaySFXAction":
                        return cls(sfx_file=data["file"])

                    def execute(self, context):
                        context.audio_manager.play_sfx(self.sfx_file)
                        return True

                    def reset(self):
                        pass

            The action can then be used in scripts::

                {"type": "play_sfx", "file": "explosion.wav"}
        """

        def decorator(action_class: type[Action]) -> type[Action]:
            cls._actions[action_type] = action_class

            # Auto-register parser if action has from_dict classmethod
            if hasattr(action_class, "from_dict"):
                # Type-safe access to the classmethod
                from_dict_method: Callable[[dict[str, Any]], Action] = action_class.from_dict  # type: ignore[attr-defined]
                cls._parsers[action_type] = from_dict_method
                logger.debug("Registered action with parser: %s", action_type)
            else:
                logger.debug("Registered action without parser: %s", action_type)

            return action_class

        return decorator

    @classmethod
    def register_parser(cls, action_type: str, parser: Callable[[dict[str, Any]], Action]) -> None:
        """Register a custom parser for an action type.

        Use this for complex parsing logic that can't be handled by a simple
        from_dict classmethod, such as when parsing requires access to external
        data or involves complex validation.

        Args:
            action_type: The "type" value used in JSON scripts.
            parser: Function that takes a dictionary and returns an Action instance.

        Example:
            Registering a custom parser::

                def parse_dialog_action(data: dict) -> DialogAction:
                    # Complex parsing with text resolution
                    text = resolve_text_reference(data.get("text_from"))
                    return DialogAction(speaker=data["speaker"], text=text)

                ActionRegistry.register_parser("dialog", parse_dialog_action)
        """
        cls._parsers[action_type] = parser
        logger.debug("Registered custom parser for action: %s", action_type)

    @classmethod
    def parse(cls, action_dict: dict[str, Any]) -> Action | None:
        """Parse an action dictionary into an Action instance.

        This method looks up the appropriate parser based on the "type" field
        in the dictionary and uses it to create an Action instance.

        Args:
            action_dict: Dictionary with a "type" key identifying the action
                and additional keys for action-specific parameters.

        Returns:
            Instantiated Action if the type is registered and parsing succeeds,
            None otherwise.

        Example:
            Parsing an action::

                action = ActionRegistry.parse({
                    "type": "move_npc",
                    "npcs": ["martin"],
                    "waypoint": "town_square"
                })
                if action:
                    action.execute(context)
        """
        action_type = action_dict.get("type")
        if not action_type:
            logger.warning("Action dict missing 'type' key: %s", action_dict)
            return None

        parser = cls._parsers.get(action_type)
        if parser:
            try:
                return parser(action_dict)
            except Exception:
                logger.exception("Failed to parse action '%s': %s", action_type, action_dict)
                return None

        # Return None if not found - allows fallback to legacy parsing
        return None

    @classmethod
    def get_action_class(cls, action_type: str) -> type[Action] | None:
        """Get the action class for a type name.

        Args:
            action_type: The "type" value used in JSON scripts.

        Returns:
            The Action class if registered, None otherwise.
        """
        return cls._actions.get(action_type)

    @classmethod
    def get_all_types(cls) -> list[str]:
        """Get all registered action type names.

        Returns:
            List of action type strings that have parsers registered.
        """
        return list(cls._parsers.keys())

    @classmethod
    def is_registered(cls, action_type: str) -> bool:
        """Check if an action type is registered.

        Args:
            action_type: The action type name to check.

        Returns:
            True if the action type has a parser registered, False otherwise.
        """
        return action_type in cls._parsers

    @classmethod
    def clear(cls) -> None:
        """Clear the registry.

        Removes all registered actions and parsers. This is primarily useful
        for testing to ensure a clean state between tests.

        Warning:
            This should not be called in production code as it will break
            any code that depends on registered actions.
        """
        cls._actions.clear()
        cls._parsers.clear()
        logger.debug("Action registry cleared")
