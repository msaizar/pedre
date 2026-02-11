"""Tests for validate command."""

import argparse
import json
from pathlib import Path as PathlibPath
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest

from pedre.actions.base import Action
from pedre.actions.registry import ActionRegistry
from pedre.commands.validate import ValidateCommand
from pedre.conditions.registry import ConditionRegistry
from pedre.events.registry import EventRegistry
from pedre.plugins.script.base import ScriptValidationError

if TYPE_CHECKING:
    from pathlib import Path


class TestValidateCommand:
    """Test validate command."""

    @pytest.fixture(autouse=True)
    def _clear_registries(self) -> object:
        """Clear all registries before and after each test to ensure isolation."""
        # Save original state
        original_actions = ActionRegistry._actions.copy()
        original_events = EventRegistry._events.copy()
        original_condition_checkers = ConditionRegistry._checkers.copy()
        original_condition_validators = ConditionRegistry._validators.copy()

        # Clear for test
        ActionRegistry.clear()
        EventRegistry.clear()
        ConditionRegistry.clear()

        yield

        # Restore original state after test
        ActionRegistry._actions = original_actions
        EventRegistry._events = original_events
        ConditionRegistry._checkers = original_condition_checkers
        ConditionRegistry._validators = original_condition_validators

    @pytest.fixture
    def scripts_dir(self, tmp_path: Path) -> Path:
        """Create a temporary scripts directory."""
        scripts_dir = tmp_path / "assets" / "data" / "scripts"
        scripts_dir.mkdir(parents=True)
        return scripts_dir

    @pytest.fixture
    def setup_registries(self) -> None:
        """Setup basic registries for tests."""

        # Register a simple event
        @EventRegistry.register("valid_event")
        class ValidEvent:
            pass

        # Register a simple action
        @ActionRegistry.register("test_action")
        class TestAction(Action):
            def __init__(self, **kwargs: object) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict) -> TestAction:
                return cls(**data)

            @staticmethod
            def validate_params(data: dict) -> list[str]:
                return []

        # Register a simple condition
        @ConditionRegistry.register("test_condition", validator=lambda data: [])
        def test_condition(data: dict, context: object) -> bool:
            return True

    def test_validate_scripts_directory_not_found(self, tmp_path: Path) -> None:
        """Test validate command when scripts directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"

        command = ValidateCommand()
        args = argparse.Namespace(path=nonexistent_dir)
        with pytest.raises(SystemExit) as exc_info:
            command.execute(args)

        assert exc_info.value.code == 1

    def test_validate_scripts_no_script_files(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate command when no script files found."""
        command = ValidateCommand()
        args = argparse.Namespace(path=scripts_dir)
        with pytest.raises(SystemExit) as exc_info:
            command.execute(args)

        assert exc_info.value.code == 0

    def test_validate_scripts_unknown_keys(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate command with unknown keys in script definition."""
        script_data = {
            "test_script": {
                "trigger": {"event": "valid_event"},
                "actions": [{"type": "test_action"}],
                "unknown_key": "value",
                "another_bad_key": 123,
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        args = argparse.Namespace(path=scripts_dir)
        with pytest.raises(SystemExit) as exc_info:
            command.execute(args)

        assert exc_info.value.code == 1

    def test_validate_scripts_json_decode_error(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate command with JSON decode error."""
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text("invalid json {")

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(argparse.Namespace(path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_scripts_os_error(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate command with OS error when opening file."""
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text("{}")

        command = ValidateCommand()

        # Mock Path.open to raise OSError (works cross-platform)
        original_open = PathlibPath.open
        error_msg = "Permission denied"

        def mock_path_open(self: PathlibPath, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            # Check if opening the test script file
            if self.name == "test_scripts.json":
                raise OSError(error_msg)
            return original_open(self, *args, **kwargs)

        with patch.object(PathlibPath, "open", mock_path_open):
            with pytest.raises(SystemExit) as exc_info:
                command.execute(argparse.Namespace(path=scripts_dir))

            assert exc_info.value.code == 1

    def test_validate_scripts_trigger_without_event(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate command with trigger missing event key."""
        script_data = {
            "test_script": {
                "trigger": {"filter": "value"},
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(argparse.Namespace(path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_scripts_with_invalid_event(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate command with invalid event triggers."""
        script_data = {
            "test_script": {
                "trigger": {"event": "unknown_event"},
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(argparse.Namespace(path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_scripts_trigger_valid_filter_keys(self, scripts_dir: Path) -> None:
        """Test validate command with valid trigger filter keys."""

        # Register event with trigger keys
        @EventRegistry.register("valid_event")
        class ValidEvent:
            trigger_keys = frozenset({"valid_key"})

        @ActionRegistry.register("test_action")
        class TestAction(Action):
            def __init__(self, **kwargs: object) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict) -> TestAction:
                return cls(**data)

            @staticmethod
            def validate_params(data: dict) -> list[str]:
                return []

        script_data = {
            "test_script": {
                "trigger": {"event": "valid_event", "valid_key": "value"},
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        # Should succeed - valid filter keys
        command.execute(argparse.Namespace(path=scripts_dir))

    def test_validate_scripts_trigger_invalid_filter_keys(self, scripts_dir: Path) -> None:
        """Test validate command with invalid trigger filter keys."""

        # Register event with trigger keys
        @EventRegistry.register("valid_event")
        class ValidEvent:
            trigger_keys = frozenset({"valid_key"})

        @ActionRegistry.register("test_action")
        class TestAction(Action):
            def __init__(self, **kwargs: object) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict) -> TestAction:
                return cls(**data)

            @staticmethod
            def validate_params(data: dict) -> list[str]:
                return []

        script_data = {
            "test_script": {
                "trigger": {"event": "valid_event", "invalid_filter": "value", "another_bad": 123},
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(argparse.Namespace(path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_scripts_condition_missing_check(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate command with condition missing check key."""
        script_data = {
            "test_script": {
                "conditions": [{"param": "value"}],
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(argparse.Namespace(path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_scripts_condition_unknown_type(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate command with unknown condition type."""
        script_data = {
            "test_script": {
                "conditions": [{"check": "unknown_condition"}],
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(argparse.Namespace(path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_scripts_condition_validation_errors(self, scripts_dir: Path) -> None:
        """Test validate command with condition parameter validation errors."""

        @ActionRegistry.register("test_action")
        class TestAction(Action):
            def __init__(self, **kwargs: object) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict) -> TestAction:
                return cls(**data)

            @staticmethod
            def validate_params(data: dict) -> list[str]:
                return []

        # Validator that returns an error
        @ConditionRegistry.register("test_condition", validator=lambda data: ["parameter error"])
        def test_condition(data: dict, context: object) -> bool:
            return True

        script_data = {
            "test_script": {
                "conditions": [{"check": "test_condition", "param": "bad_value"}],
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(argparse.Namespace(path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_scripts_empty_actions(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate command with empty actions list."""
        script_data = {
            "test_script": {
                "trigger": {"event": "valid_event"},
                "actions": [],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(argparse.Namespace(path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_scripts_action_missing_type(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate command with action missing type key."""
        script_data = {
            "test_script": {
                "actions": [{"param": "value"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(argparse.Namespace(path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_scripts_action_unknown_type(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate command with unknown action type."""
        script_data = {
            "test_script": {
                "actions": [{"type": "unknown_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(argparse.Namespace(path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_scripts_action_validation_errors(self, scripts_dir: Path) -> None:
        """Test validate command with action parameter validation errors."""

        @ActionRegistry.register("test_action")
        class TestAction(Action):
            def __init__(self, **kwargs: object) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict) -> TestAction:
                return cls(**data)

            @staticmethod
            def validate_params(data: dict) -> list[str]:
                return ["parameter error"]

        script_data = {
            "test_script": {
                "actions": [{"type": "test_action", "param": "bad_value"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(argparse.Namespace(path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_scripts_on_condition_fail_missing_type(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate command with on_condition_fail action missing type."""
        script_data = {
            "test_script": {
                "actions": [{"type": "test_action"}],
                "on_condition_fail": [{"param": "value"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(argparse.Namespace(path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_scripts_on_condition_fail_unknown_type(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate command with on_condition_fail unknown action type."""
        script_data = {
            "test_script": {
                "actions": [{"type": "test_action"}],
                "on_condition_fail": [{"type": "unknown_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(argparse.Namespace(path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_scripts_on_condition_fail_validation_errors(self, scripts_dir: Path) -> None:
        """Test validate command with on_condition_fail action validation errors."""

        @ActionRegistry.register("test_action")
        class TestAction(Action):
            def __init__(self, **kwargs: object) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict) -> TestAction:
                return cls(**data)

            @staticmethod
            def validate_params(action: dict) -> list[str]:
                if action.get("param") == "bad_value":
                    return ["parameter error"]
                return []

        script_data = {
            "test_script": {
                "actions": [{"type": "test_action"}],
                "on_condition_fail": [{"type": "test_action", "param": "bad_value"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        with pytest.raises(SystemExit) as exc_info:
            command.execute(argparse.Namespace(path=scripts_dir))

        assert exc_info.value.code == 1

    def test_validate_scripts_success(self, scripts_dir: Path) -> None:
        """Test validate command with all valid scripts."""

        # Register event with no trigger keys
        @EventRegistry.register("valid_event")
        class ValidEvent:
            pass

        @ActionRegistry.register("test_action")
        class TestAction(Action):
            def __init__(self, **_kwargs: object) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict) -> TestAction:
                return cls(**data)

            @staticmethod
            def validate_params(data: dict) -> list[str]:
                return []

        @ConditionRegistry.register("test_condition", validator=lambda _data: [])
        def test_condition(data: dict, context: object) -> bool:
            return True

        script_data = {
            "script1": {
                "trigger": {"event": "valid_event"},
                "conditions": [{"check": "test_condition"}],
                "actions": [{"type": "test_action"}],
            },
            "script2": {
                "actions": [{"type": "test_action"}],
            },
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        command = ValidateCommand()
        # Should not raise, completes successfully
        command.execute(argparse.Namespace(path=scripts_dir))

    def test_validate_scripts_script_validation_error(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate command with ScriptValidationError exception."""
        command = ValidateCommand()
        args = argparse.Namespace(path=scripts_dir)

        # Create a valid script file
        script_data = {"test_script": {"actions": [{"type": "test_action"}]}}
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        # Mock Path.glob to raise ScriptValidationError (covers lines 282-290)
        # This simulates a ScriptValidationError during the validation process
        error = ScriptValidationError(["Test validation error"])

        with patch("pedre.commands.validate.Path.glob", side_effect=error):
            with pytest.raises(SystemExit) as exc_info:
                command.execute(args)

            assert exc_info.value.code == 1

    def test_add_arguments_without_path(self) -> None:
        """Test add_arguments method adds path argument with default None."""
        command = ValidateCommand()
        parser = argparse.ArgumentParser()

        # Add arguments (covers line 39 default=None)
        command.add_arguments(parser)

        # Parse with no arguments - should use default
        args = parser.parse_args([])
        assert args.path is None

    def test_add_arguments_with_path(self, tmp_path: Path) -> None:
        """Test add_arguments method accepts path argument."""
        command = ValidateCommand()
        parser = argparse.ArgumentParser()

        command.add_arguments(parser)

        # Parse with path argument
        test_path = tmp_path / "test"
        args = parser.parse_args(["--path", str(test_path)])
        assert args.path == test_path
