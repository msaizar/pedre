"""Tests for dialog validator."""

import json
from pathlib import Path as PathlibPath
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

import pytest

from pedre.actions.base import Action
from pedre.actions.registry import ActionRegistry
from pedre.conditions.registry import ConditionRegistry
from pedre.validators.dialog_validator import DialogValidator

if TYPE_CHECKING:
    from pathlib import Path


class TestDialogValidator:
    """Test dialog validator."""

    @pytest.fixture(autouse=True)
    def _clear_registries(self) -> object:
        """Clear all registries before and after each test to ensure isolation."""
        # Save original state
        original_actions = ActionRegistry._actions.copy()
        original_condition_checkers = ConditionRegistry._checkers.copy()
        original_condition_validators = ConditionRegistry._validators.copy()

        # Clear for test
        ActionRegistry.clear()
        ConditionRegistry.clear()

        yield

        # Restore original state after test
        ActionRegistry._actions = original_actions
        ConditionRegistry._checkers = original_condition_checkers
        ConditionRegistry._validators = original_condition_validators

    @pytest.fixture
    def dialogs_dir(self, tmp_path: Path) -> Path:
        """Create a temporary dialogs directory."""
        dialogs_dir = tmp_path / "dialogs"
        dialogs_dir.mkdir(parents=True)
        return dialogs_dir

    @pytest.fixture
    def setup_registries(self) -> None:
        """Setup basic registries for tests."""

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

    def test_validator_name(self, dialogs_dir: Path) -> None:
        """Test validator name property."""
        validator = DialogValidator(dialogs_dir)
        assert validator.name == "Dialogs"

    def test_directory_not_found(self, tmp_path: Path) -> None:
        """Test validate when directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"
        validator = DialogValidator(nonexistent_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert f"Dialogs directory not found: {nonexistent_dir}" in result.errors
        assert result.item_count == 0
        assert result.metadata == {}

    def test_no_dialog_files(self, dialogs_dir: Path) -> None:
        """Test validate when no dialog files found."""
        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 0
        assert result.metadata == {}

    def test_valid_dialogs_plural_filename(self, dialogs_dir: Path) -> None:
        """Test validate with valid dialog file (*_dialogs.json)."""
        dialog_data = {
            "merchant": {
                "0": {
                    "text": ["Hello, traveler!"],
                }
            }
        }

        dialog_file = dialogs_dir / "npc_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 1
        assert result.metadata == {"Total Conditions": 0, "Total Actions": 0}

    def test_valid_dialogs_singular_filename(self, dialogs_dir: Path) -> None:
        """Test validate with valid dialog file (*_dialog.json)."""
        dialog_data = {
            "merchant": {
                "0": {
                    "text": ["Hello, traveler!"],
                }
            }
        }

        dialog_file = dialogs_dir / "npc_dialog.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 1
        assert result.metadata == {"Total Conditions": 0, "Total Actions": 0}

    def test_root_not_dict(self, dialogs_dir: Path) -> None:
        """Test validate when root is not a dictionary."""
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text("[]")

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "root must be a dictionary" in result.errors[0]
        assert result.item_count == 0

    def test_npc_dialogs_not_dict(self, dialogs_dir: Path) -> None:
        """Test validate when NPC dialogs is not a dictionary."""
        dialog_data = {"merchant": "not a dict"}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "NPC 'merchant' dialogs must be a dictionary" in result.errors[0]

    def test_dialog_data_not_dict(self, dialogs_dir: Path) -> None:
        """Test validate when dialog data is not a dictionary."""
        dialog_data = {"merchant": {"0": "not a dict"}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Dialog 'merchant' level 0: dialog data must be a dictionary" in result.errors[0]

    def test_missing_text_field(self, dialogs_dir: Path) -> None:
        """Test validate when text field is missing."""
        dialog_data = {"merchant": {"0": {"name": "Merchant"}}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Dialog 'merchant' level 0: missing required 'text' field" in result.errors[0]
        assert result.item_count == 1

    def test_text_not_list(self, dialogs_dir: Path) -> None:
        """Test validate when text is not a list."""
        dialog_data = {"merchant": {"0": {"text": "not a list"}}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Dialog 'merchant' level 0: 'text' must be a list" in result.errors[0]

    def test_text_empty_list(self, dialogs_dir: Path) -> None:
        """Test validate when text list is empty."""
        dialog_data = {"merchant": {"0": {"text": []}}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Dialog 'merchant' level 0: 'text' list cannot be empty" in result.errors[0]

    def test_text_item_not_string(self, dialogs_dir: Path) -> None:
        """Test validate when text item is not a string."""
        dialog_data = {"merchant": {"0": {"text": ["Hello", 123, "World"]}}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Dialog 'merchant' level 0: 'text[1]' must be a string, got int" in result.errors[0]

    def test_name_not_string(self, dialogs_dir: Path) -> None:
        """Test validate when name is not a string."""
        dialog_data = {"merchant": {"0": {"text": ["Hello"], "name": 123}}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Dialog 'merchant' level 0: 'name' must be a string, got int" in result.errors[0]

    def test_conditions_not_list(self, dialogs_dir: Path) -> None:
        """Test validate when conditions is not a list."""
        dialog_data = {"merchant": {"0": {"text": ["Hello"], "conditions": "not a list"}}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Dialog 'merchant' level 0: 'conditions' must be a list" in result.errors[0]

    def test_condition_not_dict(self, dialogs_dir: Path) -> None:
        """Test validate when condition is not a dictionary."""
        dialog_data = {"merchant": {"0": {"text": ["Hello"], "conditions": ["not a dict"]}}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Dialog 'merchant' level 0: condition 0 must be a dictionary" in result.errors[0]

    def test_condition_missing_check(self, dialogs_dir: Path) -> None:
        """Test validate when condition is missing check key."""
        dialog_data = {"merchant": {"0": {"text": ["Hello"], "conditions": [{"param": "value"}]}}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Dialog 'merchant' level 0: condition 0 missing required 'check' key" in result.errors[0]

    def test_condition_unknown_type(self, dialogs_dir: Path, setup_registries: None) -> None:
        """Test validate when condition has unknown type."""
        dialog_data = {"merchant": {"0": {"text": ["Hello"], "conditions": [{"check": "unknown_condition"}]}}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "condition 0 has unknown type 'unknown_condition'" in result.errors[0]

    def test_condition_validation_error(self, dialogs_dir: Path) -> None:
        """Test validate when condition parameter validation fails."""

        @ConditionRegistry.register("test_condition", validator=lambda data: ["parameter error"])
        def test_condition(data: dict, context: object) -> bool:
            return True

        dialog_data = {"merchant": {"0": {"text": ["Hello"], "conditions": [{"check": "test_condition"}]}}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Dialog 'merchant' level 0: condition 0 (test_condition): parameter error" in result.errors[0]

    def test_on_condition_fail_not_list(self, dialogs_dir: Path) -> None:
        """Test validate when on_condition_fail is not a list."""
        dialog_data = {"merchant": {"0": {"text": ["Hello"], "on_condition_fail": "not a list"}}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Dialog 'merchant' level 0: 'on_condition_fail' must be a list" in result.errors[0]

    def test_on_condition_fail_action_not_dict(self, dialogs_dir: Path) -> None:
        """Test validate when on_condition_fail action is not a dictionary."""
        dialog_data = {"merchant": {"0": {"text": ["Hello"], "on_condition_fail": ["not a dict"]}}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Dialog 'merchant' level 0: on_condition_fail action 0 must be a dictionary" in result.errors[0]

    def test_on_condition_fail_action_missing_type(self, dialogs_dir: Path) -> None:
        """Test validate when on_condition_fail action is missing type key."""
        dialog_data = {"merchant": {"0": {"text": ["Hello"], "on_condition_fail": [{"param": "value"}]}}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Dialog 'merchant' level 0: on_condition_fail action 0 missing required 'type' key" in result.errors[0]

    def test_on_condition_fail_action_unknown_type(self, dialogs_dir: Path, setup_registries: None) -> None:
        """Test validate when on_condition_fail action has unknown type."""
        dialog_data = {"merchant": {"0": {"text": ["Hello"], "on_condition_fail": [{"type": "unknown_action"}]}}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "on_condition_fail action 0 has unknown type 'unknown_action'" in result.errors[0]

    def test_on_condition_fail_action_validation_error(self, dialogs_dir: Path) -> None:
        """Test validate when on_condition_fail action parameter validation fails."""

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

        dialog_data = {"merchant": {"0": {"text": ["Hello"], "on_condition_fail": [{"type": "test_action"}]}}}

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert (
            "Dialog 'merchant' level 0: on_condition_fail action 0 (test_action): parameter error" in result.errors[0]
        )

    def test_unknown_keys(self, dialogs_dir: Path) -> None:
        """Test validate when dialog has unknown keys."""
        dialog_data = {
            "merchant": {
                "0": {
                    "text": ["Hello"],
                    "unknown_key": "value",
                    "another_bad_key": 123,
                }
            }
        }

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Dialog 'merchant' level 0: unknown keys" in result.errors[0]
        assert "'another_bad_key'" in result.errors[0]
        assert "'unknown_key'" in result.errors[0]

    def test_json_decode_error(self, dialogs_dir: Path) -> None:
        """Test validate with JSON decode error."""
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text("invalid json {")

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Failed to parse test_dialogs.json" in result.errors[0]

    def test_os_error(self, dialogs_dir: Path) -> None:
        """Test validate with OS error when opening file."""
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text("{}")

        original_open = PathlibPath.open
        error_msg = "Permission denied"

        def mock_path_open(self: PathlibPath, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            if self.name == "test_dialogs.json":
                raise OSError(error_msg)
            return original_open(self, *args, **kwargs)

        with patch.object(PathlibPath, "open", mock_path_open):
            validator = DialogValidator(dialogs_dir)
            result = validator.validate()

            assert len(result.errors) == 1
            assert "Failed to load test_dialogs.json" in result.errors[0]

    def test_valid_complex_dialog(self, dialogs_dir: Path, setup_registries: None) -> None:
        """Test validate with complex valid dialog."""
        dialog_data = {
            "merchant": {
                "0": {
                    "name": "Merchant",
                    "text": ["Hello, traveler!", "Would you like to buy something?"],
                    "conditions": [{"check": "test_condition", "param": "value"}],
                    "on_condition_fail": [{"type": "test_action", "param": "value"}],
                },
                "1": {
                    "text": ["Thank you for your business!"],
                },
            },
            "guard": {
                "0": {
                    "text": ["Halt!"],
                }
            },
        }

        dialog_file = dialogs_dir / "npc_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 3
        assert result.metadata == {"Total Conditions": 1, "Total Actions": 1}

    def test_multiple_dialog_files(self, dialogs_dir: Path) -> None:
        """Test validate with multiple dialog files."""
        dialog_data1 = {"merchant": {"0": {"text": ["Hello"]}}}
        dialog_data2 = {"guard": {"0": {"text": ["Halt"]}}}

        dialog_file1 = dialogs_dir / "merchants_dialogs.json"
        dialog_file1.write_text(json.dumps(dialog_data1))

        dialog_file2 = dialogs_dir / "guards_dialog.json"
        dialog_file2.write_text(json.dumps(dialog_data2))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 2
        assert result.metadata == {"Total Conditions": 0, "Total Actions": 0}

    def test_integer_level_keys(self, dialogs_dir: Path) -> None:
        """Test validate with integer level keys."""
        dialog_data = {
            "merchant": {
                0: {"text": ["Hello"]},  # Integer key (will be converted to string by JSON)
                1: {"text": ["Goodbye"]},
            }
        }

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 2

    def test_metadata_counts(self, dialogs_dir: Path, setup_registries: None) -> None:
        """Test that metadata correctly counts conditions and actions."""
        dialog_data = {
            "npc1": {
                "0": {
                    "text": ["Hello"],
                    "conditions": [
                        {"check": "test_condition"},
                        {"check": "test_condition"},
                    ],
                    "on_condition_fail": [
                        {"type": "test_action"},
                    ],
                },
                "1": {
                    "text": ["Goodbye"],
                    "on_condition_fail": [
                        {"type": "test_action"},
                        {"type": "test_action"},
                    ],
                },
            },
            "npc2": {
                "0": {
                    "text": ["Hi"],
                    "conditions": [{"check": "test_condition"}],
                }
            },
        }

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 3
        assert result.metadata["Total Conditions"] == 3
        assert result.metadata["Total Actions"] == 3

    def test_multiple_errors_in_single_dialog(self, dialogs_dir: Path) -> None:
        """Test that multiple errors in a single dialog are all reported."""
        dialog_data = {
            "merchant": {
                "0": {
                    # Missing text field
                    "name": 123,  # Invalid name type
                    "conditions": "not a list",  # Invalid conditions type
                    "on_condition_fail": "not a list",  # Invalid on_condition_fail type
                    "unknown_key": "value",  # Unknown key
                }
            }
        }

        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(dialog_data))

        validator = DialogValidator(dialogs_dir)
        result = validator.validate()

        # Should have multiple errors
        assert len(result.errors) == 5
        error_text = " ".join(result.errors)
        assert "missing required 'text' field" in error_text
        assert "'name' must be a string" in error_text
        assert "'conditions' must be a list" in error_text
        assert "'on_condition_fail' must be a list" in error_text
        assert "unknown keys" in error_text
