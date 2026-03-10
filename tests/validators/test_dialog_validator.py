"""Tests for DialogValidator."""

import json
from typing import TYPE_CHECKING, Any
from unittest.mock import patch

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
    def content_dir(self, tmp_path: Path) -> Path:
        """Create a temporary content directory with a dialogs/ subdirectory."""
        content_dir = tmp_path / "content"
        (content_dir / "dialogs").mkdir(parents=True)
        return content_dir

    @pytest.fixture
    def dialogs_dir(self, content_dir: Path) -> Path:
        """Return the dialogs subdirectory (content/dialogs/)."""
        return content_dir / "dialogs"

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

    def test_name_property(self, content_dir: Path, context: ValidationContext) -> None:
        """Test validator name."""
        validator = DialogValidator(content_dir, context)
        assert validator.name == "Dialogs"

    def test_validate_directory_not_found(self, tmp_path: Path, context: ValidationContext) -> None:
        """Test error when content directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"
        validator = DialogValidator(nonexistent_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert f"Dialogs directory not found: {nonexistent_dir}" in result.errors
        assert result.item_count == 0

    def test_validate_no_dialog_files(self, content_dir: Path, context: ValidationContext) -> None:
        """Test validation with no dialog files."""
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 0

    def test_validate_invalid_json(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error on invalid JSON."""
        (dialogs_dir / "test.json").write_text("not valid json{")
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert any("Failed to parse" in e for e in result.errors)

    def test_validate_os_error(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error handling when OSError occurs while reading file."""
        (dialogs_dir / "test.json").write_text(json.dumps({"npc1/1": {"text": ["Hello"]}}))

        validator = DialogValidator(content_dir, context)

        # Mock Path.open to raise PermissionError (a subclass of OSError)
        with patch("pathlib.Path.open", side_effect=PermissionError("Permission denied")):
            result = validator.validate()

        assert any("Failed to load" in e for e in result.errors)

    def test_validate_root_not_dict(self, content_dir: Path, dialogs_dir: Path, context: ValidationContext) -> None:
        """Test error when root is not a dictionary."""
        (dialogs_dir / "test.json").write_text(json.dumps([{"npc": "data"}]))
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert any("root must be a dictionary" in e for e in result.errors)

    def test_validate_npc_dialogs_not_dict(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext
    ) -> None:
        """Test error when key has no slash (invalid composite key format)."""
        (dialogs_dir / "test.json").write_text(json.dumps({"npc1": "not_a_dict"}))
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert any("must be 'npc_name/level'" in e for e in result.errors)

    def test_validate_dialog_data_not_dict(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext
    ) -> None:
        """Test error when dialog data is not a dictionary."""
        (dialogs_dir / "test.json").write_text(json.dumps({"npc1/1": "not_a_dict"}))
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert any("dialog data must be a dictionary" in e for e in result.errors)

    def test_validate_text_missing_or_empty(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext
    ) -> None:
        """Test error when text is missing or empty."""
        (dialogs_dir / "test.json").write_text(json.dumps({"npc1/1": {"text": []}}))
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert any("'text' must be a non-empty list" in e for e in result.errors)

    def test_validate_text_not_list(self, content_dir: Path, dialogs_dir: Path, context: ValidationContext) -> None:
        """Test error when text is not a list."""
        (dialogs_dir / "test.json").write_text(json.dumps({"npc1/1": {"text": "not_a_list"}}))
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert any("'text' must be a non-empty list" in e for e in result.errors)

    def test_validate_text_item_not_string(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext
    ) -> None:
        """Test error when text item is not a string."""
        (dialogs_dir / "test.json").write_text(json.dumps({"npc1/1": {"text": ["Hello", 123, "World"]}}))
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert any("text[1] must be string" in e for e in result.errors)

    def test_validate_name_not_string(self, content_dir: Path, dialogs_dir: Path, context: ValidationContext) -> None:
        """Test error when name is not a string or null."""
        (dialogs_dir / "test.json").write_text(json.dumps({"npc1/1": {"text": ["Hello"], "name": 123}}))
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert any("'name' must be string or null" in e for e in result.errors)

    def test_validate_conditions_not_list(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error when conditions is not a list."""
        (dialogs_dir / "test.json").write_text(json.dumps({"npc1/1": {"text": ["Hello"], "conditions": "not_a_list"}}))
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert any("'conditions' must be a list" in e for e in result.errors)

    def test_validate_condition_parse_error(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error when condition fails to parse."""
        (dialogs_dir / "test.json").write_text(
            json.dumps({"npc1/1": {"text": ["Hello"], "conditions": [{"name": "nonexistent_condition"}]}})
        )
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert any("condition 0:" in e for e in result.errors)

    def test_validate_on_condition_fail_not_list(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error when on_condition_fail is not a list."""
        (dialogs_dir / "test.json").write_text(
            json.dumps({"npc1/1": {"text": ["Hello"], "on_condition_fail": "not_a_list"}})
        )
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert any("'on_condition_fail' must be a list" in e for e in result.errors)

    def test_validate_on_condition_fail_parse_error(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error when on_condition_fail action fails to parse."""
        (dialogs_dir / "test.json").write_text(
            json.dumps({"npc1/1": {"text": ["Hello"], "on_condition_fail": [{"name": "nonexistent_action"}]}})
        )
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert any("on_condition_fail action 0:" in e for e in result.errors)

    def test_validate_valid_dialog(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test validation of a valid dialog."""
        data = {
            "npc1/1": {
                "text": ["Hello, traveler!"],
                "name": "Friendly NPC",
                "conditions": [{"name": "test_condition"}],
                "on_condition_fail": [{"name": "test_action"}],
            }
        }
        (dialogs_dir / "test.json").write_text(json.dumps(data))
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 1
        assert result.metadata["Total Conditions"] == 1
        assert result.metadata["Total Actions"] == 1

    def test_validate_dialog_with_null_name(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test validation of dialog with null name (should be valid)."""
        (dialogs_dir / "test.json").write_text(json.dumps({"npc1/1": {"text": ["Hello"], "name": None}}))
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 1

    def test_validate_dialog_without_name(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test validation of dialog without name field (should be valid)."""
        (dialogs_dir / "test.json").write_text(json.dumps({"npc1/1": {"text": ["Hello"]}}))
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 1

    def test_validate_dialog_references_stored(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test that dialog references are stored in context."""
        (dialogs_dir / "test_scene.json").write_text(json.dumps({"npc1/1": {"text": ["Hello"]}}))
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert ("test_scene", "npc1", "1") in context.dialog_references
        refs = context.dialog_references[("test_scene", "npc1", "1")]
        assert EntityReference(type="map", name="test_scene") in refs
        assert EntityReference(type="npc", name="npc1") in refs

    def test_validate_multiple_scenes(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test that each file's stem becomes the scene name."""
        (dialogs_dir / "village.json").write_text(json.dumps({"npc1/1": {"text": ["Hello"]}}))
        (dialogs_dir / "forest.json").write_text(json.dumps({"npc2/1": {"text": ["Hi"]}}))

        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 2
        assert ("village", "npc1", "1") in context.dialog_references
        assert ("forest", "npc2", "1") in context.dialog_references

    def test_validate_multiple_dialogs_and_npcs(
        self, content_dir: Path, dialogs_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test validation of multiple dialogs for multiple NPCs."""
        data = {
            "npc1/1": {"text": ["Hello"]},
            "npc1/2": {"text": ["How are you?"]},
            "npc2/1": {"text": ["Greetings"]},
        }
        (dialogs_dir / "test.json").write_text(json.dumps(data))
        validator = DialogValidator(content_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 3

    def test_validate_cross_references_npc_not_found(self, content_dir: Path, context: ValidationContext) -> None:
        """Test cross-reference validation when NPC is not found in map."""
        context.dialog_references[("test_scene", "missing_npc", "1")] = {
            EntityReference(type="map", name="test_scene"),
            EntityReference(type="npc", name="missing_npc"),
        }
        # Register the map but not the NPC
        context.add_map_entity("test_scene", "npcs", "other_npc")

        validator = DialogValidator(content_dir, context)
        result = validator.validate_cross_references()

        assert any("NPC 'missing_npc'" in e and "not found in map" in e for e in result.errors)

    def test_validate_cross_references_inventory_item_not_found(
        self, content_dir: Path, context: ValidationContext
    ) -> None:
        """Test cross-reference validation when inventory item is not found."""
        context.dialog_references[("test_scene", "npc1", "1")] = {
            EntityReference(type="inventory_item", name="missing_item")
        }

        validator = DialogValidator(content_dir, context)
        result = validator.validate_cross_references()

        assert any("inventory item 'missing_item' not found" in e for e in result.errors)

    def test_validate_cross_references_valid(self, content_dir: Path, context: ValidationContext) -> None:
        """Test successful cross-reference validation."""
        context.dialog_references[("test_scene", "npc1", "1")] = {
            EntityReference(type="map", name="test_scene"),
            EntityReference(type="npc", name="npc1"),
            EntityReference(type="inventory_item", name="test_item"),
        }
        # Register the entities
        context.add_map_entity("test_scene", "npcs", "npc1")
        context.add_inventory_item("test_item")

        validator = DialogValidator(content_dir, context)
        result = validator.validate_cross_references()

        assert result.errors == []
        assert result.item_count == 1
        assert result.metadata["Dialog entries validated"] == 1
