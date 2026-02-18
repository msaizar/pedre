"""Tests for validate command.

These tests focus on command-specific logic:
- Argument parsing and defaults
- Integration of multiple validators
- Error aggregation and display
- Success/failure exit codes

For validator-specific tests, see:
- tests/validators/test_script_validator.py
- tests/validators/test_dialog_validator.py
"""

import argparse
import json
from typing import TYPE_CHECKING, Any, ClassVar

import pytest

import pedre.commands.validate as validate_module
from pedre.actions.base import Action
from pedre.actions.registry import ActionRegistry
from pedre.commands.validate import ValidateCommand
from pedre.conditions.base import Condition
from pedre.conditions.registry import ConditionRegistry
from pedre.events.base import Event
from pedre.events.registry import EventRegistry

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch

    from pedre.game import GameContext


@pytest.fixture(autouse=True)
def mock_setup_resources(monkeypatch: MonkeyPatch) -> None:
    """Mock setup_resources."""
    monkeypatch.setattr(validate_module, "setup_resources", lambda *a, **k: None)


class TestValidateCommand:
    """Test validate command."""

    @pytest.fixture(autouse=True)
    def _clear_registries(self) -> object:
        """Clear all registries before and after each test to ensure isolation."""
        # Save original state
        original_actions = ActionRegistry._actions.copy()
        original_events = EventRegistry._events.copy()
        original_conditions = ConditionRegistry._conditions.copy()

        # Clear for test
        ActionRegistry.clear()
        EventRegistry.clear()
        ConditionRegistry.clear()

        yield

        # Restore original state after test
        ActionRegistry._actions = original_actions
        EventRegistry._events = original_events
        ConditionRegistry._conditions = original_conditions

    @pytest.fixture
    def scripts_dir(self, tmp_path: Path) -> Path:
        """Create a temporary scripts directory."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(parents=True)
        return scripts_dir

    @pytest.fixture
    def dialogs_dir(self, tmp_path: Path) -> Path:
        """Create a temporary dialogs directory."""
        dialogs_dir = tmp_path / "dialogs"
        dialogs_dir.mkdir(parents=True)
        return dialogs_dir

    @pytest.fixture
    def maps_dir(self, tmp_path: Path) -> Path:
        """Create a temporary maps directory."""
        maps_dir = tmp_path / "maps"
        maps_dir.mkdir(parents=True)
        return maps_dir

    @pytest.fixture
    def inventory_items_file(self, tmp_path: Path) -> Path:
        """Create a temporary inventory_items.json file with no items."""
        items_file = tmp_path / "inventory_items.json"
        items_file.write_text(json.dumps({"items": []}))
        return items_file

    @pytest.fixture
    def setup_registries(self) -> None:
        """Setup basic registries for tests."""

        # Register a simple event
        @EventRegistry.register
        class TestEvent(Event):
            name: ClassVar[str] = "test_event"

        # Register a simple action
        @ActionRegistry.register
        class TestAction(Action):
            name = "test_action"

            def __init__(self, **kwargs: dict[str, Any]) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TestAction:
                return cls(**data)

            def execute(self, context: GameContext) -> bool:
                return True

            def reset(self) -> None:
                return

        # Register a simple condition
        @ConditionRegistry.register
        class TestCondition(Condition):
            name = "test_condition"

            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TestCondition:
                return cls()

    # Argument Parsing Tests

    def test_add_arguments_defaults(self) -> None:
        """Test that add_arguments sets correct defaults."""
        command = ValidateCommand()
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)

        args = parser.parse_args([])
        assert args.scripts_path is None
        assert args.type == "all"
        assert args.dialogs_path is None

    def test_add_arguments_with_path(self, tmp_path: Path) -> None:
        """Test add_arguments accepts custom path."""
        command = ValidateCommand()
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)

        test_path = tmp_path / "custom"
        args = parser.parse_args(["--scripts-path", str(test_path)])
        assert args.scripts_path == test_path

    def test_add_arguments_with_type(self) -> None:
        """Test add_arguments accepts validation type."""
        command = ValidateCommand()
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)

        args = parser.parse_args(["--type", "scripts"])
        assert args.type == "scripts"

        args = parser.parse_args(["--type", "dialogs"])
        assert args.type == "dialogs"

        args = parser.parse_args(["--type", "all"])
        assert args.type == "all"

    def test_add_arguments_with_dialogs_dir(self, tmp_path: Path) -> None:
        """Test add_arguments accepts custom dialogs directory."""
        command = ValidateCommand()
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)

        dialogs_path = tmp_path / "custom_dialogs"
        args = parser.parse_args(["--dialogs-path", str(dialogs_path)])
        assert args.dialogs_path == dialogs_path

    # Validator Selection Tests

    def test_validate_type_scripts_only(self, scripts_dir: Path, setup_registries: None, maps_dir: Path) -> None:
        """Test --type scripts validates only scripts."""
        script_data = {
            "test_script": {
                "actions": [{"name": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        args = argparse.Namespace(
            scripts_path=scripts_dir,
            type="scripts",
            dialogs_path=None,
            maps_path=maps_dir,
        )
        command.execute(args)

    def test_validate_type_dialogs_only(self, dialogs_dir: Path, maps_dir: Path, setup_registries: None) -> None:
        """Test --type dialogs validates only dialogs."""
        # Create a map file with the merchant NPC to satisfy cross-reference validation
        # Create a simple TMX file
        tmx_content = """<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.1" orientation="orthogonal" renderorder="right-down" width="10" height="10" \
    tilewidth="32" tileheight="32" infinite="0" nextlayerid="2" nextobjectid="2">
  <objectgroup id="1" name="NPCs">
    <object id="1" name="merchant" x="100" y="100" width="32" height="32">
      <properties>
        <property name="sprite_sheet" value="merchant.png"/>
      </properties>
    </object>
  </objectgroup>
</map>"""
        map_file = maps_dir / "npc.tmx"
        map_file.write_text(tmx_content)

        dialog_data = {
            "merchant": {
                "0": {
                    "text": ["Hello, traveler!"],
                }
            }
        }

        dialog_file = dialogs_dir / "npc_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        command = ValidateCommand()
        args = argparse.Namespace(scripts_path=None, type="dialogs", dialogs_path=dialogs_dir, maps_path=maps_dir)
        command.execute(args)

    def test_validate_type_all_with_both(
        self, scripts_dir: Path, dialogs_dir: Path, maps_dir: Path, inventory_items_file: Path, setup_registries: None
    ) -> None:
        """Test --type all validates both scripts and dialogs."""
        # Create a map file with the merchant NPC
        tmx_content = """<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.1" orientation="orthogonal" renderorder="right-down" width="10" height="10" \
    tilewidth="32" tileheight="32" infinite="0" nextlayerid="2" nextobjectid="2">
  <objectgroup id="1" name="NPCs">
    <object id="1" name="merchant" x="100" y="100" width="32" height="32">
      <properties>
        <property name="sprite_sheet" value="merchant.png"/>
      </properties>
    </object>
  </objectgroup>
</map>"""
        map_file = maps_dir / "npc.tmx"
        map_file.write_text(tmx_content)

        script_data = {
            "test_script": {
                "actions": [{"name": "test_action"}],
            }
        }
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        dialog_data = {
            "merchant": {
                "0": {
                    "text": ["Hello, traveler!"],
                }
            }
        }
        dialog_file = dialogs_dir / "npc_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        command = ValidateCommand()
        args = argparse.Namespace(
            scripts_path=scripts_dir,
            type="all",
            dialogs_path=dialogs_dir,
            maps_path=maps_dir,
            inventory_items_path=inventory_items_file,
        )
        command.execute(args)

    def test_validate_with_custom_dialogs_dir(
        self, scripts_dir: Path, tmp_path: Path, maps_dir: Path, inventory_items_file: Path, setup_registries: None
    ) -> None:
        """Test validate uses custom dialogs directory when provided."""
        dialogs_dir = tmp_path / "custom_dialogs"
        dialogs_dir.mkdir(parents=True)

        # Create a map file with the merchant NPC
        tmx_content = """<?xml version="1.0" encoding="UTF-8"?>
<map version="1.10" tiledversion="1.10.1" orientation="orthogonal" renderorder="right-down" width="10" height="10" \
    tilewidth="32" tileheight="32" infinite="0" nextlayerid="2" nextobjectid="2">
  <objectgroup id="1" name="NPCs">
    <object id="1" name="merchant" x="100" y="100" width="32" height="32">
      <properties>
        <property name="sprite_sheet" value="merchant.png"/>
      </properties>
    </object>
  </objectgroup>
</map>"""
        map_file = maps_dir / "npc.tmx"
        map_file.write_text(tmx_content)

        dialog_data = {
            "merchant": {
                "0": {
                    "text": ["Hello!"],
                }
            }
        }
        dialog_file = dialogs_dir / "npc_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        command = ValidateCommand()
        args = argparse.Namespace(
            scripts_path=scripts_dir,
            type="all",
            dialogs_path=dialogs_dir,
            maps_path=maps_dir,
            inventory_items_path=inventory_items_file,
        )
        command.execute(args)

    # Error Handling Tests

    def test_validate_scripts_directory_not_found(self, tmp_path: Path) -> None:
        """Test validate exits with error when scripts directory not found."""
        nonexistent_dir = tmp_path / "nonexistent"

        command = ValidateCommand()
        args = argparse.Namespace(scripts_path=nonexistent_dir, type="scripts", dialogs_path=None)
        with pytest.raises(SystemExit) as exc_info:
            command.execute(args)

        assert exc_info.value.code == 1

    def test_validate_dialogs_directory_not_found(self, tmp_path: Path) -> None:
        """Test validate exits with error when dialogs directory not found."""
        nonexistent_dir = tmp_path / "nonexistent"

        command = ValidateCommand()
        args = argparse.Namespace(scripts_path=None, type="dialogs", dialogs_path=nonexistent_dir)
        with pytest.raises(SystemExit) as exc_info:
            command.execute(args)

        assert exc_info.value.code == 1

    def test_validate_with_validation_errors_exits(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate exits with error code when validation fails."""
        # Create invalid script (empty actions)
        script_data = {"test_script": {"actions": []}}
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        args = argparse.Namespace(scripts_path=scripts_dir, type="scripts", dialogs_path=None)
        with pytest.raises(SystemExit) as exc_info:
            command.execute(args)

        assert exc_info.value.code == 1

    def test_validate_no_errors_succeeds(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate completes successfully when no errors."""
        script_data = {
            "test_script": {
                "actions": [{"name": "test_action"}],
            }
        }
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        args = argparse.Namespace(scripts_path=scripts_dir, type="scripts", dialogs_path=None)
        # Should not raise
        command.execute(args)

    def test_validate_empty_directories_succeeds(
        self,
        scripts_dir: Path,
        dialogs_dir: Path,
        maps_dir: Path,
        inventory_items_file: Path,
        setup_registries: None,
    ) -> None:
        """Test validate succeeds with empty directories (no files to validate)."""
        command = ValidateCommand()
        args = argparse.Namespace(
            scripts_path=scripts_dir,
            type="all",
            dialogs_path=dialogs_dir,
            maps_path=maps_dir,
            inventory_items_path=inventory_items_file,
        )
        # Should not raise
        command.execute(args)

    # Error Aggregation Tests

    def test_validate_aggregates_errors_from_multiple_validators(
        self, scripts_dir: Path, dialogs_dir: Path, setup_registries: None
    ) -> None:
        """Test that errors from both validators are aggregated."""
        # Invalid script
        script_data = {"test_script": {"actions": []}}
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        # Invalid dialog
        dialog_data = {"merchant": {"0": {}}}  # Missing text field
        dialog_file = dialogs_dir / "npc_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        command = ValidateCommand()
        args = argparse.Namespace(
            scripts_path=scripts_dir, type="all", dialogs_path=dialogs_dir, maps_path=None, inventory_items_path=None
        )
        with pytest.raises(SystemExit) as exc_info:
            command.execute(args)

        # Should exit with error - both validators found issues
        assert exc_info.value.code == 1

    def test_validate_aggregates_errors_from_multiple_files(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test that errors from multiple files are aggregated."""
        # First invalid script file
        script_data1 = {"script1": {"actions": []}}
        script_file1 = scripts_dir / "game_scripts.json"
        script_file1.write_text(json.dumps(script_data1))

        # Second invalid script file
        script_data2 = {"script2": {"actions": []}}
        script_file2 = scripts_dir / "npc_scripts.json"
        script_file2.write_text(json.dumps(script_data2))

        command = ValidateCommand()
        args = argparse.Namespace(scripts_path=scripts_dir, type="scripts", dialogs_path=None)
        with pytest.raises(SystemExit) as exc_info:
            command.execute(args)

        # Should exit with error - multiple files with errors
        assert exc_info.value.code == 1
