"""Initialize command for creating new Pedre projects."""

import sys
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console
from rich.panel import Panel

from pedre.commands.base import Command
from pedre.commands.registry import CommandRegistry
from pedre.conf import settings

if TYPE_CHECKING:
    import argparse

console = Console()


@CommandRegistry.register
class InitCommand(Command):
    """Initialize a new Pedre project with the recommended directory structure."""

    name = "init"
    help = "Initialize a new Pedre project"
    description = "Create the recommended project directory structure"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add init-specific arguments."""
        parser.add_argument(
            "--path",
            "-p",
            type=Path,
            default=None,
            help="Path to project directory (default: current directory)",
        )

    def execute(self, args: argparse.Namespace) -> None:
        """Initialize a new Pedre project.

        Creates the project structure based on settings variables:
        - assets/ (ASSETS_DIRECTORY)
          - audio/
            - music/
            - sfx/
          - data/
            - dialogs/ (DIALOGS_DIRECTORY)
            - scripts/ (SCRIPTS_DIRECTORY)
          - images/
          - maps/ (SCENE_MAPS_DIRECTORY)
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
                console.print(
                    "[yellow]Project initialization cancelled to avoid overwriting existing files.[/yellow]\n"
                )
                sys.exit(1)

        # Create directory structure
        console.print("\n[bold]Creating project structure...[/bold]\n")

        folders_to_create = [
            # Assets directory
            settings.ASSETS_DIRECTORY,
            # Audio folders
            f"{settings.ASSETS_DIRECTORY}/{settings.AUDIO_MUSIC_DIRECTORY}",
            f"{settings.ASSETS_DIRECTORY}/{settings.AUDIO_SFX_DIRECTORY}",
            # Data folders
            f"{settings.ASSETS_DIRECTORY}/data",
            f"{settings.ASSETS_DIRECTORY}/{settings.DIALOGS_DIRECTORY}",
            f"{settings.ASSETS_DIRECTORY}/{settings.SCRIPTS_DIRECTORY}",
            # Images folder
            f"{settings.ASSETS_DIRECTORY}/images",
            # Maps folder
            f"{settings.ASSETS_DIRECTORY}/{settings.SCENE_MAPS_DIRECTORY}",
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
        console.print(f"2. Save it as [cyan]{settings.ASSETS_DIRECTORY}/{settings.SCENE_MAPS_DIRECTORY}/map.tmx[/cyan]")
        console.print("3. Run your game with [green]python main.py[/green]")
        console.print("\n[dim]See the documentation: https://msaizar.github.io/pedre/getting-started/[/dim]\n")
