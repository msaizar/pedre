"""Tests for script validator."""

import json
from pathlib import Path
from pathlib import Path as PathlibPath
from typing import Any
from unittest.mock import patch

import pytest

from pedre.actions.base import Action
from pedre.actions.registry import ActionRegistry
from pedre.conditions.registry import ConditionRegistry
from pedre.events.registry import EventRegistry
from pedre.validators.script_validator import ScriptValidator


class TestScriptValidator:
    """Test script validator."""

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
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(parents=True)
        return scripts_dir

    @pytest.fixture
    def setup_registries(self) -> None:
        """Setup basic registries for tests."""

        # Register a simple event
        @EventRegistry.register("test_event")
        class TestEvent:
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

    def test_validator_name(self, scripts_dir: Path) -> None:
        """Test validator name property."""
        validator = ScriptValidator(scripts_dir)
        assert validator.name == "Scripts"

    def test_directory_not_found(self, tmp_path: Path) -> None:
        """Test validate when directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"
        validator = ScriptValidator(nonexistent_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert f"Scripts directory not found: {nonexistent_dir}" in result.errors
        assert result.item_count == 0
        assert result.metadata == {}

    def test_no_script_files(self, scripts_dir: Path) -> None:
        """Test validate when no script files found."""
        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 0
        assert result.metadata == {}

    def test_valid_script_minimal(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate with minimal valid script."""
        script_data = {
            "test_script": {
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 1
        assert result.metadata == {
            "Total Actions": 1,
            "Total Conditions": 0,
            "Scripts with Triggers": 0,
        }

    def test_valid_script_complete(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate with complete valid script."""
        script_data = {
            "test_script": {
                "trigger": {"event": "test_event"},
                "conditions": [{"check": "test_condition"}],
                "scene": "test_scene",
                "run_once": True,
                "actions": [{"type": "test_action"}],
                "on_condition_fail": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 1
        assert result.metadata == {
            "Total Actions": 1,
            "Total Conditions": 1,
            "Scripts with Triggers": 1,
        }

    def test_unknown_keys(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate with unknown keys in script definition."""
        script_data = {
            "test_script": {
                "actions": [{"type": "test_action"}],
                "unknown_key": "value",
                "another_bad_key": 123,
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': unknown keys" in result.errors[0]
        assert "'another_bad_key'" in result.errors[0]
        assert "'unknown_key'" in result.errors[0]

    def test_json_decode_error(self, scripts_dir: Path) -> None:
        """Test validate with JSON decode error."""
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text("invalid json {")

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Failed to parse test_scripts.json" in result.errors[0]

    def test_os_error(self, scripts_dir: Path) -> None:
        """Test validate with OS error when opening file."""
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text("{}")

        original_open = PathlibPath.open
        error_msg = "Permission denied"

        def mock_path_open(self: PathlibPath, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            if self.name == "test_scripts.json":
                raise OSError(error_msg)
            return original_open(self, *args, **kwargs)

        with patch.object(PathlibPath, "open", mock_path_open):
            validator = ScriptValidator(scripts_dir)
            result = validator.validate()

            assert len(result.errors) == 1
            assert "Failed to load test_scripts.json" in result.errors[0]

    def test_trigger_missing_event(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate with trigger missing event key."""
        script_data = {
            "test_script": {
                "trigger": {"filter": "value"},
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': trigger missing required 'event' key" in result.errors[0]

    def test_trigger_unknown_event(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate with unknown event in trigger."""
        script_data = {
            "test_script": {
                "trigger": {"event": "unknown_event"},
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': unknown event 'unknown_event'" in result.errors[0]

    def test_trigger_valid_filter_keys(self, scripts_dir: Path) -> None:
        """Test validate with valid trigger filter keys."""

        @EventRegistry.register("test_event")
        class TestEvent:
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
                "trigger": {"event": "test_event", "valid_key": "value"},
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert result.errors == []

    def test_trigger_invalid_filter_keys(self, scripts_dir: Path) -> None:
        """Test validate with invalid trigger filter keys."""

        @EventRegistry.register("test_event")
        class TestEvent:
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
                "trigger": {"event": "test_event", "invalid_filter": "value", "another_bad": 123},
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': trigger has unknown filter keys" in result.errors[0]
        assert "'another_bad'" in result.errors[0]
        assert "'invalid_filter'" in result.errors[0]

    def test_condition_missing_check(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate with condition missing check key."""
        script_data = {
            "test_script": {
                "conditions": [{"param": "value"}],
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': condition 0 missing required 'check' key" in result.errors[0]

    def test_condition_unknown_type(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate with unknown condition type."""
        script_data = {
            "test_script": {
                "conditions": [{"check": "unknown_condition"}],
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': unknown condition 'unknown_condition'" in result.errors[0]

    def test_condition_validation_error(self, scripts_dir: Path) -> None:
        """Test validate with condition parameter validation errors."""

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

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': condition 0 (test_condition): parameter error" in result.errors[0]

    def test_empty_actions(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate with empty actions list."""
        script_data = {
            "test_script": {
                "trigger": {"event": "test_event"},
                "actions": [],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': 'actions' list is empty" in result.errors[0]

    def test_action_missing_type(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate with action missing type key."""
        script_data = {
            "test_script": {
                "actions": [{"param": "value"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': action 0 missing required 'type' key" in result.errors[0]

    def test_action_unknown_type(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate with unknown action type."""
        script_data = {
            "test_script": {
                "actions": [{"type": "unknown_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': unknown action type 'unknown_action'" in result.errors[0]

    def test_action_validation_error(self, scripts_dir: Path) -> None:
        """Test validate with action parameter validation errors."""

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

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': action 0 (test_action): parameter error" in result.errors[0]

    def test_on_condition_fail_missing_type(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate with on_condition_fail action missing type."""
        script_data = {
            "test_script": {
                "actions": [{"type": "test_action"}],
                "on_condition_fail": [{"param": "value"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': on_condition_fail action 0 missing required 'type' key" in result.errors[0]

    def test_on_condition_fail_unknown_type(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate with on_condition_fail unknown action type."""
        script_data = {
            "test_script": {
                "actions": [{"type": "test_action"}],
                "on_condition_fail": [{"type": "unknown_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': on_condition_fail action 0 has unknown type 'unknown_action'" in result.errors[0]

    def test_on_condition_fail_validation_error(self, scripts_dir: Path) -> None:
        """Test validate with on_condition_fail action validation errors."""

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

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': on_condition_fail action 0 (test_action): parameter error" in result.errors[0]

    def test_multiple_scripts(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate with multiple scripts."""
        script_data = {
            "script1": {
                "trigger": {"event": "test_event"},
                "conditions": [{"check": "test_condition"}],
                "actions": [{"type": "test_action"}],
            },
            "script2": {
                "actions": [{"type": "test_action"}, {"type": "test_action"}],
            },
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 2
        assert result.metadata["Total Actions"] == 3
        assert result.metadata["Total Conditions"] == 1
        assert result.metadata["Scripts with Triggers"] == 1

    def test_multiple_script_files(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test validate with multiple script files."""
        script_data1 = {
            "script1": {
                "actions": [{"type": "test_action"}],
            }
        }
        script_data2 = {
            "script2": {
                "actions": [{"type": "test_action"}],
            }
        }

        script_file1 = scripts_dir / "game_scripts.json"
        script_file1.write_text(json.dumps(script_data1))

        script_file2 = scripts_dir / "npc_scripts.json"
        script_file2.write_text(json.dumps(script_data2))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 2

    def test_metadata_counts(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test that metadata correctly counts actions, conditions, and triggers."""
        script_data = {
            "script1": {
                "trigger": {"event": "test_event"},
                "conditions": [
                    {"check": "test_condition"},
                    {"check": "test_condition"},
                ],
                "actions": [
                    {"type": "test_action"},
                    {"type": "test_action"},
                    {"type": "test_action"},
                ],
            },
            "script2": {
                "trigger": {"event": "test_event"},
                "actions": [{"type": "test_action"}],
            },
            "script3": {
                "conditions": [{"check": "test_condition"}],
                "actions": [{"type": "test_action"}],
            },
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 3
        assert result.metadata["Total Actions"] == 5
        assert result.metadata["Total Conditions"] == 3
        assert result.metadata["Scripts with Triggers"] == 2

    def test_multiple_errors_in_single_script(self, scripts_dir: Path, setup_registries: None) -> None:
        """Test that multiple errors in a single script are all reported."""
        script_data = {
            "test_script": {
                "unknown_key": "value",  # Unknown key
                "trigger": {"filter": "value"},  # Missing event
                "conditions": [{"param": "value"}],  # Missing check
                "actions": [],  # Empty actions
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir)
        result = validator.validate()

        assert len(result.errors) == 4
        error_text = " ".join(result.errors)
        assert "unknown keys" in error_text
        assert "trigger missing required 'event' key" in error_text
        assert "condition 0 missing required 'check' key" in error_text
        assert "'actions' list is empty" in error_text
