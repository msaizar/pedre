"""CLI commands package for Pedre.

This package provides extensible CLI commands using a registry pattern
with auto-discovery. Commands register themselves using the
@CommandRegistry.register decorator and are automatically discovered
by the CommandLoader.

Auto-Discovery:
    Commands are automatically discovered from three sources:
    1. Framework commands in pedre.commands/ (always loaded)
    2. Project commands in <project_root>/commands/ (if directory exists)
    3. External packages via entry points

    Simply create a new Python file with a Command class and it will be
    automatically available in the CLI - no configuration needed!

Example:
    Creating a project command (auto-discovered)::

        # In your_game/commands/build.py
        from pedre.commands.base import Command
        from pedre.commands.registry import CommandRegistry

        @CommandRegistry.register()
        class BuildCommand(Command):
            name = "build"
            help = "Build the game project"
            description = "Compile and package the game for distribution"

            def add_arguments(self, parser):
                parser.add_argument("--output", help="Output directory")

            def execute(self, args):
                print(f"Building project to {args.output}...")

        # No configuration needed - automatically discovered!
        # Run with: pedre build --output dist/

    Creating an external package command::

        # In your package's commands module
        from pedre.commands.base import Command
        from pedre.commands.registry import CommandRegistry

        @CommandRegistry.register()
        class BalanceCommand(Command):
            name = "balance"
            help = "Balance combat stats"

            def execute(self, args):
                print("Balancing combat...")

        # In your package's pyproject.toml:
        [project.entry-points."pedre.commands"]
        balance = "pedre_combat.commands:BalanceCommand"
        spawn = "pedre_combat.commands:SpawnCommand"

        # Now available as: pedre balance, pedre spawn

    Project structure::

        my_game/
        ├── commands/           # Your custom commands (auto-discovered!)
        │   ├── __init__.py     # Can be empty
        │   ├── build.py        # Build command
        │   └── deploy.py       # Deploy command
        ├── assets/
        ├── main.py
        └── settings.py
"""

from pedre.commands.base import Command
from pedre.commands.loader import CommandLoader
from pedre.commands.registry import CommandRegistry

__all__ = ["Command", "CommandLoader", "CommandRegistry"]
