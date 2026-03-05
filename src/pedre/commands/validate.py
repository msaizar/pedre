"""Validate command for checking game assets."""

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
from pedre.main import setup_resources
from pedre.validators.context import ValidationContext
from pedre.validators.dialog_validator import DialogValidator
from pedre.validators.items_validator import ItemsValidator
from pedre.validators.map_validator import MapValidator
from pedre.validators.npcs_validator import NPCsValidator
from pedre.validators.script_validator import ScriptValidator
from pedre.validators.sprites_validator import SpritesValidator

if TYPE_CHECKING:
    import argparse

console = Console()


@CommandRegistry.register
class ValidateCommand(Command):
    """Validate all game assets for errors."""

    name = "validate"
    help = "Validate all game assets"
    description = "Validate all game assets for errors"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add validate-specific arguments."""
        parser.add_argument(
            "--scripts-path",
            type=Path,
            default=None,
            help=f"Path to scripts directory (default: {settings.ASSETS_DIRECTORY}/{settings.SCRIPTS_DIRECTORY})",
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
            help=f"Path to maps directory (default: {settings.ASSETS_DIRECTORY}/{settings.SCENE_MAPS_DIRECTORY})",
        )
        parser.add_argument(
            "--items-path",
            type=Path,
            default=None,
            help=(
                f"Path to inventory items file (default: {settings.ASSETS_DIRECTORY}/{settings.CONTENT_DIRECTORY}"
                "/items.json)"
            ),
        )
        parser.add_argument(
            "--sprites-path",
            type=Path,
            default=None,
            help=(
                f"Path to sprites file (default: {settings.ASSETS_DIRECTORY}/{settings.CONTENT_DIRECTORY}/sprites.json)"
            ),
        )
        parser.add_argument(
            "--npcs-path",
            type=Path,
            default=None,
            help=(f"Path to NPCs file (default: {settings.ASSETS_DIRECTORY}/{settings.CONTENT_DIRECTORY}/npcs.json)"),
        )

    def execute(self, args: argparse.Namespace) -> None:
        """Validate all game assets for errors.

        Runs all validators against maps, scripts, dialogs, items, sprites,
        and NPCs. Displays results using rich formatting with colors and tables.

        Args:
            args: Parsed command-line arguments containing optional path parameters.
        """
        setup_resources(settings.ASSETS_HANDLE)
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
            f"[dim]Loaded {len(ActionRegistry.get_all_names())} actions, "
            f"{len(EventRegistry.get_all_names())} events, "
            f"{len(ConditionRegistry.get_all_names())} conditions[/dim]"
        )

        # Resolve paths
        content_dir = Path.cwd() / settings.ASSETS_DIRECTORY / settings.CONTENT_DIRECTORY
        maps_path_arg = getattr(args, "maps_path", None)
        scripts_path_arg = getattr(args, "scripts_path", None)
        dialogs_path_arg = getattr(args, "dialogs_path", None)
        maps_dir = maps_path_arg or Path.cwd() / settings.ASSETS_DIRECTORY / settings.SCENE_MAPS_DIRECTORY
        scripts_dir = scripts_path_arg or Path.cwd() / settings.ASSETS_DIRECTORY / settings.SCRIPTS_DIRECTORY
        dialogs_dir = dialogs_path_arg or Path.cwd() / settings.ASSETS_DIRECTORY / settings.DIALOGS_DIRECTORY
        items_path_arg = getattr(args, "items_path", None)
        sprites_path_arg = getattr(args, "sprites_path", None)
        npcs_path_arg = getattr(args, "npcs_path", None)
        items_file = items_path_arg or content_dir / "items.json"
        sprites_file = sprites_path_arg or content_dir / "sprites.json"
        npcs_file = npcs_path_arg or content_dir / "npcs.json"

        # Create shared validation context
        context = ValidationContext()

        # Build validator list — order matters: sprites before npcs (for cross-ref context).
        # All validators are optional: only included if explicitly provided or the default path exists.
        validators = []
        if maps_path_arg or maps_dir.exists():
            validators.append(MapValidator(maps_dir, context))
        if items_path_arg or items_file.exists():
            validators.append(ItemsValidator(items_file, context))
        if sprites_path_arg or sprites_file.exists():
            validators.append(SpritesValidator(sprites_file, context))
        if npcs_path_arg or npcs_file.exists():
            validators.append(NPCsValidator(npcs_file, context))
        if scripts_path_arg or scripts_dir.exists():
            validators.append(ScriptValidator(scripts_dir, context))
        if dialogs_path_arg or dialogs_dir.exists():
            validators.append(DialogValidator(dialogs_dir, context))

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
