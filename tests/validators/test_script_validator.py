"""Tests for ScriptValidator."""

import json
from typing import TYPE_CHECKING, Any, ClassVar
from unittest.mock import patch

import pytest

from pedre.actions.base import Action
from pedre.actions.registry import ActionRegistry
from pedre.conditions.base import Condition
from pedre.conditions.registry import ConditionRegistry
from pedre.events.base import Event
from pedre.events.registry import EventRegistry
from pedre.types import EntityReference
from pedre.validators.context import ValidationContext
from pedre.validators.script_validator import ScriptValidator

if TYPE_CHECKING:
    from pathlib import Path

    from pedre.game import GameContext


class TestScriptValidator:
    """Test ScriptValidator class."""

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
    def context(self) -> ValidationContext:
        """Create a validation context for tests."""
        return ValidationContext()

    @pytest.fixture
    def scripts_dir(self, tmp_path: Path) -> Path:
        """Create a temporary scripts directory."""
        scripts_dir = tmp_path / "scripts"
        scripts_dir.mkdir(parents=True)
        return scripts_dir

    @pytest.fixture
    def setup_basic_registries(self) -> None:
        """Setup basic registries for tests."""

        @EventRegistry.register
        class TestEvent(Event):
            name: ClassVar[str] = "test_event"
            trigger_keys: ClassVar[set[str]] = {"filter_key"}

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

    def test_name_property(self, scripts_dir: Path, context: ValidationContext) -> None:
        """Test validator name."""
        validator = ScriptValidator(scripts_dir, context)
        assert validator.name == "Scripts"

    def test_validate_directory_not_found(self, tmp_path: Path, context: ValidationContext) -> None:
        """Test error when scripts directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"
        validator = ScriptValidator(nonexistent_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert f"Scripts directory not found: {nonexistent_dir}" in result.errors
        assert result.item_count == 0

    def test_validate_no_script_files(self, scripts_dir: Path, context: ValidationContext) -> None:
        """Test validation with no script files."""
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 0

    def test_validate_invalid_json(
        self, scripts_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error on invalid JSON."""
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text("not valid json{")
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert any("Failed to parse" in e for e in result.errors)

    def test_validate_os_error(
        self, scripts_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error handling when OSError occurs while reading file."""
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps({"test_script": {"actions": [{"name": "test_action"}]}}))

        validator = ScriptValidator(scripts_dir, context)

        # Mock Path.open to raise PermissionError (a subclass of OSError)
        with patch("pathlib.Path.open", side_effect=PermissionError("Permission denied")):
            result = validator.validate()

        assert any("Failed to load" in e for e in result.errors)

    def test_validate_trigger_missing_event(
        self, scripts_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error when trigger is missing event key."""
        data = {"test_script": {"trigger": {"filter_key": "value"}, "actions": [{"name": "test_action"}]}}
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(data))
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert any("trigger missing required 'event' key" in e for e in result.errors)

    def test_validate_trigger_unknown_event(
        self, scripts_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error when trigger references unknown event."""
        data = {"test_script": {"trigger": {"event": "unknown_event"}, "actions": [{"name": "test_action"}]}}
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(data))
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert any("unknown event 'unknown_event'" in e for e in result.errors)

    def test_validate_trigger_unknown_filter_keys(
        self, scripts_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error when trigger has unknown filter keys."""
        data = {
            "test_script": {
                "trigger": {"event": "test_event", "unknown_key": "value"},
                "actions": [{"name": "test_action"}],
            }
        }
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(data))
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert any("trigger has unknown filter keys" in e for e in result.errors)
        assert any("unknown_key" in e for e in result.errors)

    def test_validate_condition_parse_error(
        self, scripts_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error when condition fails to parse."""
        data = {
            "test_script": {
                "conditions": [{"name": "nonexistent_condition"}],
                "actions": [{"name": "test_action"}],
            }
        }
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(data))
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert any("condition 0:" in e for e in result.errors)

    def test_validate_action_parse_error(
        self, scripts_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error when action fails to parse."""
        data = {"test_script": {"actions": [{"name": "nonexistent_action"}]}}
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(data))
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert any("action 0:" in e for e in result.errors)

    def test_validate_empty_actions_list(
        self, scripts_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error when actions list is empty."""
        data = {"test_script": {"actions": []}}
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(data))
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert any("'actions' list is empty" in e for e in result.errors)

    def test_validate_on_condition_fail_parse_error(
        self, scripts_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test error when on_condition_fail action fails to parse."""
        data = {
            "test_script": {
                "actions": [{"name": "test_action"}],
                "on_condition_fail": [{"name": "nonexistent_action"}],
            }
        }
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(data))
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert any("on_condition_fail action 0:" in e for e in result.errors)

    def test_validate_valid_script(
        self, scripts_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test validation of a valid script."""
        data = {
            "test_script": {
                "trigger": {"event": "test_event", "filter_key": "value"},
                "conditions": [{"name": "test_condition"}],
                "actions": [{"name": "test_action"}],
                "on_condition_fail": [{"name": "test_action"}],
                "scene": "test_map",
                "run_once": True,
            }
        }
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(data))
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 1
        assert result.metadata["Total Actions"] == 1
        assert result.metadata["Total Conditions"] == 1
        assert result.metadata["Scripts with Triggers"] == 1

    def test_validate_script_references_stored(
        self, scripts_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test that script references are stored in context."""
        data = {
            "test_script": {
                "actions": [{"name": "test_action"}],
                "scene": "test_map",
            }
        }
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(data))
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert "test_script" in context.script_references
        # Check that scene reference is stored
        refs = context.script_references["test_script"]
        assert EntityReference(type="map", name="test_map") in refs

    def test_validate_script_trigger_references_stored(self, scripts_dir: Path, context: ValidationContext) -> None:
        """Test that event trigger references using reference_fields are properly stored."""

        # Create a mock event with explicit reference fields
        @EventRegistry.register
        class RefFieldEvent(Event):
            name: ClassVar[str] = "ref_field_event"
            trigger_keys: ClassVar[frozenset[str]] = frozenset({"target_npc"})
            reference_fields: ClassVar[dict[str, str]] = {"target_npc": "npc"}

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

        data = {
            "test_script": {
                "trigger": {"event": "ref_field_event", "target_npc": "merchant"},
                "actions": [{"name": "test_action"}],
            }
        }
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(data))
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert "test_script" in context.script_references
        refs = context.script_references["test_script"]

        # Verify the reference_fields mapped the trigger key correctly to an NPC reference
        assert EntityReference(type="npc", name="merchant") in refs

    def test_validate_cross_references_npc_not_found(self, scripts_dir: Path, context: ValidationContext) -> None:
        """Test cross-reference validation when NPC is not found."""
        context.script_references["test_script"] = {EntityReference(type="npc", name="missing_npc")}
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate_cross_references()

        assert any("NPC 'missing_npc' not found" in e for e in result.errors)

    def test_validate_cross_references_waypoint_not_found(self, scripts_dir: Path, context: ValidationContext) -> None:
        """Test cross-reference validation when waypoint is not found."""
        context.script_references["test_script"] = {EntityReference(type="waypoint", name="missing_waypoint")}
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate_cross_references()

        assert any("waypoint 'missing_waypoint' not found" in e for e in result.errors)

    def test_validate_cross_references_portal_not_found(self, scripts_dir: Path, context: ValidationContext) -> None:
        """Test cross-reference validation when portal is not found."""
        context.script_references["test_script"] = {EntityReference(type="portal", name="missing_portal")}
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate_cross_references()

        assert any("portal 'missing_portal' not found" in e for e in result.errors)

    def test_validate_cross_references_map_not_found(self, scripts_dir: Path, context: ValidationContext) -> None:
        """Test cross-reference validation when map is not found."""
        context.script_references["test_script"] = {EntityReference(type="map", name="missing_map")}
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate_cross_references()

        assert any("target map 'missing_map' not found" in e for e in result.errors)

    def test_validate_cross_references_inventory_item_not_found(
        self, scripts_dir: Path, context: ValidationContext
    ) -> None:
        """Test cross-reference validation when inventory item is not found."""
        context.script_references["test_script"] = {EntityReference(type="inventory_item", name="missing_item")}
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate_cross_references()

        assert any("inventory item 'missing_item' not found" in e for e in result.errors)

    def test_validate_cross_references_interactive_object_not_found(
        self, scripts_dir: Path, context: ValidationContext
    ) -> None:
        """Test cross-reference validation when interactive object is not found."""
        context.script_references["test_script"] = {EntityReference(type="interactive_object", name="missing_object")}
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate_cross_references()

        assert any("interactive object 'missing_object' not found" in e for e in result.errors)

    def test_validate_cross_references_map_scoped_npc(self, scripts_dir: Path, context: ValidationContext) -> None:
        """Test cross-reference validation with map-scoped NPC."""
        # Add a map reference to trigger map-scoped validation
        context.script_references["test_script"] = {
            EntityReference(type="map", name="test_map"),
            EntityReference(type="npc", name="test_npc"),
        }
        # Register the map but not the NPC in that map (add a different NPC)
        context.add_map_entity("test_map", "npcs", "other_npc")

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate_cross_references()

        assert any("NPC 'test_npc' not found in map 'test_map'" in e for e in result.errors)

    def test_validate_cross_references_valid(self, scripts_dir: Path, context: ValidationContext) -> None:
        """Test successful cross-reference validation."""
        context.script_references["test_script"] = {
            EntityReference(type="npc", name="test_npc"),
            EntityReference(type="waypoint", name="test_waypoint"),
        }
        # Register the entities
        context.add_map_entity("test_map", "npcs", "test_npc")
        context.add_map_entity("test_map", "waypoints", "test_waypoint")

        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate_cross_references()

        assert result.errors == []
        assert result.item_count == 1

    def test_validate_multiple_scripts(
        self, scripts_dir: Path, context: ValidationContext, setup_basic_registries: None
    ) -> None:
        """Test validation of multiple scripts."""
        data = {
            "script1": {"actions": [{"name": "test_action"}]},
            "script2": {"actions": [{"name": "test_action"}]},
        }
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(data))
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 2

    def test_validate_trigger_with_no_trigger_keys(self, scripts_dir: Path, context: ValidationContext) -> None:
        """Test trigger validation when event has no trigger_keys (None)."""

        # Register an event with no trigger_keys
        @EventRegistry.register
        class NoKeysEvent(Event):
            name: ClassVar[str] = "no_keys_event"
            trigger_keys: ClassVar[set[str] | None] = None

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

        # Script with trigger that has filters, but event has no trigger_keys
        data = {
            "test_script": {
                "trigger": {"event": "no_keys_event", "any_filter": "value"},
                "actions": [{"name": "test_action"}],
            }
        }
        script_file = scripts_dir / "test_scripts.json"
        script_file.write_text(json.dumps(data))
        validator = ScriptValidator(scripts_dir, context)
        result = validator.validate()

        # Should pass - when trigger_keys is None, no filter validation is done
        assert result.errors == []
        assert result.item_count == 1
