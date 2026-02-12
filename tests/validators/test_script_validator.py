"""Tests for script validator."""

import json
from pathlib import Path
from pathlib import Path as PathlibPath
from typing import Any
from unittest.mock import patch

import pytest

from pedre.actions.base import Action
from pedre.actions.registry import ActionRegistry
from pedre.conditions.base import Condition
from pedre.conditions.registry import ConditionRegistry
from pedre.events.registry import EventRegistry
from pedre.validators.context import ValidationContext
from pedre.validators.script_validator import ScriptValidator


class TestScriptValidator:
    """Test script validator."""

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
    def context(self) -> ValidationContext:
        """Create a validation context for tests."""
        return ValidationContext()

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
        @ConditionRegistry.register("test_condition")
        class TestCondition(Condition):
            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict) -> TestCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict) -> list[str]:
                return []

    def test_validator_name(self, scripts_dir: Path, context: ValidationContext) -> None:
        """Test validator name property."""
        validator = ScriptValidator(scripts_dir, context)
        assert validator.name == "Scripts"

    def test_directory_not_found(self, tmp_path: Path, context: ValidationContext) -> None:
        """Test validate when directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"
        validator = ScriptValidator(nonexistent_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert f"Scripts directory not found: {nonexistent_dir}" in result.errors
        assert result.item_count == 0
        assert result.metadata == {}

    def test_no_script_files(self, scripts_dir: Path, context: ValidationContext) -> None:
        """Test validate when no script files found."""
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 0
        assert result.metadata == {}

    def test_valid_script_minimal(self, scripts_dir: Path, setup_registries: None, context: ValidationContext) -> None:
        """Test validate with minimal valid script."""
        script_data = {
            "test_script": {
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 1
        assert result.metadata == {
            "Total Actions": 1,
            "Total Conditions": 0,
            "Scripts with Triggers": 0,
        }

    def test_valid_script_complete(self, scripts_dir: Path, setup_registries: None, context: ValidationContext) -> None:
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

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 1
        assert result.metadata == {
            "Total Actions": 1,
            "Total Conditions": 1,
            "Scripts with Triggers": 1,
        }

    def test_unknown_keys(self, scripts_dir: Path, setup_registries: None, context: ValidationContext) -> None:
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

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': unknown keys" in result.errors[0]
        assert "'another_bad_key'" in result.errors[0]
        assert "'unknown_key'" in result.errors[0]

    def test_json_decode_error(self, scripts_dir: Path, context: ValidationContext) -> None:
        """Test validate with JSON decode error."""
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text("invalid json {")

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Failed to parse test_scripts.json" in result.errors[0]

    def test_os_error(self, scripts_dir: Path, context: ValidationContext) -> None:
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
            validator = ScriptValidator(scripts_dir, context)
            result = validator.validate()

            assert len(result.errors) == 1
            assert "Failed to load test_scripts.json" in result.errors[0]

    def test_trigger_missing_event(self, scripts_dir: Path, setup_registries: None, context: ValidationContext) -> None:
        """Test validate with trigger missing event key."""
        script_data = {
            "test_script": {
                "trigger": {"filter": "value"},
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': trigger missing required 'event' key" in result.errors[0]

    def test_trigger_unknown_event(self, scripts_dir: Path, setup_registries: None, context: ValidationContext) -> None:
        """Test validate with unknown event in trigger."""
        script_data = {
            "test_script": {
                "trigger": {"event": "unknown_event"},
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': unknown event 'unknown_event'" in result.errors[0]

    def test_trigger_valid_filter_keys(self, scripts_dir: Path, context: ValidationContext) -> None:
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

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert result.errors == []

    def test_trigger_invalid_filter_keys(self, scripts_dir: Path, context: ValidationContext) -> None:
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

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': trigger has unknown filter keys" in result.errors[0]
        assert "'another_bad'" in result.errors[0]
        assert "'invalid_filter'" in result.errors[0]

    def test_condition_missing_check(
        self, scripts_dir: Path, setup_registries: None, context: ValidationContext
    ) -> None:
        """Test validate with condition missing check key."""
        script_data = {
            "test_script": {
                "conditions": [{"param": "value"}],
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': condition 0 missing required 'check' key" in result.errors[0]

    def test_condition_unknown_type(
        self, scripts_dir: Path, setup_registries: None, context: ValidationContext
    ) -> None:
        """Test validate with unknown condition type."""
        script_data = {
            "test_script": {
                "conditions": [{"check": "unknown_condition"}],
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': unknown condition 'unknown_condition'" in result.errors[0]

    def test_condition_validation_error(self, scripts_dir: Path, context: ValidationContext) -> None:
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

        @ConditionRegistry.register("test_condition")
        class TestCondition(Condition):
            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict) -> TestCondition:
                return cls()

            @staticmethod
            def validate_params(data: dict[str, Any]) -> list[str]:
                return ["parameter error"]

        script_data = {
            "test_script": {
                "conditions": [{"check": "test_condition", "param": "bad_value"}],
                "actions": [{"type": "test_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': condition 0 (test_condition): parameter error" in result.errors[0]

    def test_empty_actions(self, scripts_dir: Path, setup_registries: None, context: ValidationContext) -> None:
        """Test validate with empty actions list."""
        script_data = {
            "test_script": {
                "trigger": {"event": "test_event"},
                "actions": [],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': 'actions' list is empty" in result.errors[0]

    def test_action_missing_type(self, scripts_dir: Path, setup_registries: None, context: ValidationContext) -> None:
        """Test validate with action missing type key."""
        script_data = {
            "test_script": {
                "actions": [{"param": "value"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': action 0 missing required 'type' key" in result.errors[0]

    def test_action_unknown_type(self, scripts_dir: Path, setup_registries: None, context: ValidationContext) -> None:
        """Test validate with unknown action type."""
        script_data = {
            "test_script": {
                "actions": [{"type": "unknown_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': unknown action type 'unknown_action'" in result.errors[0]

    def test_action_validation_error(self, scripts_dir: Path, context: ValidationContext) -> None:
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

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': action 0 (test_action): parameter error" in result.errors[0]

    def test_on_condition_fail_missing_type(
        self, scripts_dir: Path, setup_registries: None, context: ValidationContext
    ) -> None:
        """Test validate with on_condition_fail action missing type."""
        script_data = {
            "test_script": {
                "actions": [{"type": "test_action"}],
                "on_condition_fail": [{"param": "value"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': on_condition_fail action 0 missing required 'type' key" in result.errors[0]

    def test_on_condition_fail_unknown_type(
        self, scripts_dir: Path, setup_registries: None, context: ValidationContext
    ) -> None:
        """Test validate with on_condition_fail unknown action type."""
        script_data = {
            "test_script": {
                "actions": [{"type": "test_action"}],
                "on_condition_fail": [{"type": "unknown_action"}],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': on_condition_fail action 0 has unknown type 'unknown_action'" in result.errors[0]

    def test_on_condition_fail_validation_error(self, scripts_dir: Path, context: ValidationContext) -> None:
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

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Script 'test_script': on_condition_fail action 0 (test_action): parameter error" in result.errors[0]

    def test_multiple_scripts(self, scripts_dir: Path, setup_registries: None, context: ValidationContext) -> None:
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

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 2
        assert result.metadata["Total Actions"] == 3
        assert result.metadata["Total Conditions"] == 1
        assert result.metadata["Scripts with Triggers"] == 1

    def test_multiple_script_files(self, scripts_dir: Path, setup_registries: None, context: ValidationContext) -> None:
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

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 2

    def test_metadata_counts(self, scripts_dir: Path, setup_registries: None, context: ValidationContext) -> None:
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

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 3
        assert result.metadata["Total Actions"] == 5
        assert result.metadata["Total Conditions"] == 3
        assert result.metadata["Scripts with Triggers"] == 2

    def test_multiple_errors_in_single_script(
        self, scripts_dir: Path, setup_registries: None, context: ValidationContext
    ) -> None:
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

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert len(result.errors) == 4
        error_text = " ".join(result.errors)
        assert "unknown keys" in error_text
        assert "trigger missing required 'event' key" in error_text
        assert "condition 0 missing required 'check' key" in error_text

    def test_script_references_population(self, scripts_dir: Path, context: ValidationContext) -> None:  # noqa: C901
        """Test that script references (NPCs, waypoints) are correctly populated from actions."""

        # Register dummy actions so validation passes
        @ActionRegistry.register("move_npc")
        class MoveNpcAction(Action):
            def __init__(self, **kwargs: object) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict) -> MoveNpcAction:
                return cls(**data)

            @staticmethod
            def validate_params(data: dict) -> list[str]:
                return []

        @ActionRegistry.register("change_scene")
        class ChangeSceneAction(Action):
            def __init__(self, **kwargs: object) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict) -> ChangeSceneAction:
                return cls(**data)

            @staticmethod
            def validate_params(data: dict) -> list[str]:
                return []

        @ActionRegistry.register("start_appear_animation")
        class StartAppearAnimationAction(Action):
            def __init__(self, **kwargs: object) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict) -> StartAppearAnimationAction:
                return cls(**data)

            @staticmethod
            def validate_params(data: dict) -> list[str]:
                return []

        @ActionRegistry.register("advance_dialog")
        class AdvanceDialogAction(Action):
            def __init__(self, **kwargs: object) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict) -> AdvanceDialogAction:
                return cls(**data)

            @staticmethod
            def validate_params(data: dict) -> list[str]:
                return []

        script_data = {
            "test_script": {
                "actions": [
                    {
                        "type": "move_npc",
                        "npcs": ["guard1", "guard2"],
                        "waypoint": "guard_post",
                    },
                    {
                        "type": "change_scene",
                        "spawn_waypoint": "entry_point",
                    },
                    {
                        "type": "start_appear_animation",
                        "npcs": ["merchant"],
                    },
                    {
                        "type": "advance_dialog",
                        "npc": "elder",
                    },
                ],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert result.errors == []

        # Verify references were captured
        refs = context.script_references.get("test_script", {})
        assert "guard1" in refs.get("npcs", set())
        assert "guard2" in refs.get("npcs", set())
        assert "merchant" in refs.get("npcs", set())
        assert "elder" in refs.get("npcs", set())

    def test_script_references_missing_keys(self, scripts_dir: Path, context: ValidationContext) -> None:
        """Test script references population with missing optional keys (branch coverage)."""

        # Register dummy actions
        @ActionRegistry.register("move_npc")
        class MoveNpcAction(Action):
            def __init__(self, **kwargs: object) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict) -> MoveNpcAction:
                return cls(**data)

            @staticmethod
            def validate_params(data: dict) -> list[str]:
                return []

        @ActionRegistry.register("change_scene")
        class ChangeSceneAction(Action):
            def __init__(self, **kwargs: object) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict) -> ChangeSceneAction:
                return cls(**data)

            @staticmethod
            def validate_params(data: dict) -> list[str]:
                return []

        @ActionRegistry.register("start_appear_animation")
        class StartAppearAnimationAction(Action):
            def __init__(self, **kwargs: object) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict) -> StartAppearAnimationAction:
                return cls(**data)

            @staticmethod
            def validate_params(data: dict) -> list[str]:
                return []

        script_data = {
            "test_script": {
                "actions": [
                    {
                        "type": "move_npc",
                        # Missing npcs key
                    },
                    {
                        "type": "change_scene",
                        # Missing spawn_waypoint
                    },
                    {
                        "type": "start_appear_animation",
                        # Missing npcs
                    },
                ],
            }
        }

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert result.errors == []

        # Verify no references captured
        refs = context.script_references.get("test_script", {})
        assert len(refs.get("npcs", set())) == 0

    def test_script_references_portal_key_variations(self, scripts_dir: Path, context: ValidationContext) -> None:
        """Test script references captures portal names from both 'portal_name' and 'portal' keys."""
        script_data = {
            "script1": {
                "trigger": {
                    "event": "portal_entered",
                    "portal_name": "portal1",
                },
                "actions": [{"type": "test_action"}],
            },
            "script2": {
                "trigger": {
                    "event": "portal_entered",
                    "portal": "portal2",
                },
                "actions": [{"type": "test_action"}],
            },
        }

        # Need to register test_action
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

        # Need to register portal_entered event
        @EventRegistry.register("portal_entered")
        class PortalEnteredEvent:
            pass

        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(script_data))

        validator = ScriptValidator(scripts_dir, context)
        validator.validate()

        refs1 = context.script_references.get("script1", {})
        assert "portal1" in refs1.get("portals", set())

        refs2 = context.script_references.get("script2", {})
        assert "portal2" in refs2.get("portals", set())
