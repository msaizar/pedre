"""Command loader for dynamically loading and registering CLI commands.

This module provides the CommandLoader class which handles the discovery
and registration of commands using auto-discovery and entry points.

Auto-discovery:
    Commands are automatically discovered from:
    1. Built-in framework commands in pedre.commands/
    2. User project commands in <project_root>/commands/
    3. External package commands via entry points

Entry Points:
    External packages can register commands using the "pedre.commands" entry point
    group in their pyproject.toml:

        [project.entry-points."pedre.commands"]
        build = "my_package.commands:BuildCommand"
        deploy = "my_package.commands:DeployCommand"

Example:
    Basic usage (auto-discovery)::

        from pedre.commands.loader import CommandLoader

        loader = CommandLoader()
        loader.load_modules()  # Auto-discovers all commands

    Project structure::

        my_game/
        ├── commands/           # User's custom commands (auto-discovered!)
        │   ├── __init__.py
        │   ├── build.py
        │   └── deploy.py
        ├── assets/
        ├── main.py
        └── settings.py

    External package with entry points::

        # In external_package/pyproject.toml
        [project.entry-points."pedre.commands"]
        balance = "pedre_combat.commands:BalanceCommand"
        spawn = "pedre_combat.commands:SpawnCommand"
"""

import importlib
import logging
import pkgutil
import sys
from importlib.metadata import entry_points
from pathlib import Path

import pedre.commands

logger = logging.getLogger(__name__)


class CommandLoader:
    """Loads command modules to trigger registration.

    The CommandLoader is responsible for importing command modules, which
    causes their @CommandRegistry.register decorators to execute and
    register the commands with the global CommandRegistry.

    Commands are discovered from three sources:
    1. Framework commands: pedre.commands package (auto-discovered)
    2. Project commands: <project_root>/commands directory (auto-discovered if exists)
    3. External packages: via "pedre.commands" entry points

    Example:
        Basic usage::

            loader = CommandLoader()
            loader.load_modules()

            # Now CommandRegistry.get_all_commands() returns all registered commands
            commands = CommandRegistry.get_all_commands()
    """

    def autodiscover_framework_commands(self) -> None:
        """Auto-discover and import all framework command modules in pedre.commands.

        This walks through all Python modules in the pedre.commands package
        and imports them, which triggers their @CommandRegistry.register
        decorators to execute.

        Modules starting with '_' are skipped (e.g., __init__.py, _private.py).
        """
        logger.debug("Auto-discovering framework commands in pedre.commands...")
        for _, module_name, _ in pkgutil.iter_modules(pedre.commands.__path__):
            # Skip private modules and special files
            if module_name.startswith("_"):
                continue

            # Skip base, registry, and loader modules (not actual commands)
            if module_name in {"base", "registry", "loader"}:
                continue

            module_path = f"pedre.commands.{module_name}"
            try:
                importlib.import_module(module_path)
                logger.debug("Auto-discovered framework command: %s", module_path)
            except ImportError:
                logger.exception("Failed to auto-discover framework command '%s'", module_path)
                raise

    def autodiscover_project_commands(self) -> None:
        """Auto-discover and import user project commands from <cwd>/commands/.

        This looks for a 'commands' directory in the current working directory
        and imports all Python modules from it. This allows users to create
        custom commands by simply adding files to their project's commands/ folder.

        If the commands directory doesn't exist, this silently returns.
        """
        # Look for commands directory in current working directory
        cwd = Path.cwd()
        commands_dir = cwd / "commands"

        if not commands_dir.exists() or not commands_dir.is_dir():
            logger.debug("No project commands directory found at %s", commands_dir)
            return

        logger.debug("Auto-discovering project commands in %s...", commands_dir)

        # Add the project directory to sys.path if not already there
        cwd_str = str(cwd)
        if cwd_str not in sys.path:
            sys.path.insert(0, cwd_str)

        # Find all Python modules in the commands directory
        try:
            for _, module_name, _ in pkgutil.iter_modules([str(commands_dir)]):
                # Skip private modules and special files
                if module_name.startswith("_"):
                    continue

                module_path = f"commands.{module_name}"
                try:
                    importlib.import_module(module_path)
                    logger.debug("Auto-discovered project command: %s", module_path)
                except ImportError:
                    logger.exception("Failed to auto-discover project command '%s'", module_path)
                    # Don't raise - allow partial discovery
                    continue
        except Exception:
            logger.exception("Error while discovering project commands")
            # Don't raise - project commands are optional

    def load_entry_point_commands(self) -> None:
        """Load commands from external packages via entry points.

        This discovers and loads commands from external packages that have
        registered commands using the "pedre.commands" entry point group.

        External packages can register commands in their pyproject.toml:

            [project.entry-points."pedre.commands"]
            build = "my_package.commands:BuildCommand"

        The entry point name is not used - the command's `name` attribute
        determines the CLI command name.
        """
        # Python 3.10+ has importlib.metadata as stable

        logger.debug("Loading commands from entry points...")

        try:
            # Get entry points - API differs between Python versions
            eps = entry_points()

            # Python 3.10+ returns EntryPoints object, 3.9 returns dict
            if hasattr(eps, "select"):
                # Python 3.10+ API
                command_eps = eps.select(group="pedre.commands")
            else:
                # Python 3.9 API
                command_eps = eps.get("pedre.commands", [])

            for ep in command_eps:
                try:
                    # Load the command class
                    _command_class = ep.load()
                    logger.debug("Loaded entry point command: %s from %s", ep.name, ep.value)

                    # The command class should auto-register itself via @CommandRegistry.register
                    # If not already registered, we could register it here, but it's better
                    # to require the decorator for consistency

                except Exception:
                    logger.exception("Failed to load entry point command '%s'", ep.name)
                    # Don't raise - allow partial discovery
                    continue

        except Exception:
            logger.exception("Error while loading entry point commands")
            # Don't raise - entry points are optional

    def load_modules(self) -> None:
        """Import command modules to trigger registration.

        This method does three things in order:
        1. Auto-discovers framework commands in pedre.commands/ package
        2. Auto-discovers project commands in <cwd>/commands/ directory (if exists)
        3. Loads commands from external packages via entry points

        The auto-discovery and entry points ensure all commands are available
        without any configuration needed.

        Raises:
            ImportError: If a framework command module cannot be imported.
        """
        # First, auto-discover framework commands
        self.autodiscover_framework_commands()

        # Second, auto-discover project commands (optional)
        self.autodiscover_project_commands()

        # Finally, load commands from external packages via entry points
        self.load_entry_point_commands()
