"""Base command class for CLI commands."""

import logging
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import argparse

logger = logging.getLogger(__name__)


class Command(ABC):
    """Base class for all CLI commands.

    Each command must define:
    - name: The command name (e.g., "init", "validate")
    - help: Short help text shown in command list
    - description: Longer description for command help page

    Commands can optionally override:
    - add_arguments: Add command-specific arguments to the parser
    - execute: Run the command with parsed arguments

    Example:
        Creating a custom command::

            from pedre.commands.base import Command
            from pedre.commands.registry import CommandRegistry

            @CommandRegistry.register()
            class MyCommand(Command):
                name = "mycommand"
                help = "Does something useful"
                description = "Longer description of what this command does"

                def add_arguments(self, parser):
                    parser.add_argument("--option", help="An option")

                def execute(self, args):
                    print(f"Executing with option: {args.option}")
    """

    # Subclasses must define these
    name: str = ""
    help: str = ""
    description: str = ""

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments to the argument parser.

        Override this method to add arguments specific to your command.
        The parser is already configured with the command name and description.

        Args:
            parser: The ArgumentParser for this subcommand.

        Example:
            Adding arguments::

                def add_arguments(self, parser):
                    parser.add_argument("--path", type=Path, help="Project path")
                    parser.add_argument("--verbose", action="store_true")
        """
        return

    @abstractmethod
    def execute(self, args: argparse.Namespace) -> None:
        """Execute the command.

        This method is called when the user runs this command.
        All command-specific arguments will be available in the args namespace.

        Args:
            args: Parsed command-line arguments.

        Example:
            Implementing execute::

                def execute(self, args):
                    console.print(f"Running command with path: {args.path}")
                    # Command implementation here
        """
