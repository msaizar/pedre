"""Registry for CLI commands.

This module provides the CommandRegistry class which tracks all available CLI commands.
Commands register themselves using the @CommandRegistry.register decorator, enabling
a Django-style plugin architecture where commands are auto-discovered.

Example:
    Registering a custom command::

        from pedre.commands.base import Command
        from pedre.commands.registry import CommandRegistry

        @CommandRegistry.register()
        class BuildCommand(Command):
            name = "build"
            help = "Build the project"
            description = "Compile and package the game project"

            def add_arguments(self, parser):
                parser.add_argument("--output", help="Output directory")

            def execute(self, args):
                print(f"Building to {args.output}")

    Using commands in the CLI::

        # In cli.py
        from pedre.commands.loader import CommandLoader
        from pedre.commands.registry import CommandRegistry

        loader = CommandLoader()
        loader.load_modules()

        # Get all registered commands
        commands = CommandRegistry.get_all_commands()
"""

import logging
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Callable

    from pedre.commands.base import Command

logger = logging.getLogger(__name__)


class CommandRegistry:
    """Central registry for all CLI commands.

    The CommandRegistry maintains a mapping of command names to their Command classes.
    Commands register themselves using the @CommandRegistry.register decorator,
    which allows the CLI to discover and execute commands without hardcoding them.

    This enables users to create custom commands that integrate seamlessly with
    the Pedre CLI.

    Class Attributes:
        _commands: Dictionary mapping command names to their Command classes.

    Example:
        Registering and using a command::

            @CommandRegistry.register()
            class TestCommand(Command):
                name = "test"
                help = "Run tests"

                def execute(self, args):
                    print("Running tests...")

            # CLI uses the registry to get commands:
            command_class = CommandRegistry.get_command("test")
            if command_class:
                command = command_class()
                command.execute(args)
    """

    _commands: ClassVar[dict[str, type[Command]]] = {}

    @classmethod
    def register(cls) -> Callable[[type[Command]], type[Command]]:
        """Decorator to register a command class.

        The command class must have a `name` attribute that identifies the command
        in the CLI (e.g., "init", "validate", "build").

        Returns:
            Decorator function that registers the command class.

        Example:
            Using the decorator::

                @CommandRegistry.register()
                class ServeCommand(Command):
                    name = "serve"
                    help = "Start development server"
                    description = "Run a local development server for testing"

                    def execute(self, args):
                        start_dev_server()

            The command can then be invoked::

                pedre serve
        """

        def decorator(command_class: type[Command]) -> type[Command]:
            if not command_class.name:
                logger.warning(
                    "Command class %s has no name, skipping registration",
                    command_class.__name__,
                )
                return command_class

            cls._commands[command_class.name] = command_class
            logger.debug("Registered command: %s", command_class.name)
            return command_class

        return decorator

    @classmethod
    def get_command(cls, command_name: str) -> type[Command] | None:
        """Get the command class for a command name.

        Args:
            command_name: The name of the command (e.g., "init", "validate").

        Returns:
            The Command class if registered, None otherwise.
        """
        return cls._commands.get(command_name)

    @classmethod
    def get_all_commands(cls) -> dict[str, type[Command]]:
        """Get all registered commands.

        Returns:
            Dictionary mapping command names to Command classes.
        """
        return cls._commands.copy()

    @classmethod
    def is_registered(cls, command_name: str) -> bool:
        """Check if a command is registered.

        Args:
            command_name: The command name to check.

        Returns:
            True if the command is registered, False otherwise.
        """
        return command_name in cls._commands

    @classmethod
    def clear(cls) -> None:
        """Clear the registry.

        Removes all registered commands. This is primarily useful
        for testing to ensure a clean state between tests.

        Warning:
            This should not be called in production code as it will break
            any code that depends on registered commands.
        """
        cls._commands.clear()
        logger.debug("Command registry cleared")
