"""Registry for plugins.

This module provides the PluginRegistry class which tracks all available plugin classes.
Plugins register themselves using the @PluginRegistry.register decorator, enabling
dynamic discovery and instantiation based on configuration.

Example:
    Registering a plugin::

        from pedre.plugins.base import BasePlugin
        from pedre.plugins.registry import PluginRegistry

        @PluginRegistry.register
        class AudioPlugin(BasePlugin):
            name = "audio"
            dependencies = []

            def setup(self, context, settings):
                pass

    Retrieving a plugin class::

        audio_class = PluginRegistry.get("audio")
        if audio_class:
            instance = audio_class()
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from pedre.plugins.base import BasePlugin

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Central registry for all available plugins.

    The PluginRegistry maintains a mapping of plugin names to their classes.
    Plugins register themselves using the @PluginRegistry.register decorator,
    which allows the PluginLoader to discover and instantiate them based on
    the settings.installed_plugins configuration.

    This pattern is similar to Django's app registry, enabling users to create
    custom plugins that integrate seamlessly with the engine.

    Class Attributes:
        _plugins: Dictionary mapping plugin names to their classes.

    Example:
        Registering and retrieving plugins::

            @PluginRegistry.register
            class MyPlugin(BasePlugin):
                name = "my_plugin"
                def setup(self, context, settings): pass

            # Later, retrieve the class
            cls = PluginRegistry.get("my_plugin")
            instance = cls()
    """

    _plugins: ClassVar[dict[str, type[BasePlugin]]] = {}

    @classmethod
    def register(cls, plugin_class: type[BasePlugin]) -> type[BasePlugin]:
        """Register a plugin class.

        This method is typically used as a decorator on plugin classes. It
        validates that the plugin has a name attribute and adds it to the
        registry.

        Args:
            plugin_class: The plugin class to register. Must have a 'name'
                class attribute defined.

        Returns:
            The same class, allowing use as a decorator.

        Raises:
            ValueError: If the plugin class doesn't define a 'name' attribute.

        Example:
            Using as a decorator::

                @PluginRegistry.register
                class MyPlugin(BasePlugin):
                    name = "my_plugin"
                    def setup(self, context, settings): pass

            Manual registration::

                class MyPlugin(BasePlugin):
                    name = "my_plugin"
                    def setup(self, context, settings): pass

                PluginRegistry.register(MyPlugin)
        """
        if not hasattr(plugin_class, "name") or not plugin_class.name:
            msg = f"Plugin {plugin_class.__name__} must define a 'name' class attribute"
            raise ValueError(msg)

        if plugin_class.name in cls._plugins:
            logger.warning(
                "Plugin '%s' is being re-registered (was %s, now %s)",
                plugin_class.name,
                cls._plugins[plugin_class.name].__name__,
                plugin_class.__name__,
            )

        cls._plugins[plugin_class.name] = plugin_class
        logger.debug("Registered plugin: %s", plugin_class.name)
        return plugin_class

    @classmethod
    def get(cls, name: str) -> type[BasePlugin] | None:
        """Get a registered plugin class by name.

        Args:
            name: The plugin's unique identifier (its 'name' class attribute).

        Returns:
            The plugin class if found, None otherwise.

        Example:
            audio_cls = PluginRegistry.get("audio")
            if audio_cls:
                audio = audio_cls()
        """
        return cls._plugins.get(name)

    @classmethod
    def get_all(cls) -> dict[str, type[BasePlugin]]:
        """Get all registered plugins.

        Returns:
            A copy of the plugins dictionary mapping names to classes.

        Example:
            for name, plugin_cls in PluginRegistry.get_all().items():
                print(f"Plugin '{name}': {plugin_cls.__name__}")
        """
        return cls._plugins.copy()

    @classmethod
    def is_registered(cls, name: str) -> bool:
        """Check if a plugin is registered.

        Args:
            name: The plugin's unique identifier.

        Returns:
            True if the plugin is registered, False otherwise.
        """
        return name in cls._plugins

    @classmethod
    def clear(cls) -> None:
        """Clear the registry.

        Removes all registered plugins. This is primarily useful for testing
        to ensure a clean state between tests.

        Warning:
            This should not be called in production code as it will break
            any code that depends on registered plugins.
        """
        cls._plugins.clear()
        logger.debug("Plugin registry cleared")
