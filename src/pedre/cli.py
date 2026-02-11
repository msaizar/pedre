"""CLI commands for Pedre game framework.

This module provides command-line utilities for managing and validating Pedre game projects.

Usage:
    With uv (recommended):
        uv run pedre init              # Initialize a new project
        uv run pedre validate          # Run validation command
        uv run pedre                   # Show CLI help

    With pip install:
        pip install -e .               # Install in editable mode
        pedre init                     # Initialize a new project
        pedre validate                 # Run validation command
        pedre                          # Show CLI help

    As a uv tool:
        uv tool install pedre          # Install as a tool
        pedre init                     # Initialize a new project
        pedre validate                 # Run validation command
        pedre                          # Show CLI help
"""

import argparse
import logging

from rich.console import Console

from pedre.commands.loader import CommandLoader
from pedre.commands.registry import CommandRegistry

console = Console()
logger = logging.getLogger(__name__)


def main() -> None:
    """Main entry point for the Pedre CLI.

    Loads all registered commands and routes to the appropriate handler.
    """
    # Load all command modules to trigger registration
    loader = CommandLoader()
    loader.load_modules()

    # Create main parser
    parser = argparse.ArgumentParser(
        prog="pedre",
        description="Pedre game framework CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Register all commands with argparse
    commands = CommandRegistry.get_all_commands()
    command_instances = {}

    for command_class in commands.values():
        # Create command instance
        command_instance = command_class()
        command_instances[command_instance.name] = command_instance

        # Create subparser for this command
        command_parser = subparsers.add_parser(
            command_instance.name,
            help=command_instance.help,
            description=command_instance.description,
        )

        # Let the command add its arguments
        command_instance.add_arguments(command_parser)

    args = parser.parse_args()

    # Route to appropriate command
    if args.command and args.command in command_instances:
        command = command_instances[args.command]
        command.execute(args)
    else:
        # No subcommand provided - show help
        console.print("\n[bold cyan]Pedre CLI[/bold cyan]")
        console.print("=" * 60)
        console.print("\nAvailable commands:")
        for _command_name, command_class in sorted(commands.items()):
            command_instance = command_class()
            console.print(f"  [green]pedre {command_instance.name:12}[/green] - {command_instance.help}")
        console.print("\nRun [cyan]pedre <command> --help[/cyan] for more information on a command.\n")
