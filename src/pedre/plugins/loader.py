"""Plugin loader for dynamically loading and initializing pluggable plugins.

This module provides the PluginLoader class which handles the discovery,
instantiation, and initialization of plugins based on configuration.
It performs dependency resolution to ensure plugins are initialized in
the correct order.

Example:
    Loading and initializing plugins::

        from pedre.plugins.loader import PluginLoader
        from pedre.conf import settings

        # Configure settings in your settings.py:
        # INSTALLED_PLUGINS = [
        #     "pedre.plugins.audio",
        #     "pedre.plugins.npc",
        #     "myapp.weather",  # Custom plugin
        # ]

        loader = PluginLoader()
        plugins = loader.instantiate_all()

        # Setup all plugins with game context
        loader.setup_all(game_context)

        # In game loop
        loader.update_all(delta_time)
"""

import importlib
import logging
from typing import TYPE_CHECKING

from pedre.conf import settings
from pedre.plugins.registry import PluginRegistry

if TYPE_CHECKING:
    from pedre.plugins.base import BasePlugin
    from pedre.plugins.game_context import GameContext

logger = logging.getLogger(__name__)


class CircularDependencyError(Exception):
    """Raised when plugins have circular dependencies."""


class MissingDependencyError(Exception):
    """Raised when a plugin depends on an unregistered plugin."""


class PluginLoader:
    """Loads and initializes plugins based on configuration.

    The PluginLoader is responsible for:
    1. Importing plugin modules to trigger registration
    2. Resolving dependencies between plugins
    3. Instantiating plugins in dependency order
    4. Calling lifecycle methods (setup, update, cleanup) on all plugins

    This enables a Django-like plugin architecture where users can configure
    which plugins to load via settings.INSTALLED_PLUGINS.

    Example:
        Basic usage::

            loader = PluginLoader()
            plugins = loader.instantiate_all()
            loader.setup_all(context)

            # In game loop
            loader.update_all(delta_time)

            # On scene unload
            loader.cleanup_all()
    """

    def __init__(self) -> None:
        """Initialize the plugin loader."""
        self._instances: dict[str, BasePlugin] = {}
        self._load_order: list[str] = []

    def load_modules(self) -> None:
        """Import all configured plugin modules to trigger registration.

        This imports each module path from settings.INSTALLED_PLUGINS,
        which causes any @PluginRegistry.register decorators to execute
        and register the plugins.

        Raises:
            ImportError: If a module cannot be imported.
        """
        installed_plugins = settings.INSTALLED_PLUGINS
        for module_path in installed_plugins:
            try:
                importlib.import_module(module_path)
                logger.debug("Loaded plugin module: %s", module_path)
            except ImportError:
                logger.exception("Could not load plugin module '%s'", module_path)
                raise

    def instantiate_all(self) -> dict[str, BasePlugin]:
        """Create instances of all registered plugins in dependency order.

        This method:
        1. Imports all configured plugin modules
        2. Resolves dependencies to determine initialization order
        3. Instantiates each plugin class

        Returns:
            Dictionary mapping plugin names to their instances.

        Raises:
            ImportError: If a plugin module cannot be imported.
            CircularDependencyError: If plugins have circular dependencies.
            MissingDependencyError: If a plugin depends on an unregistered plugin.
        """
        self.load_modules()

        all_plugins = PluginRegistry.get_all()
        if not all_plugins:
            logger.warning("No plugins registered")
            return {}

        # Resolve dependencies to get initialization order
        self._load_order = self._resolve_dependencies(all_plugins)

        # Instantiate plugins in order
        for name in self._load_order:
            plugin_class = all_plugins[name]
            self._instances[name] = plugin_class()
            logger.debug("Instantiated plugin: %s", name)

        logger.info("Instantiated %d plugins", len(self._instances))
        return self._instances

    def setup_all(self, context: GameContext) -> None:
        """Call setup() on all plugins in dependency order.

        This should be called after instantiate_all() and after the
        GameContext has been created with all necessary references.

        Args:
            context: Game context providing access to other plugins.
        """
        for name in self._load_order:
            plugin = self._instances.get(name)
            if plugin:
                plugin.setup(context)
                logger.debug("Setup plugin: %s", name)

    def update_all(self, delta_time: float) -> None:
        """Call update() on all plugins.

        This should be called each frame from the game loop.

        Args:
            delta_time: Time elapsed since last frame in seconds.
        """
        for plugin in self._instances.values():
            plugin.update(delta_time)

    def draw_all(self) -> None:
        """Call on_draw() on all plugins (world coordinates).

        This should be called during the draw phase of each frame,
        while world camera is active.
        """
        for plugin in self._instances.values():
            plugin.on_draw()

    def draw_ui_all(self) -> None:
        """Call on_draw_ui() on all plugins (screen coordinates).

        This should be called during the draw phase of each frame,
        while screen camera is active.
        """
        for plugin in self._instances.values():
            plugin.on_draw_ui()

    def cleanup_all(self) -> None:
        """Call cleanup() on all plugins in reverse dependency order.

        This should be called when unloading a scene or exiting the game.
        Plugins are cleaned up in reverse order so that plugins can safely
        access their dependencies during cleanup.
        """
        for name in reversed(self._load_order):
            plugin = self._instances.get(name)
            if plugin:
                plugin.cleanup()
                logger.debug("Cleaned up plugin: %s", name)

    def reset_all(self) -> None:
        """Call reset() on all plugins to prepare for a new game session.

        This clears transient state (items, NPCs, flags) but keeps plugin wiring intact.
        """
        # Reset all plugins (including cache which will clear itself)
        for name in self._load_order:
            plugin = self._instances.get(name)
            if plugin:
                plugin.reset()
                logger.debug("Reset plugin: %s", name)

    def get_plugin(self, name: str) -> BasePlugin | None:
        """Get a plugin instance by name.

        Args:
            name: The plugin's unique identifier.

        Returns:
            The plugin instance if found, None otherwise.
        """
        return self._instances.get(name)

    def get_all_instances(self) -> dict[str, BasePlugin]:
        """Get all plugin instances.

        Returns:
            Dictionary mapping plugin names to their instances.
        """
        return self._instances.copy()

    def _resolve_dependencies(self, plugins: dict[str, type[BasePlugin]]) -> list[str]:
        """Resolve plugin dependencies using topological sort.

        Uses Kahn's algorithm to produce a valid initialization order
        where each plugin is initialized after all its dependencies.

        Args:
            plugins: Dictionary mapping plugin names to their classes.

        Returns:
            List of plugin names in dependency order.

        Raises:
            CircularDependencyError: If plugins have circular dependencies.
            MissingDependencyError: If a plugin depends on an unregistered plugin.
        """
        # Build adjacency list and in-degree count
        in_degree: dict[str, int] = dict.fromkeys(plugins, 0)
        dependents: dict[str, list[str]] = {name: [] for name in plugins}

        for name, plugin_class in plugins.items():
            for dep in plugin_class.dependencies:
                if dep not in plugins:
                    msg = f"Plugin '{name}' depends on '{dep}' which is not registered"
                    raise MissingDependencyError(msg)
                dependents[dep].append(name)
                in_degree[name] += 1

        # Start with plugins that have no dependencies
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result: list[str] = []

        while queue:
            # Sort for deterministic order when multiple plugins have same in-degree
            queue.sort()
            current = queue.pop(0)
            result.append(current)

            for dependent in dependents[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(result) != len(plugins):
            # Find the cycle for a better error message
            remaining = set(plugins.keys()) - set(result)
            msg = f"Circular dependency detected among plugins: {remaining}"
            raise CircularDependencyError(msg)

        return result

    def on_key_press_all(self, symbol: int, modifiers: int) -> bool:
        """Propagate key press events to all plugins.

        Iterates through plugins in dependency order (or specific input order if needed).
        If a plugin returns True, propagation stops.

        Args:
            symbol: Arcade key constant.
            modifiers: Modifier key bitfield.

        Returns:
            True if any plugin handled the event.
        """
        for name in reversed(self._load_order):
            plugin = self._instances.get(name)
            if plugin and plugin.on_key_press(symbol, modifiers):
                logger.debug("Key press handled by plugin: %s", name)
                return True
        return False

    def on_key_release_all(self, symbol: int, modifiers: int) -> bool:
        """Propagate key release events to all plugins.

        Args:
            symbol: Arcade key constant.
            modifiers: Modifier key bitfield.

        Returns:
            True if any plugin handled the event.
        """
        for name in reversed(self._load_order):
            plugin = self._instances.get(name)
            if plugin and plugin.on_key_release(symbol, modifiers):
                return True
        return False
