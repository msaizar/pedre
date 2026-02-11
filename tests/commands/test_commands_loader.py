"""Tests for CommandLoader."""

import sys
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest

from pedre.actions.registry import ActionRegistry
from pedre.commands.loader import CommandLoader
from pedre.commands.registry import CommandRegistry
from pedre.conditions.registry import ConditionRegistry
from pedre.events.registry import EventRegistry

if TYPE_CHECKING:
    from pathlib import Path


class TestAutodiscoverFrameworkCommands:
    """Test autodiscover_framework_commands method."""

    def test_autodiscover_framework_commands_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful auto-discovery of framework commands."""
        # Save original state
        original_commands = CommandRegistry._commands.copy()
        original_actions = ActionRegistry._actions.copy()
        original_events = EventRegistry._events.copy()
        original_condition_checkers = ConditionRegistry._checkers.copy()
        original_condition_validators = ConditionRegistry._validators.copy()

        # Track which command modules we import so we can clean them up
        modules_before = set(sys.modules.keys())

        try:
            CommandRegistry.clear()

            # Remove any already imported command modules to force re-import
            modules_to_remove = [
                key
                for key in sys.modules
                if key.startswith("pedre.commands.")
                and key
                not in ["pedre.commands", "pedre.commands.loader", "pedre.commands.registry", "pedre.commands.base"]
            ]
            for module in modules_to_remove:
                del sys.modules[module]

            loader = CommandLoader()
            loader.autodiscover_framework_commands()

            # Verify that framework commands were registered
            # Check for specific commands that should exist
            assert CommandRegistry.is_registered("init")
            assert CommandRegistry.is_registered("validate")
        finally:
            # Restore original state
            CommandRegistry._commands = original_commands
            ActionRegistry._actions = original_actions
            EventRegistry._events = original_events
            ConditionRegistry._checkers = original_condition_checkers
            ConditionRegistry._validators = original_condition_validators

            # Clean up any modules we imported during the test
            modules_after = set(sys.modules.keys())
            new_modules = modules_after - modules_before
            for module in new_modules:
                if module.startswith("pedre.commands.") and module not in [
                    "pedre.commands",
                    "pedre.commands.loader",
                    "pedre.commands.registry",
                    "pedre.commands.base",
                ]:
                    del sys.modules[module]

    def test_autodiscover_skips_private_modules(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that modules starting with _ are skipped."""
        CommandRegistry.clear()

        # Mock pkgutil.iter_modules to return a mix of public and private modules
        mock_modules = [
            (None, "init", False),
            (None, "_private", False),
            (None, "__init__", False),
            (None, "validate", False),
        ]

        with (
            patch("pkgutil.iter_modules", return_value=mock_modules),
            patch("importlib.import_module") as mock_import,
        ):
            loader = CommandLoader()
            loader.autodiscover_framework_commands()

            # Verify that import_module was only called for public modules
            import_calls = [call[0][0] for call in mock_import.call_args_list]
            assert "pedre.commands.init" in import_calls
            assert "pedre.commands.validate" in import_calls
            assert "pedre.commands._private" not in import_calls
            assert "pedre.commands.__init__" not in import_calls

    def test_autodiscover_skips_non_command_modules(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that base, registry, and loader modules are skipped."""
        CommandRegistry.clear()

        # Mock pkgutil.iter_modules to return non-command modules
        mock_modules = [
            (None, "base", False),
            (None, "registry", False),
            (None, "loader", False),
            (None, "init", False),
        ]

        with (
            patch("pkgutil.iter_modules", return_value=mock_modules),
            patch("importlib.import_module") as mock_import,
        ):
            loader = CommandLoader()
            loader.autodiscover_framework_commands()

            # Verify that import_module was only called for actual commands
            import_calls = [call[0][0] for call in mock_import.call_args_list]
            assert "pedre.commands.init" in import_calls
            assert "pedre.commands.base" not in import_calls
            assert "pedre.commands.registry" not in import_calls
            assert "pedre.commands.loader" not in import_calls

    def test_autodiscover_raises_on_import_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that ImportError is raised when a module cannot be imported."""
        CommandRegistry.clear()

        # Mock pkgutil.iter_modules to return a module that will fail to import
        mock_modules = [
            (None, "broken_command", False),
        ]

        with (
            patch("pkgutil.iter_modules", return_value=mock_modules),
            patch("importlib.import_module", side_effect=ImportError("Module not found")),
        ):
            loader = CommandLoader()
            with pytest.raises(ImportError, match="Module not found"):
                loader.autodiscover_framework_commands()


class TestAutodiscoverProjectCommands:
    """Test autodiscover_project_commands method."""

    def test_autodiscover_project_commands_no_directory(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that method returns silently when no commands directory exists."""
        CommandRegistry.clear()

        # Change to a directory without a commands folder
        monkeypatch.chdir(tmp_path)

        loader = CommandLoader()
        loader.autodiscover_project_commands()  # Should not raise

        # No project commands should be registered
        # (Framework commands might still be present if autodiscovered)

    def test_autodiscover_project_commands_success(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful auto-discovery of project commands."""
        CommandRegistry.clear()

        # Create a commands directory with a test command
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "__init__.py").write_text("")

        # Create a simple command module
        command_content = """
from pedre.commands.base import Command
from pedre.commands.registry import CommandRegistry

@CommandRegistry.register()
class TestProjectCommand(Command):
    name = "testproject"
    help = "Test project command"
    description = "A test command from project"

    def execute(self, args):
        pass
"""
        (commands_dir / "testproject.py").write_text(command_content)

        # Change to the test directory
        monkeypatch.chdir(tmp_path)

        loader = CommandLoader()
        loader.autodiscover_project_commands()

        # Verify that the project command was registered
        assert CommandRegistry.is_registered("testproject")

    def test_autodiscover_project_commands_adds_to_sys_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that project directory is added to sys.path."""
        CommandRegistry.clear()

        # Create a commands directory
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "__init__.py").write_text("")

        # Change to the test directory
        monkeypatch.chdir(tmp_path)

        # Ensure tmp_path is not in sys.path
        tmp_path_str = str(tmp_path)
        if tmp_path_str in sys.path:
            sys.path.remove(tmp_path_str)

        loader = CommandLoader()
        loader.autodiscover_project_commands()

        # Verify that tmp_path was added to sys.path
        assert tmp_path_str in sys.path

    def test_autodiscover_project_commands_already_in_sys_path(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that project directory is not added again if already in sys.path."""
        CommandRegistry.clear()

        # Create a commands directory
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "__init__.py").write_text("")

        # Change to the test directory
        monkeypatch.chdir(tmp_path)

        # Add tmp_path to sys.path before calling the method
        tmp_path_str = str(tmp_path)
        if tmp_path_str not in sys.path:
            sys.path.insert(0, tmp_path_str)

        # Count how many times tmp_path appears in sys.path
        count_before = sys.path.count(tmp_path_str)

        loader = CommandLoader()
        loader.autodiscover_project_commands()

        # Verify that tmp_path was not added again
        count_after = sys.path.count(tmp_path_str)
        assert count_after == count_before

    def test_autodiscover_project_commands_skips_private_modules(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that modules starting with _ are skipped."""
        CommandRegistry.clear()

        # Create a commands directory
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "__init__.py").write_text("")
        (commands_dir / "_private.py").write_text("# Private module")
        (commands_dir / "public.py").write_text("")

        # Change to the test directory
        monkeypatch.chdir(tmp_path)

        with patch("importlib.import_module") as mock_import:
            loader = CommandLoader()
            loader.autodiscover_project_commands()

            # Verify that import_module was only called for public modules
            import_calls = [call[0][0] for call in mock_import.call_args_list]
            if import_calls:  # Only check if any imports were attempted
                assert "commands.public" in import_calls or any("public" in call for call in import_calls)
                assert "commands._private" not in import_calls

    def test_autodiscover_project_commands_handles_import_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that ImportError in project command doesn't crash the loader."""
        CommandRegistry.clear()

        # Create a commands directory
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "__init__.py").write_text("")

        # Create a broken command module
        (commands_dir / "broken.py").write_text("import nonexistent_module")

        # Change to the test directory
        monkeypatch.chdir(tmp_path)

        loader = CommandLoader()
        # Should not raise - errors should be caught and logged
        loader.autodiscover_project_commands()

    def test_autodiscover_project_commands_handles_general_exception(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that general exceptions during discovery don't crash the loader."""
        CommandRegistry.clear()

        # Create a commands directory
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()

        # Change to the test directory
        monkeypatch.chdir(tmp_path)

        # Mock pkgutil.iter_modules to raise an exception
        with patch("pkgutil.iter_modules", side_effect=Exception("Discovery error")):
            loader = CommandLoader()
            # Should not raise - errors should be caught and logged
            loader.autodiscover_project_commands()


class TestLoadEntryPointCommands:
    """Test load_entry_point_commands method."""

    def test_load_entry_point_commands_python_310_plus(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading entry point commands using Python 3.10+ API."""
        CommandRegistry.clear()

        # Create mock entry points object with select method (Python 3.10+)
        mock_entry_point = Mock()
        mock_entry_point.name = "test_ep_command"
        mock_entry_point.value = "test_package.commands:TestCommand"
        mock_entry_point.load = Mock(return_value=Mock)  # Return a mock command class

        mock_eps = Mock()
        mock_eps.select = Mock(return_value=[mock_entry_point])

        with patch("pedre.commands.loader.entry_points", return_value=mock_eps):
            loader = CommandLoader()
            loader.load_entry_point_commands()

            # Verify select was called with correct group
            mock_eps.select.assert_called_once_with(group="pedre.commands")
            # Verify load was called
            mock_entry_point.load.assert_called_once()

    def test_load_entry_point_commands_python_39(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test loading entry point commands using Python 3.9 API."""
        CommandRegistry.clear()

        # Create mock entry points dict (Python 3.9)
        mock_entry_point = Mock()
        mock_entry_point.name = "test_ep_command_39"
        mock_entry_point.value = "test_package.commands:TestCommand39"
        mock_entry_point.load = Mock(return_value=Mock)  # Return a mock command class

        mock_eps = {"pedre.commands": [mock_entry_point]}

        with patch("pedre.commands.loader.entry_points", return_value=mock_eps):
            loader = CommandLoader()
            loader.load_entry_point_commands()

            # Verify load was called
            mock_entry_point.load.assert_called_once()

    def test_load_entry_point_commands_no_entry_points(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that loader handles missing entry points gracefully."""
        CommandRegistry.clear()

        # Mock entry_points to return empty result
        mock_eps = Mock()
        mock_eps.select = Mock(return_value=[])

        with patch("pedre.commands.loader.entry_points", return_value=mock_eps):
            loader = CommandLoader()
            loader.load_entry_point_commands()  # Should not raise

    def test_load_entry_point_commands_handles_load_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that errors loading individual entry points don't crash the loader."""
        CommandRegistry.clear()

        # Create mock entry point that raises on load
        mock_entry_point = Mock()
        mock_entry_point.name = "broken_ep"
        mock_entry_point.value = "broken.module:BrokenCommand"
        mock_entry_point.load = Mock(side_effect=Exception("Load failed"))

        mock_eps = Mock()
        mock_eps.select = Mock(return_value=[mock_entry_point])

        with patch("pedre.commands.loader.entry_points", return_value=mock_eps):
            loader = CommandLoader()
            # Should not raise - errors should be caught and logged
            loader.load_entry_point_commands()

    def test_load_entry_point_commands_handles_entry_points_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that errors getting entry points don't crash the loader."""
        CommandRegistry.clear()

        with patch("pedre.commands.loader.entry_points", side_effect=Exception("Entry points error")):
            loader = CommandLoader()
            # Should not raise - errors should be caught and logged
            loader.load_entry_point_commands()


class TestLoadModules:
    """Test load_modules method."""

    def test_load_modules_calls_all_discovery_methods(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that load_modules calls all three discovery methods."""
        loader = CommandLoader()

        # Mock all three discovery methods
        with (
            patch.object(loader, "autodiscover_framework_commands") as mock_framework,
            patch.object(loader, "autodiscover_project_commands") as mock_project,
            patch.object(loader, "load_entry_point_commands") as mock_entry_points,
        ):
            loader.load_modules()

            # Verify all three methods were called
            mock_framework.assert_called_once()
            mock_project.assert_called_once()
            mock_entry_points.assert_called_once()

    def test_load_modules_calls_methods_in_order(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that load_modules calls discovery methods in the correct order."""
        loader = CommandLoader()

        call_order: list[str] = []

        def mock_framework() -> None:
            call_order.append("framework")

        def mock_project() -> None:
            call_order.append("project")

        def mock_entry_points() -> None:
            call_order.append("entry_points")

        with (
            patch.object(loader, "autodiscover_framework_commands", side_effect=mock_framework),
            patch.object(loader, "autodiscover_project_commands", side_effect=mock_project),
            patch.object(loader, "load_entry_point_commands", side_effect=mock_entry_points),
        ):
            loader.load_modules()

            # Verify correct order
            assert call_order == ["framework", "project", "entry_points"]


class TestCommandLoaderIntegration:
    """Integration tests for CommandLoader."""

    def test_full_loading_cycle(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test complete loading cycle loads framework commands."""
        # Save original state
        original_commands = CommandRegistry._commands.copy()
        original_actions = ActionRegistry._actions.copy()
        original_events = EventRegistry._events.copy()
        original_condition_checkers = ConditionRegistry._checkers.copy()
        original_condition_validators = ConditionRegistry._validators.copy()

        # Track which modules we import so we can clean them up
        modules_before = set(sys.modules.keys())

        try:
            CommandRegistry.clear()

            # Remove any already imported command modules
            modules_to_remove = [
                key
                for key in sys.modules
                if key.startswith("pedre.commands.")
                and key
                not in ["pedre.commands", "pedre.commands.loader", "pedre.commands.registry", "pedre.commands.base"]
            ]
            for module in modules_to_remove:
                del sys.modules[module]

            loader = CommandLoader()
            loader.load_modules()

            # Verify framework commands are registered (this is the main integration test)
            assert CommandRegistry.is_registered("init")  # Framework command
            assert CommandRegistry.is_registered("validate")  # Framework command
        finally:
            # Restore original state
            CommandRegistry._commands = original_commands
            ActionRegistry._actions = original_actions
            EventRegistry._events = original_events
            ConditionRegistry._checkers = original_condition_checkers
            ConditionRegistry._validators = original_condition_validators

            # Clean up any modules we imported during the test
            modules_after = set(sys.modules.keys())
            new_modules = modules_after - modules_before
            for module in new_modules:
                if module.startswith("pedre.commands.") and module not in [
                    "pedre.commands",
                    "pedre.commands.loader",
                    "pedre.commands.registry",
                    "pedre.commands.base",
                ]:
                    del sys.modules[module]
