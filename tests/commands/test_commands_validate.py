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
        original_actions = ActionRegistry._actions.copy()
        original_events = EventRegistry._events.copy()
        original_conditions = ConditionRegistry._conditions.copy()

        ActionRegistry.clear()
        EventRegistry.clear()
        ConditionRegistry.clear()

        yield

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
    def items_file(self, tmp_path: Path) -> Path:
        """Create a temporary items.json file."""
        items_file = tmp_path / "items.json"
        items_file.write_text(json.dumps({}))
        return items_file

    @pytest.fixture
    def setup_registries(self) -> None:
        """Setup basic registries for tests."""

        @EventRegistry.register
        class TestEvent(Event):
            name: ClassVar[str] = "test_event"

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

        @ConditionRegistry.register
        class TestCondition(Condition):
            name = "test_condition"

            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TestCondition:
                return cls()

    def _make_args(self, **kwargs: object) -> argparse.Namespace:
        """Create a Namespace with all expected path arguments defaulting to None."""
        defaults = {
            "scripts_path": None,
            "dialogs_path": None,
            "maps_path": None,
            "items_path": None,
            "sprites_path": None,
            "npcs_path": None,
        }
        defaults.update(kwargs)
        return argparse.Namespace(**defaults)

    # Argument Parsing Tests

    def test_add_arguments_defaults(self) -> None:
        """Test that add_arguments sets correct defaults."""
        command = ValidateCommand()
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)

        args = parser.parse_args([])
        assert args.scripts_path is None
        assert args.dialogs_path is None
        assert args.maps_path is None

    def test_add_arguments_with_scripts_path(self, tmp_path: Path) -> None:
        """Test add_arguments accepts custom scripts path."""
        command = ValidateCommand()
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)

        test_path = tmp_path / "custom"
        args = parser.parse_args(["--scripts-path", str(test_path)])
        assert args.scripts_path == test_path

    def test_add_arguments_with_dialogs_dir(self, tmp_path: Path) -> None:
        """Test add_arguments accepts custom dialogs directory."""
        command = ValidateCommand()
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)

        dialogs_path = tmp_path / "custom_dialogs"
        args = parser.parse_args(["--dialogs-path", str(dialogs_path)])
        assert args.dialogs_path == dialogs_path

    # Validation Tests

    def test_validate_scripts_and_dialogs(
        self,
        scripts_dir: Path,
        dialogs_dir: Path,
        maps_dir: Path,
        items_file: Path,
        setup_registries: None,
    ) -> None:
        """Test validation runs all validators successfully."""
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
        (maps_dir / "npc.tmx").write_text(tmx_content)

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps({"test_script": {"actions": [{"name": "test_action"}]}}))

        dialog_file = dialogs_dir / "npc_dialogs.json"
        dialog_file.write_text(json.dumps({"merchant": {"0": {"text": ["Hello, traveler!"]}}}))

        command = ValidateCommand()
        command.execute(
            self._make_args(
                scripts_path=scripts_dir,
                dialogs_path=dialogs_dir,
                maps_path=maps_dir,
                items_path=items_file,
            )
        )

    def test_validate_empty_directories_succeeds(
        self,
        scripts_dir: Path,
        dialogs_dir: Path,
        maps_dir: Path,
        items_file: Path,
        setup_registries: None,
    ) -> None:
        """Test validate succeeds with empty directories (no files to validate)."""
        command = ValidateCommand()
        command.execute(
            self._make_args(
                scripts_path=scripts_dir,
                dialogs_path=dialogs_dir,
                maps_path=maps_dir,
                items_path=items_file,
            )
        )

    def test_validate_with_custom_dialogs_dir(
        self, scripts_dir: Path, tmp_path: Path, maps_dir: Path, items_file: Path, setup_registries: None
    ) -> None:
        """Test validate uses custom dialogs directory when provided."""
        dialogs_dir = tmp_path / "custom_dialogs"
        dialogs_dir.mkdir(parents=True)

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
        (maps_dir / "npc.tmx").write_text(tmx_content)
        (dialogs_dir / "npc_dialogs.json").write_text(json.dumps({"merchant": {"0": {"text": ["Hello!"]}}}))

        command = ValidateCommand()
        command.execute(
            self._make_args(
                scripts_path=scripts_dir,
                dialogs_path=dialogs_dir,
                maps_path=maps_dir,
                items_path=items_file,
            )
        )

    # Error Handling Tests

    def test_validate_scripts_directory_not_found(self, tmp_path: Path) -> None:
        """Test validate exits with error when scripts directory not found."""
        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(self._make_args(scripts_path=tmp_path / "nonexistent"))

        assert exc_info.value.code == 1

    def test_validate_dialogs_directory_not_found(self, tmp_path: Path) -> None:
        """Test validate exits with error when dialogs directory not found."""
        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(self._make_args(dialogs_path=tmp_path / "nonexistent"))

        assert exc_info.value.code == 1

    def test_validate_with_validation_errors_exits(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate exits with error code when validation fails."""
        (scripts_dir / "test_scripts.json").write_text(json.dumps({"test_script": {"actions": []}}))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(self._make_args(scripts_path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_no_errors_succeeds(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate completes successfully when no errors."""
        (scripts_dir / "test_scripts.json").write_text(
            json.dumps({"test_script": {"actions": [{"name": "test_action"}]}})
        )

        command = ValidateCommand()
        command.execute(self._make_args(scripts_path=scripts_dir))

    # Error Aggregation Tests

    def test_validate_aggregates_errors_from_multiple_validators(
        self, scripts_dir: Path, dialogs_dir: Path, setup_registries: None
    ) -> None:
        """Test that errors from both validators are aggregated."""
        (scripts_dir / "test_scripts.json").write_text(json.dumps({"test_script": {"actions": []}}))
        (dialogs_dir / "npc_dialogs.json").write_text(json.dumps({"merchant": {"0": {}}}))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(self._make_args(scripts_path=scripts_dir, dialogs_path=dialogs_dir))

        assert exc_info.value.code == 1

    def test_validate_aggregates_errors_from_multiple_files(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test that errors from multiple files are aggregated."""
        (scripts_dir / "game_scripts.json").write_text(json.dumps({"script1": {"actions": []}}))
        (scripts_dir / "npc_scripts.json").write_text(json.dumps({"script2": {"actions": []}}))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(self._make_args(scripts_path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_cross_reference_errors(self, dialogs_dir: Path, maps_dir: Path) -> None:
        """Test that cross-reference validation errors are detected and aggregated."""
        (dialogs_dir / "npc_dialogs.json").write_text(
            json.dumps({"nonexistent_npc": {"0": {"text": ["Hello, traveler!"]}}})
        )

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(self._make_args(dialogs_path=dialogs_dir, maps_path=maps_dir))

        assert exc_info.value.code == 1

    def test_validate_with_explicit_sprites_and_npcs_paths(self, tmp_path: Path) -> None:
        """Test validate includes sprites and npcs validators when paths are explicitly provided."""
        sprites_file = tmp_path / "sprites.json"
        sprites_file.write_text(json.dumps({}))
        npcs_file = tmp_path / "npcs.json"
        npcs_file.write_text(json.dumps({}))

        command = ValidateCommand()
        # Should not raise — explicit paths trigger the validators even if files are otherwise absent
        command.execute(self._make_args(sprites_path=sprites_file, npcs_path=npcs_file))
