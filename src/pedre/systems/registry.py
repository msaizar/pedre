"""Registry for pluggable systems.

This module provides the SystemRegistry class which tracks all available system classes.
Systems register themselves using the @SystemRegistry.register decorator, enabling
dynamic discovery and instantiation based on configuration.

Example:
    Registering a system::

        from pedre.systems.base import BaseSystem
        from pedre.systems.registry import SystemRegistry

        @SystemRegistry.register
        class AudioManager(BaseSystem):
            name = "audio"
            dependencies = []

            def setup(self, context, settings):
                pass

    Retrieving a system class::

        audio_class = SystemRegistry.get("audio")
        if audio_class:
            instance = audio_class()
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pedre.systems.base import BaseSystem

logger = logging.getLogger(__name__)


class SystemRegistry:
    """Central registry for all available systems.

    The SystemRegistry maintains a mapping of system names to their classes.
    Systems register themselves using the @SystemRegistry.register decorator,
    which allows the SystemLoader to discover and instantiate them based on
    the settings.installed_systems configuration.

    This pattern is similar to Django's app registry, enabling users to create
    custom systems that integrate seamlessly with the engine.

    Class Attributes:
        _systems: Dictionary mapping system names to their classes.

    Example:
        Registering and retrieving systems::

            @SystemRegistry.register
            class MySystem(BaseSystem):
                name = "my_system"
                def setup(self, context, settings): pass

            # Later, retrieve the class
            cls = SystemRegistry.get("my_system")
            instance = cls()
    """

    _systems: ClassVar[dict[str, type[BaseSystem]]] = {}

    @classmethod
    def register(cls, system_class: type[BaseSystem]) -> type[BaseSystem]:
        """Register a system class.

        This method is typically used as a decorator on system classes. It
        validates that the system has a name attribute and adds it to the
        registry.

        Args:
            system_class: The system class to register. Must have a 'name'
                class attribute defined.

        Returns:
            The same class, allowing use as a decorator.

        Raises:
            ValueError: If the system class doesn't define a 'name' attribute.

        Example:
            Using as a decorator::

                @SystemRegistry.register
                class MySystem(BaseSystem):
                    name = "my_system"
                    def setup(self, context, settings): pass

            Manual registration::

                class MySystem(BaseSystem):
                    name = "my_system"
                    def setup(self, context, settings): pass

                SystemRegistry.register(MySystem)
        """
        if not hasattr(system_class, "name") or not system_class.name:
            msg = f"System {system_class.__name__} must define a 'name' class attribute"
            raise ValueError(msg)

        if system_class.name in cls._systems:
            logger.warning(
                "System '%s' is being re-registered (was %s, now %s)",
                system_class.name,
                cls._systems[system_class.name].__name__,
                system_class.__name__,
            )

        cls._systems[system_class.name] = system_class
        logger.debug("Registered system: %s", system_class.name)
        return system_class

    @classmethod
    def get(cls, name: str) -> type[BaseSystem] | None:
        """Get a registered system class by name.

        Args:
            name: The system's unique identifier (its 'name' class attribute).

        Returns:
            The system class if found, None otherwise.

        Example:
            audio_cls = SystemRegistry.get("audio")
            if audio_cls:
                audio = audio_cls()
        """
        return cls._systems.get(name)

    @classmethod
    def get_all(cls) -> dict[str, type[BaseSystem]]:
        """Get all registered systems.

        Returns:
            A copy of the systems dictionary mapping names to classes.

        Example:
            for name, system_cls in SystemRegistry.get_all().items():
                print(f"System '{name}': {system_cls.__name__}")
        """
        return cls._systems.copy()

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a system is registered.

        Args:
            name: The system's unique identifier.

        Returns:
            True if the system is registered, False otherwise.
        """
        return name in cls._systems

    @classmethod
    def clear(cls) -> None:
        """Clear the registry.

        Removes all registered systems. This is primarily useful for testing
        to ensure a clean state between tests.

        Warning:
            This should not be called in production code as it will break
            any code that depends on registered systems.
        """
        cls._systems.clear()
        logger.debug("System registry cleared")
