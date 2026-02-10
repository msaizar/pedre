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
import json
import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pedre.actions.loader import ActionLoader
from pedre.actions.registry import ActionRegistry
from pedre.conditions.loader import ConditionLoader
from pedre.conditions.registry import ConditionRegistry
from pedre.conf import settings
from pedre.events.loader import EventLoader
from pedre.events.registry import EventRegistry
from pedre.plugins.script.base import Script, ScriptValidationError

console = Console()
logger = logging.getLogger(__name__)


def init_project(args: argparse.Namespace) -> None:
    """Initialize a new Pedre project with the recommended directory structure.

    Creates the project structure based on settings variables:
    - assets/ (ASSETS_DIRECTORY)
      - audio/
        - music/
        - sfx/
      - data/
        - dialogs/ (DIALOGS_DIRECTORY)
        - scripts/ (SCRIPTS_DIRECTORY)
      - images/
      - maps/ (SCENE_MAPS_FOLDER)
    - main.py (basic game entry point)
    - settings.py (project configuration)

    Args:
        args: Parsed command-line arguments containing optional path parameter.
    """
    console.print("\n[bold cyan]Pedre Project Initializer[/bold cyan]")
    console.print("=" * 60)

    # Determine project root (default to current directory)
    project_root = args.path or Path.cwd()
    console.print(f"\n[dim]Project root:[/dim] {project_root}")

    # Check if directory already has files that might conflict
    if project_root.exists() and any(project_root.iterdir()):
        existing_files = list(project_root.iterdir())
        console.print(f"\n[yellow]⚠[/yellow] Directory is not empty ({len(existing_files)} items)")

        # Check for critical files
        critical_files = ["main.py", "settings.py", settings.ASSETS_DIRECTORY]
        conflicts = [f for f in critical_files if (project_root / f).exists()]

        if conflicts:
            console.print(f"[red]✗[/red] The following files/folders already exist: {', '.join(conflicts)}")
            console.print("[yellow]Project initialization cancelled to avoid overwriting existing files.[/yellow]\n")
            sys.exit(1)

    # Create directory structure
    console.print("\n[bold]Creating project structure...[/bold]\n")

    folders_to_create = [
        # Assets directory
        settings.ASSETS_DIRECTORY,
        # Audio folders
        f"{settings.ASSETS_DIRECTORY}/audio",
        f"{settings.ASSETS_DIRECTORY}/audio/music",
        f"{settings.ASSETS_DIRECTORY}/audio/sfx",
        # Data folders
        f"{settings.ASSETS_DIRECTORY}/data",
        f"{settings.ASSETS_DIRECTORY}/{settings.DIALOGS_DIRECTORY}",
        f"{settings.ASSETS_DIRECTORY}/{settings.SCRIPTS_DIRECTORY}",
        # Images folder
        f"{settings.ASSETS_DIRECTORY}/images",
        # Maps folder
        f"{settings.ASSETS_DIRECTORY}/{settings.SCENE_MAPS_FOLDER}",
    ]

    created_folders = []
    for folder in folders_to_create:
        folder_path = project_root / folder
        try:
            folder_path.mkdir(parents=True, exist_ok=True)
            created_folders.append(folder)
            console.print(f"[green]✓[/green] Created: {folder}/")
        except OSError as e:
            console.print(f"[red]✗[/red] Failed to create {folder}: {e}")
            sys.exit(1)

    # Create main.py
    main_py_content = '''"""Main entry point for the game."""

from pedre import run_game

if __name__ == "__main__":
    run_game()
'''
    main_py_path = project_root / "main.py"
    try:
        main_py_path.write_text(main_py_content)
        console.print("[green]✓[/green] Created: main.py")
    except OSError as e:
        console.print(f"[red]✗[/red] Failed to create main.py: {e}")
        sys.exit(1)

    # Create settings.py
    settings_py_content = '''"""Project settings for your Pedre game.

Override framework defaults by setting values here.
See: https://msaizar.github.io/pedre/guides/configuration/
"""

# Add your custom settings below
'''
    settings_py_path = project_root / "settings.py"
    try:
        settings_py_path.write_text(settings_py_content)
        console.print("[green]✓[/green] Created: settings.py")
    except OSError as e:
        console.print(f"[red]✗[/red] Failed to create settings.py: {e}")
        sys.exit(1)

    # Success message
    console.print(
        Panel(
            "[green bold]✓ Project Initialized Successfully[/green bold]\n\n"
            f"Created {len(created_folders)} folders and 2 files",
            border_style="green",
            expand=False,
        )
    )

    # Next steps
    console.print("\n[bold]Next steps:[/bold]\n")
    console.print("1. Create your first map in Tiled Map Editor")
    console.print(f"2. Save it as [cyan]{settings.ASSETS_DIRECTORY}/{settings.SCENE_MAPS_FOLDER}/map.tmx[/cyan]")
    console.print("3. Run your game with [green]python main.py[/green]")
    console.print("\n[dim]See the documentation: https://msaizar.github.io/pedre/getting-started/[/dim]\n")


def validate_scripts(args: argparse.Namespace) -> None:
    """Validate all game scripts for errors.

    Loads and validates all script files in the scripts directory, checking:
    - Trigger events are registered
    - Conditions have valid types
    - Actions have valid types
    - Scripts have at least one action
    - All parameters are correct

    Displays results using rich formatting with colors and tables.

    Args:
        args: Parsed command-line arguments containing optional path parameter.
    """
    console.print("\n[bold cyan]Pedre Script Validator[/bold cyan]")
    console.print("=" * 60)

    # Load registries (actions, events, conditions) BEFORE validating scripts
    console.print("\n[dim]Loading registries...[/dim]")

    action_loader = ActionLoader()
    action_loader.load_modules()

    event_loader = EventLoader()
    event_loader.load_modules()

    condition_loader = ConditionLoader()
    condition_loader.load_modules()

    console.print(
        f"[dim]Loaded {len(ActionRegistry.get_all_types())} actions, "
        f"{len(EventRegistry.get_all_types())} events, "
        f"{len(ConditionRegistry.get_all_types())} conditions[/dim]"
    )

    try:
        # Locate scripts directory
        # Look in the current working directory's assets folder, not the installed package
        # Use settings to get the relative path if no path provided
        scripts_dir = args.path or Path.cwd() / settings.ASSETS_DIRECTORY / settings.SCRIPTS_DIRECTORY

        if not scripts_dir.exists():
            console.print(f"\n[red]✗[/red] Scripts directory not found: {scripts_dir}")
            sys.exit(1)

        # Find all script files
        script_files = list(scripts_dir.glob("*_scripts.json"))

        if not script_files:
            console.print(f"\n[yellow]⚠[/yellow] No script files found in {scripts_dir}")
            sys.exit(0)

        console.print(f"\n[dim]Scripts directory:[/dim] {scripts_dir}")
        console.print(f"[dim]Found {len(script_files)} script file(s)[/dim]\n")

        # Load and parse all scripts
        scripts: dict[str, Script] = {}
        validation_errors: list[str] = []

        for script_file in script_files:
            try:
                with script_file.open() as f:
                    script_data = json.load(f)

                console.print(f"[dim]Loading:[/dim] {script_file.name} ({len(script_data)} scripts)")

                # Parse scripts
                valid_keys = {"trigger", "conditions", "scene", "run_once", "actions", "on_condition_fail"}

                for script_name, script_def in script_data.items():
                    # Check for unknown keys
                    unknown_keys = set(script_def.keys()) - valid_keys
                    if unknown_keys:
                        validation_errors.append(
                            f"Script '{script_name}': unknown keys {sorted(unknown_keys)} "
                            f"(valid keys: {sorted(valid_keys)})"
                        )

                    script = Script(
                        trigger=script_def.get("trigger"),
                        conditions=script_def.get("conditions", []),
                        scene=script_def.get("scene"),
                        run_once=script_def.get("run_once", False),
                        actions=script_def.get("actions", []),
                        on_condition_fail=script_def.get("on_condition_fail", []),
                    )

                    scripts[script_name] = script

            except json.JSONDecodeError as e:
                console.print(f"[red]✗[/red] Failed to parse {script_file.name}: {e}")
                sys.exit(1)
            except OSError as e:
                console.print(f"[red]✗[/red] Failed to load {script_file.name}: {e}")
                sys.exit(1)

        console.print(f"\n[bold]Total scripts loaded:[/bold] {len(scripts)}\n")

        # Validate all scripts
        errors = list(validation_errors)

        for script_name, script in scripts.items():
            # Validate trigger event
            if script.trigger:
                event_name = script.trigger.get("event")
                if not event_name:
                    errors.append(f"Script '{script_name}': trigger missing required 'event' key")
                elif not EventRegistry.is_registered(event_name):
                    errors.append(
                        f"Script '{script_name}': unknown event '{event_name}' "
                        f"(registered events: {', '.join(EventRegistry.get_all_types())})"
                    )
                else:
                    # Validate trigger filter keys
                    trigger_keys_set = EventRegistry.get_trigger_keys(event_name)
                    if trigger_keys_set is not None:
                        filter_keys = {k for k in script.trigger if k != "event"}
                        unknown_filter_keys = filter_keys - trigger_keys_set
                        if unknown_filter_keys:
                            errors.append(
                                f"Script '{script_name}': trigger has unknown filter keys "
                                f"{sorted(unknown_filter_keys)} for event '{event_name}' "
                                f"(valid keys: {sorted(trigger_keys_set)})"
                            )

            # Validate conditions
            for i, condition in enumerate(script.conditions):
                check_type = condition.get("check")
                if not check_type:
                    errors.append(f"Script '{script_name}': condition {i} missing required 'check' key")
                elif not ConditionRegistry.is_registered(check_type):
                    errors.append(
                        f"Script '{script_name}': unknown condition '{check_type}' "
                        f"(registered conditions: {', '.join(ConditionRegistry.get_all_types())})"
                    )
                else:
                    # Validate condition parameters
                    param_errors = ConditionRegistry.validate(check_type, condition)
                    errors.extend(
                        f"Script '{script_name}': condition {i} ({check_type}): {err}" for err in param_errors
                    )

            # Validate actions list is not empty
            if not script.actions:
                errors.append(f"Script '{script_name}': 'actions' list is empty")

            # Validate actions
            for i, action in enumerate(script.actions):
                action_type = action.get("type")
                if not action_type:
                    errors.append(f"Script '{script_name}': action {i} missing required 'type' key")
                elif not ActionRegistry.is_registered(action_type):
                    errors.append(
                        f"Script '{script_name}': unknown action type '{action_type}' "
                        f"(registered actions: {', '.join(ActionRegistry.get_all_types())})"
                    )
                else:
                    # Validate action parameters
                    param_errors = ActionRegistry.validate(action_type, action)
                    errors.extend(f"Script '{script_name}': action {i} ({action_type}): {err}" for err in param_errors)

            # Validate on_condition_fail actions
            for i, action in enumerate(script.on_condition_fail):
                action_type = action.get("type")
                if not action_type:
                    errors.append(f"Script '{script_name}': on_condition_fail action {i} missing required 'type' key")
                elif not ActionRegistry.is_registered(action_type):
                    errors.append(
                        f"Script '{script_name}': on_condition_fail action {i} has unknown type '{action_type}' "
                        f"(registered actions: {', '.join(ActionRegistry.get_all_types())})"
                    )
                else:
                    # Validate action parameters
                    param_errors = ActionRegistry.validate(action_type, action)
                    errors.extend(
                        f"Script '{script_name}': on_condition_fail action {i} ({action_type}): {err}"
                        for err in param_errors
                    )

        # Display results
        if errors:
            console.print(
                Panel(
                    f"[red bold]Validation Failed[/red bold]\n\n"
                    f"Found {len(errors)} error(s) in {len(scripts)} script(s)",
                    border_style="red",
                    expand=False,
                )
            )
            console.print("\n[bold red]Errors:[/bold red]\n")

            # Group errors by script
            error_table = Table(show_header=True, header_style="bold red", show_lines=True)
            error_table.add_column("#", style="dim", width=4)
            error_table.add_column("Error", style="red")

            for idx, error in enumerate(errors, 1):
                error_table.add_row(str(idx), error)

            console.print(error_table)
            console.print()
            sys.exit(1)
        else:
            console.print(
                Panel(
                    f"[green bold]✓ All Scripts Valid[/green bold]\n\nValidated {len(scripts)} script(s) successfully",
                    border_style="green",
                    expand=False,
                )
            )

            # Show summary table
            summary_table = Table(show_header=True, header_style="bold cyan")
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Count", justify="right", style="green")

            total_actions = sum(len(s.actions) for s in scripts.values())
            total_conditions = sum(len(s.conditions) for s in scripts.values())
            total_triggers = sum(1 for s in scripts.values() if s.trigger)

            summary_table.add_row("Total Scripts", str(len(scripts)))
            summary_table.add_row("Total Actions", str(total_actions))
            summary_table.add_row("Total Conditions", str(total_conditions))
            summary_table.add_row("Scripts with Triggers", str(total_triggers))

            console.print("\n[bold]Summary:[/bold]\n")
            console.print(summary_table)
            console.print()

    except ScriptValidationError as e:
        console.print(
            Panel(
                f"[red bold]Validation Failed[/red bold]\n\n{e}",
                border_style="red",
                expand=False,
            )
        )
        sys.exit(1)


def main() -> None:
    """Main entry point for the Pedre CLI.

    Parses subcommands and routes to the appropriate handler.
    """
    parser = argparse.ArgumentParser(
        prog="pedre",
        description="Pedre game framework CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init subcommand
    init_parser = subparsers.add_parser(
        "init",
        help="Initialize a new Pedre project",
        description="Create the recommended project directory structure",
    )
    init_parser.add_argument(
        "--path",
        "-p",
        type=Path,
        default=None,
        help="Path to project directory (default: current directory)",
    )

    # Validate subcommand
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate game scripts",
        description="Validate all game scripts for errors",
    )
    validate_parser.add_argument(
        "--path",
        "-p",
        type=Path,
        default=None,
        help=f"Path to scripts directory (default: {settings.ASSETS_DIRECTORY}/{settings.SCRIPTS_DIRECTORY})",
    )

    args = parser.parse_args()

    # Route to appropriate subcommand
    if args.command == "init":
        init_project(args)
    elif args.command == "validate":
        validate_scripts(args)
    else:
        # No subcommand provided - show help
        console.print("\n[bold cyan]Pedre CLI[/bold cyan]")
        console.print("=" * 60)
        console.print("\nAvailable commands:")
        console.print("  [green]pedre init[/green]      - Initialize a new Pedre project")
        console.print("  [green]pedre validate[/green]  - Validate game scripts")
        console.print("\nRun [cyan]pedre <command> --help[/cyan] for more information on a command.\n")
