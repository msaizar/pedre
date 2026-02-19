"""Tests for DialogValidator."""

import json
from typing import TYPE_CHECKING, Any

import pytest

from pedre.actions.base import Action
from pedre.actions.registry import ActionRegistry
from pedre.conditions.base import Condition
from pedre.conditions.registry import ConditionRegistry
from pedre.types import EntityReference
from pedre.validators.context import ValidationContext
from pedre.validators.dialog_validator import DialogValidator

if TYPE_CHECKING:
    from pathlib import Path

    from pedre.game import GameContext


class TestDialogValidator:
    """Test DialogValidator class."""

    @pytest.fixture(autouse=True)
    def _clear_registries(self) -> object:
        """Clear all registries before and after each test to ensure isolation."""
        # Save original state
        original_actions = ActionRegistry._actions.copy()
        original_conditions = ConditionRegistry._conditions.copy()

        # Clear for test
        ActionRegistry.clear()
        ConditionRegistry.clear()

        yield

        # Restore original state after test
        ActionRegistry._actions = original_actions
        ConditionRegistry._conditions = original_conditions

    @pytest.fixture
    def context(self) -> ValidationContext:
        """Create a validation context for tests."""
        return ValidationContext()

    @pytest.fixture
    def dialogs_dir(self, tmp_path: Path) -> Path:
        """Create a temporary dialogs directory."""
        dialogs_dir = tmp_path / "dialogs"
        dialogs_dir.mkdir(parents=True)
        return dialogs_dir

    @pytest.fixture
    def setup_basic_registries(self) -> None:
        """Setup basic registries for tests."""

        @ActionRegistry.register
        class TestAction(Action):
            name = "test_action"

            def __init__(self, **kwargs: dict[str, Any]) -> None:
                self.kwargs = kwargs

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TestAction:
                return cls(**data)

            def execute(self, context: GameContext) -> bool:
                return True

            def reset(self) -> None:
                return

            def get_references(self) -> set[EntityReference]:
                return set()

        @ConditionRegistry.register
        class TestCondition(Condition):
            name = "test_condition"

            def check(self, context: object) -> bool:
                return True

            @classmethod
            def from_dict(cls, data: dict[str, Any]) -> TestCondition:
                return cls()

            def get_references(self) -> set[EntityReference]:
                return set()

    def test_name_property(self, dialogs_dir: Path, context: ValidationContext) -> None:
        """Test validator name."""
        validator = DialogValidator(dialogs_dir, context)
        assert validator.name == "Dialogs"

    def test_validate_directory_not_found(self, tmp_path: Path, context: ValidationContext) -> None:
        """Test error when dialogs directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"
        validator = DialogValidator(nonexistent_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert f"Dialogs directory not found: {nonexistent_dir}" in result.errors
        assert result.item_count == 0

    def test_validate_no_dialog_files(self, dialogs_dir: Path, context: ValidationContext) -> None:
        """Test validation with no dialog files."""
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 0

    def test_validate_invalid_json(
        self, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error on invalid JSON."""
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text("not valid json{")
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert any("Failed to parse" in e for e in result.errors)

    def test_validate_os_error(
        self, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error handling when OSError occurs while reading file."""
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps({"npc1": {"1": {"text": ["Hello"]}}}))
        dialog_file.chmod(0o000)

        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        dialog_file.chmod(0o644)
        assert any("Failed to load" in e for e in result.errors)

    def test_validate_root_not_dict(self, dialogs_dir: Path, context: ValidationContext) -> None:
        """Test error when root is not a dictionary."""
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps([{"npc": "data"}]))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert any("root must be a dictionary" in e for e in result.errors)

    def test_validate_npc_dialogs_not_dict(self, dialogs_dir: Path, context: ValidationContext) -> None:
        """Test error when NPC dialogs are not a dictionary."""
        data = {"npc1": "not_a_dict"}
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(data))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert any("NPC 'npc1' dialogs must be a dictionary" in e for e in result.errors)

    def test_validate_dialog_data_not_dict(self, dialogs_dir: Path, context: ValidationContext) -> None:
        """Test error when dialog data is not a dictionary."""
        data = {"npc1": {"1": "not_a_dict"}}
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(data))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert any("dialog data must be a dictionary" in e for e in result.errors)

    def test_validate_text_missing_or_empty(self, dialogs_dir: Path, context: ValidationContext) -> None:
        """Test error when text is missing or empty."""
        data1 = {"npc1": {"1": {"text": []}}}
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(data1))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert any("'text' must be a non-empty list" in e for e in result.errors)

    def test_validate_text_not_list(self, dialogs_dir: Path, context: ValidationContext) -> None:
        """Test error when text is not a list."""
        data = {"npc1": {"1": {"text": "not_a_list"}}}
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(data))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert any("'text' must be a non-empty list" in e for e in result.errors)

    def test_validate_text_item_not_string(self, dialogs_dir: Path, context: ValidationContext) -> None:
        """Test error when text item is not a string."""
        data = {"npc1": {"1": {"text": ["Hello", 123, "World"]}}}
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(data))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert any("text[1] must be string" in e for e in result.errors)

    def test_validate_name_not_string(self, dialogs_dir: Path, context: ValidationContext) -> None:
        """Test error when name is not a string or null."""
        data = {"npc1": {"1": {"text": ["Hello"], "name": 123}}}
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(data))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert any("'name' must be string or null" in e for e in result.errors)

    def test_validate_conditions_not_list(
        self, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error when conditions is not a list."""
        data = {"npc1": {"1": {"text": ["Hello"], "conditions": "not_a_list"}}}
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(data))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert any("'conditions' must be a list" in e for e in result.errors)

    def test_validate_condition_parse_error(
        self, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error when condition fails to parse."""
        data = {"npc1": {"1": {"text": ["Hello"], "conditions": [{"name": "nonexistent_condition"}]}}}
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(data))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert any("condition 0:" in e for e in result.errors)

    def test_validate_on_condition_fail_not_list(
        self, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error when on_condition_fail is not a list."""
        data = {"npc1": {"1": {"text": ["Hello"], "on_condition_fail": "not_a_list"}}}
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(data))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert any("'on_condition_fail' must be a list" in e for e in result.errors)

    def test_validate_on_condition_fail_parse_error(
        self, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error when on_condition_fail action fails to parse."""
        data = {"npc1": {"1": {"text": ["Hello"], "on_condition_fail": [{"name": "nonexistent_action"}]}}}
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(data))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert any("on_condition_fail action 0:" in e for e in result.errors)

    def test_validate_valid_dialog(
        self, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test validation of a valid dialog."""
        data = {
            "npc1": {
                "1": {
                    "text": ["Hello, traveler!"],
                    "name": "Friendly NPC",
                    "conditions": [{"name": "test_condition"}],
                    "on_condition_fail": [{"name": "test_action"}],
                }
            }
        }
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(data))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 1
        assert result.metadata["Total Conditions"] == 1
        assert result.metadata["Total Actions"] == 1

    def test_validate_dialog_with_null_name(
        self, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test validation of dialog with null name (should be valid)."""
        data = {"npc1": {"1": {"text": ["Hello"], "name": None}}}
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(data))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 1

    def test_validate_dialog_without_name(
        self, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test validation of dialog without name field (should be valid)."""
        data = {"npc1": {"1": {"text": ["Hello"]}}}
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(data))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 1

    def test_validate_dialog_references_stored(
        self, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test that dialog references are stored in context."""
        data = {"npc1": {"1": {"text": ["Hello"]}}}
        dialog_file = dialogs_dir / "test_scene_dialogs.json"
        dialog_file.write_text(json.dumps(data))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert ("test_scene", "npc1", "1") in context.dialog_references
        # Check that scene and NPC references are stored
        refs = context.dialog_references[("test_scene", "npc1", "1")]
        assert EntityReference(type="map", name="test_scene") in refs
        assert EntityReference(type="npc", name="npc1") in refs

    def test_validate_dialog_file_suffix_variations(
        self, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test that both *_dialogs.json and *_dialog.json suffixes work."""
        data1 = {"npc1": {"1": {"text": ["Hello"]}}}
        data2 = {"npc2": {"1": {"text": ["Hi"]}}}

        dialog_file1 = dialogs_dir / "scene1_dialogs.json"
        dialog_file1.write_text(json.dumps(data1))

        dialog_file2 = dialogs_dir / "scene2_dialog.json"
        dialog_file2.write_text(json.dumps(data2))

        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 2
        assert ("scene1", "npc1", "1") in context.dialog_references
        assert ("scene2", "npc2", "1") in context.dialog_references

    def test_validate_multiple_dialogs_and_npcs(
        self, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test validation of multiple dialogs for multiple NPCs."""
        data = {
            "npc1": {
                "1": {"text": ["Hello"]},
                "2": {"text": ["How are you?"]},
            },
            "npc2": {
                "1": {"text": ["Greetings"]},
            },
        }
        dialog_file = dialogs_dir / "test_dialogs.json"
        dialog_file.write_text(json.dumps(data))
        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 3

    def test_validate_cross_references_npc_not_found(self, dialogs_dir: Path, context: ValidationContext) -> None:
        """Test cross-reference validation when NPC is not found in map."""
        context.dialog_references[("test_scene", "missing_npc", "1")] = {
            EntityReference(type="map", name="test_scene"),
            EntityReference(type="npc", name="missing_npc"),
        }
        # Register the map but not the NPC
        context.add_map_entity("test_scene", "npcs", "other_npc")

        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate_cross_references()

        assert any("NPC 'missing_npc'" in e and "not found in map" in e for e in result.errors)

    def test_validate_cross_references_inventory_item_not_found(
        self, dialogs_dir: Path, context: ValidationContext
    ) -> None:
        """Test cross-reference validation when inventory item is not found."""
        context.dialog_references[("test_scene", "npc1", "1")] = {
            EntityReference(type="inventory_item", name="missing_item")
        }

        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate_cross_references()

        assert any("inventory item 'missing_item' not found" in e for e in result.errors)

    def test_validate_cross_references_valid(self, dialogs_dir: Path, context: ValidationContext) -> None:
        """Test successful cross-reference validation."""
        context.dialog_references[("test_scene", "npc1", "1")] = {
            EntityReference(type="map", name="test_scene"),
            EntityReference(type="npc", name="npc1"),
            EntityReference(type="inventory_item", name="test_item"),
        }
        # Register the entities
        context.add_map_entity("test_scene", "npcs", "npc1")
        context.add_inventory_item("test_item")

        validator = DialogValidator(dialogs_dir, context)
        result = validator.validate_cross_references()

        assert result.errors == []
        assert result.item_count == 1
        assert result.metadata["Dialog entries validated"] == 1
