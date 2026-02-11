"""Validate command for checking game scripts and dialogs."""

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from pedre.actions.loader import ActionLoader
from pedre.actions.registry import ActionRegistry
from pedre.commands.base import Command
from pedre.commands.registry import CommandRegistry
from pedre.conditions.loader import ConditionLoader
from pedre.conditions.registry import ConditionRegistry
from pedre.conf import settings
from pedre.events.loader import EventLoader
from pedre.events.registry import EventRegistry
from pedre.validators.context import ValidationContext
from pedre.validators.dialog_validator import DialogValidator
from pedre.validators.map_validator import MapValidator
from pedre.validators.script_validator import ScriptValidator

if TYPE_CHECKING:
    import argparse

console = Console()


@CommandRegistry.register()
class ValidateCommand(Command):
    """Validate game scripts and dialogs for errors."""

    name = "validate"
    help = "Validate game scripts and dialogs"
    description = "Validate all game scripts and dialogs for errors"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add validate-specific arguments."""
        parser.add_argument(
            "--scripts-path",
            type=Path,
            default=None,
            help=f"Path to scripts directory (default: {settings.ASSETS_DIRECTORY}/{settings.SCRIPTS_DIRECTORY})",
        )
        parser.add_argument(
            "--type",
            "-t",
            choices=["all", "scripts", "dialogs", "maps"],
            default="all",
            help="Type of validation to run (default: all)",
        )
        parser.add_argument(
            "--dialogs-path",
            type=Path,
            default=None,
            help=f"Path to dialogs directory (default: {settings.ASSETS_DIRECTORY}/{settings.DIALOGS_DIRECTORY})",
        )
        parser.add_argument(
            "--maps-path",
            type=Path,
            default=None,
            help=f"Path to maps directory (default: {settings.ASSETS_DIRECTORY}/{settings.SCENE_MAPS_FOLDER})",
        )

    def execute(self, args: argparse.Namespace) -> None:
        """Validate game scripts and dialogs for errors.

        Loads and validates script and dialog files, checking:
        - Script triggers, conditions, and actions are valid
        - Dialog structure and required fields
        - All parameters are correct

        Displays results using rich formatting with colors and tables.

        Args:
            args: Parsed command-line arguments containing optional path parameters.
        """
        console.print("\n[bold cyan]Pedre Validator[/bold cyan]")
        console.print("=" * 60)

        # Load registries (actions, events, conditions) BEFORE validating
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

        # Create shared validation context
        context = ValidationContext()

        # Determine which validators to run based on args.type
        validation_type = getattr(args, "type", "all")
        dialogs_path_arg = getattr(args, "dialogs_path", None)
        scripts_path_arg = getattr(args, "scripts_path", None)
        maps_path_arg = getattr(args, "maps_path", None)

        # Always create MapValidator to populate context, but only add to validators list if needed for validation
        maps_dir = maps_path_arg or Path.cwd() / settings.ASSETS_DIRECTORY / settings.SCENE_MAPS_FOLDER
        map_validator = MapValidator(maps_dir, context)

        # Determine which validators to run
        validators = []

        if validation_type in ["all", "scripts"]:
            scripts_dir = scripts_path_arg or Path.cwd() / settings.ASSETS_DIRECTORY / settings.SCRIPTS_DIRECTORY
            validators.append(ScriptValidator(scripts_dir, context))

        if validation_type in ["all", "dialogs"]:
            dialogs_dir = dialogs_path_arg or Path.cwd() / settings.ASSETS_DIRECTORY / settings.DIALOGS_DIRECTORY
            validators.append(DialogValidator(dialogs_dir, context))

        if validation_type in ["all", "maps"]:
            validators.append(map_validator)

        # Always populate context from maps (needed for cross-reference validation)
        # Run map validation silently if it's not in the validators list
        if validation_type not in {"all", "maps"}:
            map_validator.validate()  # Populates context but we don't report errors

        # Phase 1: Structural validation (also populates context)
        console.print("\n[bold]Phase 1: Structural Validation[/bold]")
        all_errors = []
        all_metadata = {}
        total_items = 0

        for validator in validators:
            console.print(f"\n[bold]Validating {validator.name}...[/bold]")
            result = validator.validate()

            if result.errors:
                all_errors.extend(result.errors)

            all_metadata[validator.name] = result.metadata
            all_metadata[validator.name]["Count"] = result.item_count
            total_items += result.item_count

            console.print(f"[dim]Found {result.item_count} {validator.name.lower()}[/dim]")

        # Phase 2: Cross-reference validation
        console.print("\n[bold]Phase 2: Cross-Reference Validation[/bold]")

        for validator in validators:
            result = validator.validate_cross_references()

            if result.errors:
                all_errors.extend(result.errors)

            # Merge cross-ref metadata
            if result.metadata:
                for key, value in result.metadata.items():
                    all_metadata[validator.name][f"Cross-ref {key}"] = value

        # Display results
        if all_errors:
            console.print(
                Panel(
                    f"[red bold]Validation Failed[/red bold]\n\n"
                    f"Found {len(all_errors)} error(s) across {total_items} item(s)",
                    border_style="red",
                    expand=False,
                )
            )
            console.print("\n[bold red]Errors:[/bold red]\n")

            # Display errors in table
            error_table = Table(show_header=True, header_style="bold red", show_lines=True)
            error_table.add_column("#", style="dim", width=4)
            error_table.add_column("Error", style="red")

            for idx, error in enumerate(all_errors, 1):
                error_table.add_row(str(idx), error)

            console.print(error_table)
            console.print()
            sys.exit(1)
        else:
            console.print(
                Panel(
                    f"[green bold]✓ All Validations Passed[/green bold]\n\n"
                    f"Validated {total_items} item(s) successfully",
                    border_style="green",
                    expand=False,
                )
            )

            # Show summary table
            summary_table = Table(show_header=True, header_style="bold cyan")
            summary_table.add_column("Type", style="cyan")
            summary_table.add_column("Metric", style="cyan")
            summary_table.add_column("Count", justify="right", style="green")

            for validator_name, metadata in all_metadata.items():
                # Add count first
                count = metadata.get("Count", 0)
                summary_table.add_row(validator_name, "Total", str(count))

                # Add other metrics
                for key, value in metadata.items():
                    if key != "Count":
                        summary_table.add_row("", key, str(value))

            console.print("\n[bold]Summary:[/bold]\n")
            console.print(summary_table)
            console.print()
