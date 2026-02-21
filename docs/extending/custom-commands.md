# Custom Commands

Pedre's command system is extensible — you can add project-specific commands or distribute commands via installable packages.

## Project Commands

Create custom commands for your project by adding Python files to the `commands/` directory:

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

**Example: `commands/build.py`**

```python
"""Build command for packaging the game."""

import argparse
from pedre.commands.base import Command
from pedre.commands.registry import CommandRegistry


@CommandRegistry.register
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

**Run with:**

```bash
pedre build --output dist --platform windows
```

## External Package Commands

External packages can register commands using entry points. This is the recommended way for distributable packages.

### Step 1: Create Command Module

**`pedre_combat/commands.py`**

```python
"""Combat system commands for Pedre."""

import argparse
from pedre.commands.base import Command
from pedre.commands.registry import CommandRegistry


@CommandRegistry.register
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


@CommandRegistry.register
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

### Step 2: Register Entry Points

**`pyproject.toml`**

```toml
[project]
name = "pedre-combat"
version = "0.1.0"
dependencies = ["pedre"]

[project.entry-points."pedre.commands"]
balance = "pedre_combat.commands:BalanceCommand"
spawn = "pedre_combat.commands:SpawnCommand"
```

### Step 3: Install and Use

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

If multiple commands have the same name, the last one loaded wins (external packages can override built-in commands if needed).

## Command Base Class

All commands must inherit from `pedre.commands.base.Command`:

```python
from abc import ABC, abstractmethod
import argparse

class Command(ABC):
    """Base class for all CLI commands."""

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

### Command Design

1. **Use descriptive names** - Command names should be clear and concise
   - Good: `build`, `test`, `deploy`, `validate`
   - Avoid: `do_stuff`, `run`, `execute`

2. **Provide comprehensive help** - Always set `name`, `help`, and `description`
   - `name`: The command name used in CLI
   - `help`: Short one-line description (shown in command list)
   - `description`: Longer description (shown in command help page)

3. **Add type hints** - Use type hints for better IDE support

   ```python
   def add_arguments(self, parser: argparse.ArgumentParser) -> None:
       parser.add_argument("--count", type=int, help="Number of items")
   ```

4. **Use argparse features** - Add arguments with proper types, choices, and help

   ```python
   parser.add_argument("--format", choices=["json", "yaml"], default="json")
   parser.add_argument("--verbose", action="store_true")
   parser.add_argument("--output", type=Path, required=True)
   ```

### Error Handling

1. **Handle errors gracefully** - Catch exceptions and provide clear messages

   ```python
   def execute(self, args: argparse.Namespace) -> None:
       try:
           # Command logic
           pass
       except FileNotFoundError as e:
           console.print(f"[red]Error:[/red] {e}")
           sys.exit(1)
   ```

2. **Use appropriate exit codes** - Exit with non-zero status on errors

   ```python
   sys.exit(0)  # Success
   sys.exit(1)  # General error
   ```

3. **Validate input early** - Check arguments before performing operations

   ```python
   def execute(self, args: argparse.Namespace) -> None:
       if not args.output.exists():
           console.print("[red]Error:[/red] Output directory does not exist")
           sys.exit(1)
   ```

### Testing

Create unit tests for your commands:

```python
# tests/test_commands.py
import pytest
from argparse import Namespace
from my_game.commands.build import BuildCommand

def test_build_command():
    command = BuildCommand()
    args = Namespace(output="dist", platform="windows")

    # Test that command executes without error
    command.execute(args)

    # Verify expected behavior
    assert Path("dist").exists()
```

### Rich Console Output

Use Rich for better terminal output:

```python
from rich.console import Console
from rich.panel import Panel

console = Console()

def execute(self, args: argparse.Namespace) -> None:
    # Progress indicators
    with console.status("[bold green]Building project..."):
        # Long-running operation
        pass

    # Styled output
    console.print("[green]✓[/green] Build complete")

    # Panels for important information
    console.print(Panel(
        "[green bold]Build Successful[/green bold]\n\nOutput: dist/game.exe",
        border_style="green"
    ))
```

## Entry Point Naming

The entry point name (left side of `=`) is not used by Pedre — it's just for reference. The command's `name` attribute determines the actual CLI command:

```toml
# Entry point name can be anything
[project.entry-points."pedre.commands"]
my_balance_cmd = "pedre_combat.commands:BalanceCommand"  # Entry point name

# But the CLI command name comes from the class:
class BalanceCommand(Command):
    name = "balance"  # CLI command: "pedre balance"
```

Use descriptive entry point names for clarity, but remember only the `name` attribute matters for the CLI.

## Complete Example: Test Command

Here's a complete example of a custom test command:

```python
"""Test command for running game tests."""

import sys
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel

from pedre.commands.base import Command
from pedre.commands.registry import CommandRegistry

if TYPE_CHECKING:
    import argparse

console = Console()


@CommandRegistry.register
class TestCommand(Command):
    """Run game tests with pytest."""

    name = "test"
    help = "Run game tests"
    description = "Run game tests using pytest with optional coverage"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add test-specific arguments."""
        parser.add_argument(
            "--coverage",
            action="store_true",
            help="Generate coverage report",
        )
        parser.add_argument(
            "--verbose",
            "-v",
            action="store_true",
            help="Verbose output",
        )
        parser.add_argument(
            "path",
            nargs="?",
            default="tests",
            help="Test path (default: tests)",
        )

    def execute(self, args: argparse.Namespace) -> None:
        """Execute the test command."""
        console.print("\n[bold cyan]Running Tests[/bold cyan]")
        console.print("=" * 60)

        # Build pytest command
        cmd = ["pytest", args.path]

        if args.verbose:
            cmd.append("-v")

        if args.coverage:
            cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term"])

        # Run tests
        console.print(f"\n[dim]Command:[/dim] {' '.join(cmd)}\n")

        try:
            result = subprocess.run(cmd, check=False)

            if result.returncode == 0:
                console.print(Panel(
                    "[green bold]✓ All Tests Passed[/green bold]",
                    border_style="green",
                    expand=False,
                ))
                if args.coverage:
                    console.print("\n[dim]Coverage report: htmlcov/index.html[/dim]\n")
            else:
                console.print(Panel(
                    "[red bold]✗ Tests Failed[/red bold]",
                    border_style="red",
                    expand=False,
                ))
                sys.exit(1)

        except FileNotFoundError:
            console.print("[red]Error:[/red] pytest not found. Install with: pip install pytest")
            sys.exit(1)
```

**Usage:**

```bash
# Run all tests
pedre test

# Run specific test directory
pedre test tests/unit

# Run with coverage
pedre test --coverage

# Verbose output
pedre test -v
```

## See Also

- [CLI Guide](../guides/cli.md) - Built-in commands and installation
- [Custom Plugins](custom-plugins.md) - Build complete game plugins
