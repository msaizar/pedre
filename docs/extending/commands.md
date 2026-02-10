# Pedre CLI Commands

The Pedre CLI provides an extensible command system with automatic discovery. Commands are discovered from three sources:

1. **Framework commands** - Built-in commands in `pedre/commands/`
2. **Project commands** - User commands in `<project_root>/commands/`
3. **External packages** - Commands registered via entry points

## Creating Project Commands

Simply create Python files in your project's `commands/` directory:

```text
my_game/
├── commands/
│   ├── __init__.py      # Can be empty
│   ├── build.py
│   └── deploy.py
├── assets/
├── main.py
└── settings.py
```

Example: `commands/build.py`

```python
"""Build command for packaging the game."""

import argparse
from pedre.commands.base import Command
from pedre.commands.registry import CommandRegistry


@CommandRegistry.register()
class BuildCommand(Command):
    """Build and package the game for distribution."""

    name = "build"
    help = "Build the game project"
    description = "Compile and package the game for distribution"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        parser.add_argument(
            "--output",
            "-o",
            default="dist",
            help="Output directory (default: dist)",
        )
        parser.add_argument(
            "--platform",
            choices=["windows", "mac", "linux"],
            help="Target platform",
        )

    def execute(self, args: argparse.Namespace) -> None:
        """Execute the build command."""
        print(f"Building game for {args.platform or 'all platforms'}...")
        print(f"Output directory: {args.output}")
        # Build implementation here
```

Run with: `pedre build --output dist --platform windows`

## Creating External Package Commands

External packages can register commands using entry points. This is the recommended way for distributable packages to extend the Pedre CLI.

### Step 1: Create your command module

`pedre_combat/commands.py`

```python
"""Combat system commands for Pedre."""

import argparse
from pedre.commands.base import Command
from pedre.commands.registry import CommandRegistry


@CommandRegistry.register()
class BalanceCommand(Command):
    """Balance combat statistics."""

    name = "balance"
    help = "Balance combat stats"
    description = "Analyze and balance combat statistics"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--interactive", action="store_true", help="Interactive mode")

    def execute(self, args: argparse.Namespace) -> None:
        print("Balancing combat statistics...")
        # Implementation here


@CommandRegistry.register()
class SpawnCommand(Command):
    """Spawn enemies for testing."""

    name = "spawn"
    help = "Spawn test enemies"
    description = "Spawn enemies for combat testing"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("enemy_type", help="Type of enemy to spawn")
        parser.add_argument("--count", type=int, default=1, help="Number to spawn")

    def execute(self, args: argparse.Namespace) -> None:
        print(f"Spawning {args.count} {args.enemy_type} enemies...")
        # Implementation here
```

### Step 2: Register entry points in pyproject.toml

`pyproject.toml`

```toml
[project]
name = "pedre-combat"
version = "0.1.0"
dependencies = ["pedre"]

[project.entry-points."pedre.commands"]
balance = "pedre_combat.commands:BalanceCommand"
spawn = "pedre_combat.commands:SpawnCommand"
```

### Step 3: Install and use

```bash
# Install your package
pip install pedre-combat

# Commands are now available
pedre balance --interactive
pedre spawn goblin --count 5
```

## Command Discovery Order

Commands are loaded in this order:

1. Framework commands from `pedre/commands/`
2. Project commands from `<project_root>/commands/`
3. External package commands via `pedre.commands` entry points

If multiple commands have the same name, the last one loaded wins (so external packages can override built-in commands if needed).

## Command Base Class

All commands must inherit from `pedre.commands.base.Command`:

```python
from abc import ABC, abstractmethod
import argparse

class Command(ABC):
    # Required attributes
    name: str = ""              # Command name (e.g., "build")
    help: str = ""              # Short help text
    description: str = ""       # Long description

    # Optional method
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        pass

    # Required method
    @abstractmethod
    def execute(self, args: argparse.Namespace) -> None:
        """Execute the command."""
        pass
```

## Best Practices

1. **Use descriptive names** - Command names should be clear and concise (e.g., `build`, `test`, `deploy`)
2. **Add type hints** - Use type hints for better IDE support
3. **Provide help text** - Always set `name`, `help`, and `description`
4. **Use argparse features** - Add arguments with proper types, choices, and help text
5. **Handle errors gracefully** - Catch exceptions and provide clear error messages
6. **Use `sys.exit()`** - Exit with non-zero status on errors: `sys.exit(1)`
7. **Test your commands** - Create unit tests for command logic

## Entry Point Naming

The entry point name (left side of `=`) is not used by Pedre - it's just for reference. The command's `name` attribute determines the actual CLI command:

```toml
# Entry point name can be anything
[project.entry-points."pedre.commands"]
my_balance_cmd = "pedre_combat.commands:BalanceCommand"  # Entry point name: "my_balance_cmd"

# But the CLI command name comes from the class:
class BalanceCommand(Command):
    name = "balance"  # CLI command: "pedre balance"
```

Use descriptive entry point names for clarity, but remember only the `name` attribute matters for the CLI.
