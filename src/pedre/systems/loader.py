"""System loader for dynamically loading and initializing pluggable systems.

This module provides the SystemLoader class which handles the discovery,
instantiation, and initialization of systems based on configuration.
It performs dependency resolution to ensure systems are initialized in
the correct order.

Example:
    Loading and initializing systems::

        from pedre.systems.loader import SystemLoader
        from pedre.config import GameSettings

        settings = GameSettings(
            installed_systems=[
                "pedre.systems.audio",
                "pedre.systems.npc",
                "myapp.weather",  # Custom system
            ]
        )

        loader = SystemLoader(settings)
        systems = loader.instantiate_all()

        # Setup all systems with game context
        loader.setup_all(game_context)

        # In game loop
        loader.update_all(delta_time, game_context)
"""

from __future__ import annotations

import importlib
import logging
from typing import TYPE_CHECKING

from pedre.caches.loader import CacheLoader
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    from pedre.config import GameSettings
    from pedre.systems.base import BaseSystem
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


class CircularDependencyError(Exception):
    """Raised when systems have circular dependencies."""


class MissingDependencyError(Exception):
    """Raised when a system depends on an unregistered system."""


class SystemLoader:
    """Loads and initializes systems based on configuration.

    The SystemLoader is responsible for:
    1. Importing system modules to trigger registration
    2. Resolving dependencies between systems
    3. Instantiating systems in dependency order
    4. Calling lifecycle methods (setup, update, cleanup) on all systems

    This enables a Django-like plugin architecture where users can configure
    which systems to load via GameSettings.installed_systems.

    Attributes:
        settings: Game configuration containing installed_systems list.

    Example:
        Basic usage::

            loader = SystemLoader(settings)
            systems = loader.instantiate_all()
            loader.setup_all(context)

            # In game loop
            loader.update_all(delta_time, context)

            # On scene unload
            loader.cleanup_all()
    """

    def __init__(self, settings: GameSettings) -> None:
        """Initialize the system loader.

        Args:
            settings: Game configuration containing the installed_systems list.
        """
        self.settings = settings
        self._instances: dict[str, BaseSystem] = {}
        self._load_order: list[str] = []
        self._cache_loader: CacheLoader | None = None

    def load_modules(self) -> None:
        """Import all configured system modules to trigger registration.

        This imports each module path from settings.installed_systems,
        which causes any @SystemRegistry.register decorators to execute
        and register the systems.

        Raises:
            ImportError: If a module cannot be imported.
        """
        installed_systems = self.settings.installed_systems or []
        for module_path in installed_systems:
            try:
                importlib.import_module(module_path)
                logger.debug("Loaded system module: %s", module_path)
            except ImportError:
                logger.exception("Could not load system module '%s'", module_path)
                raise

    def instantiate_all(self) -> dict[str, BaseSystem]:
        """Create instances of all registered systems in dependency order.

        This method:
        1. Imports all configured system modules
        2. Resolves dependencies to determine initialization order
        3. Instantiates each system class

        Returns:
            Dictionary mapping system names to their instances.

        Raises:
            ImportError: If a system module cannot be imported.
            CircularDependencyError: If systems have circular dependencies.
            MissingDependencyError: If a system depends on an unregistered system.
        """
        self.load_modules()

        all_systems = SystemRegistry.get_all()
        if not all_systems:
            logger.warning("No systems registered")
            return {}

        # Resolve dependencies to get initialization order
        self._load_order = self._resolve_dependencies(all_systems)

        # Instantiate systems in order
        for name in self._load_order:
            system_class = all_systems[name]
            self._instances[name] = system_class()
            logger.debug("Instantiated system: %s", name)

        logger.info("Instantiated %d systems", len(self._instances))
        return self._instances

    def setup_all(self, context: GameContext) -> None:
        """Call setup() on all systems in dependency order.

        This should be called after instantiate_all() and after the
        GameContext has been created with all necessary references.

        Args:
            context: Game context providing access to other systems.
        """
        # Initialize and set up the cache loader before systems
        self._cache_loader = CacheLoader(self.settings)
        self._cache_loader.instantiate_all()

        # Initialize SceneManager with the cache loader
        # Import here to avoid circular dependency
        from pedre.systems.scene import SceneManager  # noqa: PLC0415

        SceneManager.init_cache_loader(self._cache_loader)

        for name in self._load_order:
            system = self._instances.get(name)
            if system:
                system.setup(context, self.settings)
                logger.debug("Setup system: %s", name)

    def update_all(self, delta_time: float, context: GameContext) -> None:
        """Call update() on all systems.

        This should be called each frame from the game loop.

        Args:
            delta_time: Time elapsed since last frame in seconds.
            context: Game context providing access to other systems.
        """
        for system in self._instances.values():
            system.update(delta_time, context)

    def draw_all(self, context: GameContext) -> None:
        """Call on_draw() on all systems (world coordinates).

        This should be called during the draw phase of each frame,
        while world camera is active.

        Args:
            context: Game context providing access to other systems.
        """
        for system in self._instances.values():
            system.on_draw(context)

    def draw_ui_all(self, context: GameContext) -> None:
        """Call on_draw_ui() on all systems (screen coordinates).

        This should be called during the draw phase of each frame,
        while screen camera is active.

        Args:
            context: Game context providing access to other systems.
        """
        for system in self._instances.values():
            system.on_draw_ui(context)

    def cleanup_all(self) -> None:
        """Call cleanup() on all systems in reverse dependency order.

        This should be called when unloading a scene or exiting the game.
        Systems are cleaned up in reverse order so that systems can safely
        access their dependencies during cleanup.
        """
        for name in reversed(self._load_order):
            system = self._instances.get(name)
            if system:
                system.cleanup()
                logger.debug("Cleaned up system: %s", name)

    def get_system(self, name: str) -> BaseSystem | None:
        """Get a system instance by name.

        Args:
            name: The system's unique identifier.

        Returns:
            The system instance if found, None otherwise.
        """
        return self._instances.get(name)

    def get_all_instances(self) -> dict[str, BaseSystem]:
        """Get all system instances.

        Returns:
            Dictionary mapping system names to their instances.
        """
        return self._instances.copy()

    def _resolve_dependencies(self, systems: dict[str, type[BaseSystem]]) -> list[str]:
        """Resolve system dependencies using topological sort.

        Uses Kahn's algorithm to produce a valid initialization order
        where each system is initialized after all its dependencies.

        Args:
            systems: Dictionary mapping system names to their classes.

        Returns:
            List of system names in dependency order.

        Raises:
            CircularDependencyError: If systems have circular dependencies.
            MissingDependencyError: If a system depends on an unregistered system.
        """
        # Build adjacency list and in-degree count
        in_degree: dict[str, int] = dict.fromkeys(systems, 0)
        dependents: dict[str, list[str]] = {name: [] for name in systems}

        for name, system_class in systems.items():
            for dep in system_class.dependencies:
                if dep not in systems:
                    msg = f"System '{name}' depends on '{dep}' which is not registered"
                    raise MissingDependencyError(msg)
                dependents[dep].append(name)
                in_degree[name] += 1

        # Start with systems that have no dependencies
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result: list[str] = []

        while queue:
            # Sort for deterministic order when multiple systems have same in-degree
            queue.sort()
            current = queue.pop(0)
            result.append(current)

            for dependent in dependents[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(result) != len(systems):
            # Find the cycle for a better error message
            remaining = set(systems.keys()) - set(result)
            msg = f"Circular dependency detected among systems: {remaining}"
            raise CircularDependencyError(msg)

        return result

    def on_key_press_all(self, symbol: int, modifiers: int, context: GameContext) -> bool:
        """Propagate key press events to all systems.

        Iterates through systems in dependency order (or specific input order if needed).
        If a system returns True, propagation stops.

        Args:
            symbol: Arcade key constant.
            modifiers: Modifier key bitfield.
            context: Game context.

        Returns:
            True if any system handled the event.
        """
        for name in reversed(self._load_order):
            system = self._instances.get(name)
            if system and system.on_key_press(symbol, modifiers, context):
                logger.debug("Key press handled by system: %s", name)
                return True
        return False

    def on_key_release_all(self, symbol: int, modifiers: int, context: GameContext) -> bool:
        """Propagate key release events to all systems.

        Args:
            symbol: Arcade key constant.
            modifiers: Modifier key bitfield.
            context: Game context.

        Returns:
            True if any system handled the event.
        """
        for name in reversed(self._load_order):
            system = self._instances.get(name)
            if system and system.on_key_release(symbol, modifiers, context):
                return True
        return False
