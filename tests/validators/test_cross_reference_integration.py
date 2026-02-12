"""Integration tests for cross-reference validation between validators."""

import json
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

import pytest

from pedre.actions.base import Action
from pedre.actions.registry import ActionRegistry
from pedre.conditions.registry import ConditionRegistry
from pedre.events.registry import EventRegistry
from pedre.types import EntityReference
from pedre.validators.context import ValidationContext
from pedre.validators.dialog_validator import DialogValidator
from pedre.validators.map_validator import MapValidator
from pedre.validators.script_validator import ScriptValidator

if TYPE_CHECKING:
    from pathlib import Path


class TestCrossReferenceIntegration:
    """Test cross-reference validation between different validators."""

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
    def setup_registries(self) -> None:
        """Setup basic registries for tests."""

        # Register test actions used in scripts
        @ActionRegistry.register("move_npc")
        class MoveNPCAction(Action):
            def __init__(self, **kwargs: object) -> None:
                pass

            @classmethod
            def from_dict(cls, data: dict) -> MoveNPCAction:
                return cls(**data)

            @staticmethod
            def validate_params(data: dict) -> list[str]:
                return []

            @classmethod
            def extract_references(cls, _data: dict[str, Any]) -> list[EntityReference]:
                """Extract references for validation."""
                refs: list[EntityReference] = []

                refs.extend(EntityReference(type="npc", name=npc) for npc in _data.get("npcs", []))

                waypoint = _data.get("waypoint")
                if isinstance(waypoint, str):
                    refs.append(EntityReference(type="waypoint", name=waypoint))

                return refs

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

            @classmethod
            def extract_references(cls, _data: dict[str, Any]) -> list[EntityReference]:
                """Extract references for validation."""
                refs: list[EntityReference] = []

                target_map = _data.get("target_map")
                if isinstance(target_map, str):
                    map_name = target_map.removesuffix(".tmx")

                    # Map reference
                    refs.append(
                        EntityReference(
                            type="map",
                            name=map_name,
                        )
                    )

                    spawn_waypoint = _data.get("spawn_waypoint")
                    if isinstance(spawn_waypoint, str):
                        refs.append(
                            EntityReference(
                                type="waypoint",
                                name=spawn_waypoint,
                                scope="map",
                                target_map=map_name,
                            )
                        )

                return refs

    @pytest.fixture
    def temp_dirs(self, tmp_path: Path) -> dict[str, Path]:
        """Create temporary directories for all asset types."""
        dirs = {
            "maps": tmp_path / "maps",
            "dialogs": tmp_path / "dialogs",
            "scripts": tmp_path / "scripts",
        }
        for dir_path in dirs.values():
            dir_path.mkdir(parents=True)
        return dirs

    @pytest.fixture
    def context(self) -> ValidationContext:
        """Create a validation context for tests."""
        return ValidationContext()

    def _create_mock_tilemap(
        self,
        npcs: list[str] | None = None,
        waypoints: list[str] | None = None,
    ) -> Mock:
        """Create a mock TileMap with NPCs and waypoints.

        Args:
            npcs: List of NPC names
            waypoints: List of waypoint names

        Returns:
            Mock TileMap object
        """
        tile_map = Mock()
        tile_map.properties = {}
        tile_map.object_lists = {}

        if npcs:
            npc_objects = []
            for npc_name in npcs:
                npc = Mock()
                npc.name = npc_name
                npc.properties = {"sprite_sheet": f"{npc_name}.png"}
                npc_objects.append(npc)
            tile_map.object_lists["NPCs"] = npc_objects

        if waypoints:
            waypoint_objects = []
            for waypoint_name in waypoints:
                waypoint = Mock()
                waypoint.name = waypoint_name
                waypoint.shape = [100.0, 200.0]
                waypoint_objects.append(waypoint)
            tile_map.object_lists["Waypoints"] = waypoint_objects

        return tile_map

    # Dialog-to-Map NPC Cross-Reference Tests

    def test_dialog_npc_exists_in_map(
        self,
        temp_dirs: dict[str, Path],
        context: ValidationContext,
    ) -> None:
        """Test dialog referencing an NPC that exists in the map."""
        # Create map with NPC
        map_file = temp_dirs["maps"] / "village.tmx"
        map_file.write_text("")

        tile_map = self._create_mock_tilemap(npcs=["merchant"])

        # Create dialog for that NPC
        dialog_file = temp_dirs["dialogs"] / "village_dialogs.json"
        dialog_data = {"merchant": {"0": {"text": ["Hello!"]}}}
        dialog_file.write_text(json.dumps(dialog_data))

        # Phase 1: Structural validation
        map_validator = MapValidator(temp_dirs["maps"], context)
        dialog_validator = DialogValidator(temp_dirs["dialogs"], context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            map_result = map_validator.validate()
            dialog_result = dialog_validator.validate()

        assert map_result.errors == []
        assert dialog_result.errors == []

        # Phase 2: Cross-reference validation
        dialog_xref_result = dialog_validator.validate_cross_references()

        assert dialog_xref_result.errors == []

    def test_dialog_npc_missing_from_map(
        self,
        temp_dirs: dict[str, Path],
        context: ValidationContext,
    ) -> None:
        """Test dialog referencing an NPC that doesn't exist in the map."""
        # Create map WITHOUT the NPC
        map_file = temp_dirs["maps"] / "village.tmx"
        map_file.write_text("")

        tile_map = self._create_mock_tilemap(npcs=[])

        # Create dialog for non-existent NPC
        dialog_file = temp_dirs["dialogs"] / "village_dialogs.json"
        dialog_data = {"merchant": {"0": {"text": ["Hello!"]}}}
        dialog_file.write_text(json.dumps(dialog_data))

        # Phase 1: Structural validation
        map_validator = MapValidator(temp_dirs["maps"], context)
        dialog_validator = DialogValidator(temp_dirs["dialogs"], context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            map_result = map_validator.validate()
            dialog_result = dialog_validator.validate()

        assert map_result.errors == []
        assert dialog_result.errors == []

        # Phase 2: Cross-reference validation
        dialog_xref_result = dialog_validator.validate_cross_references()

        assert len(dialog_xref_result.errors) == 1
        assert "NPC 'merchant' not found in map 'village.tmx'" in dialog_xref_result.errors[0]

    def test_dialog_multiple_npcs_partial_match(
        self,
        temp_dirs: dict[str, Path],
        context: ValidationContext,
    ) -> None:
        """Test dialog with multiple NPCs where some exist and some don't."""
        # Create map with only one NPC
        map_file = temp_dirs["maps"] / "village.tmx"
        map_file.write_text("")

        tile_map = self._create_mock_tilemap(npcs=["merchant"])

        # Create dialog for two NPCs
        dialog_file = temp_dirs["dialogs"] / "village_dialogs.json"
        dialog_data = {
            "merchant": {"0": {"text": ["Hello!"]}},
            "guard": {"0": {"text": ["Halt!"]}},
        }
        dialog_file.write_text(json.dumps(dialog_data))

        # Phase 1: Structural validation
        map_validator = MapValidator(temp_dirs["maps"], context)
        dialog_validator = DialogValidator(temp_dirs["dialogs"], context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            map_result = map_validator.validate()
            dialog_result = dialog_validator.validate()

        assert map_result.errors == []
        assert dialog_result.errors == []

        # Phase 2: Cross-reference validation
        dialog_xref_result = dialog_validator.validate_cross_references()

        assert len(dialog_xref_result.errors) == 1
        assert "NPC 'guard' not found in map 'village.tmx'" in dialog_xref_result.errors[0]

    # Script-to-Map Cross-Reference Tests

    def test_script_npc_exists_in_map(
        self,
        temp_dirs: dict[str, Path],
        context: ValidationContext,
        setup_registries: None,
    ) -> None:
        """Test script referencing an NPC that exists in a map."""
        # Create map with NPC
        map_file = temp_dirs["maps"] / "village.tmx"
        map_file.write_text("")

        tile_map = self._create_mock_tilemap(npcs=["merchant"], waypoints=["somewhere"])

        # Create script referencing that NPC
        script_file = temp_dirs["scripts"] / "quest_scripts.json"
        script_data = {
            "quest_script": {
                "actions": [{"type": "move_npc", "npcs": ["merchant"], "waypoint": "somewhere"}],
            }
        }
        script_file.write_text(json.dumps(script_data))

        # Phase 1: Structural validation
        map_validator = MapValidator(temp_dirs["maps"], context)
        script_validator = ScriptValidator(temp_dirs["scripts"], context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            map_result = map_validator.validate()
            script_result = script_validator.validate()

        assert map_result.errors == []
        assert script_result.errors == []

        # Phase 2: Cross-reference validation
        script_xref_result = script_validator.validate_cross_references()

        assert script_xref_result.errors == []

    def test_script_npc_missing_from_all_maps(
        self,
        temp_dirs: dict[str, Path],
        context: ValidationContext,
        setup_registries: None,
    ) -> None:
        """Test script referencing an NPC that doesn't exist in any map."""
        # Create map WITHOUT the NPC
        map_file = temp_dirs["maps"] / "village.tmx"
        map_file.write_text("")

        tile_map = self._create_mock_tilemap(npcs=[], waypoints=["somewhere"])

        # Create script referencing non-existent NPC
        script_file = temp_dirs["scripts"] / "quest_scripts.json"
        script_data = {
            "quest_script": {
                "actions": [{"type": "move_npc", "npcs": ["merchant"], "waypoint": "somewhere"}],
            }
        }
        script_file.write_text(json.dumps(script_data))

        # Phase 1: Structural validation
        map_validator = MapValidator(temp_dirs["maps"], context)
        script_validator = ScriptValidator(temp_dirs["scripts"], context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            map_result = map_validator.validate()
            script_result = script_validator.validate()

        assert map_result.errors == []
        assert script_result.errors == []

        # Phase 2: Cross-reference validation
        script_xref_result = script_validator.validate_cross_references()

        assert len(script_xref_result.errors) == 1
        assert "NPC 'merchant' not found in any map" in script_xref_result.errors[0]

    def test_script_waypoint_exists_in_map(
        self,
        temp_dirs: dict[str, Path],
        context: ValidationContext,
        setup_registries: None,
    ) -> None:
        """Test script referencing a waypoint that exists in a map."""
        # Create map with waypoint
        map_file = temp_dirs["maps"] / "village.tmx"
        map_file.write_text("")

        tile_map = self._create_mock_tilemap(waypoints=["spawn_point"])

        # Create script referencing that waypoint via change_scene
        script_file = temp_dirs["scripts"] / "teleport_scripts.json"
        script_data = {
            "teleport_script": {
                "actions": [{"type": "change_scene", "target_map": "village", "spawn_waypoint": "spawn_point"}],
            }
        }
        script_file.write_text(json.dumps(script_data))

        # Phase 1: Structural validation
        map_validator = MapValidator(temp_dirs["maps"], context)
        script_validator = ScriptValidator(temp_dirs["scripts"], context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            map_result = map_validator.validate()
            script_result = script_validator.validate()

        assert map_result.errors == []
        assert script_result.errors == []

        # Phase 2: Cross-reference validation
        script_xref_result = script_validator.validate_cross_references()

        assert script_xref_result.errors == []

    def test_script_waypoint_missing_from_all_maps(
        self,
        temp_dirs: dict[str, Path],
        context: ValidationContext,
        setup_registries: None,
    ) -> None:
        """Test script referencing a spawn waypoint that doesn't exist in the target map."""
        # Create map WITHOUT the waypoint
        map_file = temp_dirs["maps"] / "village.tmx"
        map_file.write_text("")

        tile_map = self._create_mock_tilemap(waypoints=[])

        # Create script referencing non-existent waypoint in target map
        script_file = temp_dirs["scripts"] / "teleport_scripts.json"
        script_data = {
            "teleport_script": {
                "actions": [{"type": "change_scene", "target_map": "village", "spawn_waypoint": "spawn_point"}],
            }
        }
        script_file.write_text(json.dumps(script_data))

        # Phase 1: Structural validation
        map_validator = MapValidator(temp_dirs["maps"], context)
        script_validator = ScriptValidator(temp_dirs["scripts"], context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            map_result = map_validator.validate()
            script_result = script_validator.validate()

        assert map_result.errors == []
        assert script_result.errors == []

        # Phase 2: Cross-reference validation
        script_xref_result = script_validator.validate_cross_references()

        assert len(script_xref_result.errors) == 1
        assert "waypoint 'spawn_point' not found in any map" in script_xref_result.errors[0]

    # Multi-File Integration Tests

    def test_multiple_maps_with_shared_entities(
        self,
        temp_dirs: dict[str, Path],
        context: ValidationContext,
        setup_registries: None,
    ) -> None:
        """Test scripts referencing entities across multiple maps."""
        # Create two maps with different NPCs
        village_map = temp_dirs["maps"] / "village.tmx"
        village_map.write_text("")
        forest_map = temp_dirs["maps"] / "forest.tmx"
        forest_map.write_text("")

        village_tilemap = self._create_mock_tilemap(npcs=["merchant"], waypoints=["village_spawn"])
        forest_tilemap = self._create_mock_tilemap(npcs=["hermit"], waypoints=["forest_spawn"])

        # Create script referencing NPCs from both maps
        script_file = temp_dirs["scripts"] / "quest_scripts.json"
        script_data = {
            "quest_script": {
                "actions": [
                    {"type": "move_npc", "npcs": ["merchant", "hermit"], "waypoint": "forest_spawn"},
                ],
            }
        }
        script_file.write_text(json.dumps(script_data))

        # Phase 1: Structural validation
        map_validator = MapValidator(temp_dirs["maps"], context)
        script_validator = ScriptValidator(temp_dirs["scripts"], context)

        def mock_load_tilemap(path: str) -> Mock:
            if "village" in path:
                return village_tilemap
            return forest_tilemap

        with patch("arcade.load_tilemap", side_effect=mock_load_tilemap):
            map_result = map_validator.validate()
            script_result = script_validator.validate()

        assert map_result.errors == []
        assert script_result.errors == []

        # Phase 2: Cross-reference validation
        script_xref_result = script_validator.validate_cross_references()

        # All references should be valid
        assert script_xref_result.errors == []

    def test_full_validation_pipeline(
        self,
        temp_dirs: dict[str, Path],
        context: ValidationContext,
        setup_registries: None,
    ) -> None:
        """Test the complete validation pipeline with all validators."""
        # Create map with NPCs and waypoints
        map_file = temp_dirs["maps"] / "village.tmx"
        map_file.write_text("")

        tile_map = self._create_mock_tilemap(
            npcs=["merchant", "guard"],
            waypoints=["spawn", "exit"],
        )

        # Create dialog for NPCs
        dialog_file = temp_dirs["dialogs"] / "village_dialogs.json"
        dialog_data = {
            "merchant": {"0": {"text": ["Welcome!"]}},
            "guard": {"0": {"text": ["Halt!"]}},
            "stranger": {"0": {"text": ["Hello!"]}},  # This NPC doesn't exist
        }
        dialog_file.write_text(json.dumps(dialog_data))

        # Create script referencing NPCs and waypoints
        script_file = temp_dirs["scripts"] / "quest_scripts.json"
        script_data = {
            "quest_script": {
                "actions": [
                    {"type": "move_npc", "npcs": ["guard", "bandit"], "waypoint": "exit"},
                ],
            }
        }
        script_file.write_text(json.dumps(script_data))

        # Create validators
        map_validator = MapValidator(temp_dirs["maps"], context)
        dialog_validator = DialogValidator(temp_dirs["dialogs"], context)
        script_validator = ScriptValidator(temp_dirs["scripts"], context)

        # Phase 1: Structural validation
        with patch("arcade.load_tilemap", return_value=tile_map):
            map_result = map_validator.validate()
            dialog_result = dialog_validator.validate()
            script_result = script_validator.validate()

        # All structural validation should pass
        assert map_result.errors == []
        assert dialog_result.errors == []
        assert script_result.errors == []

        # Phase 2: Cross-reference validation
        dialog_xref_result = dialog_validator.validate_cross_references()
        script_xref_result = script_validator.validate_cross_references()

        # Should find missing NPCs
        assert len(dialog_xref_result.errors) == 1
        assert "NPC 'stranger' not found in map 'village.tmx'" in dialog_xref_result.errors[0]

        assert len(script_xref_result.errors) == 1
        assert "NPC 'bandit' not found in any map" in script_xref_result.errors[0]

    def test_empty_context_cross_references(
        self,
        temp_dirs: dict[str, Path],
        context: ValidationContext,
        setup_registries: None,
    ) -> None:
        """Test cross-reference validation with empty context (no maps loaded)."""
        # Create dialog without any maps
        dialog_file = temp_dirs["dialogs"] / "village_dialogs.json"
        dialog_data = {
            "merchant": {"0": {"text": ["Hello!"]}},
        }
        dialog_file.write_text(json.dumps(dialog_data))

        # Create script without any maps
        script_file = temp_dirs["scripts"] / "quest_scripts.json"
        script_data = {
            "quest_script": {
                "actions": [{"type": "move_npc", "npcs": ["merchant"]}],  # No waypoint
            }
        }
        script_file.write_text(json.dumps(script_data))

        # Create validators (no map validator, so context stays empty)
        dialog_validator = DialogValidator(temp_dirs["dialogs"], context)
        script_validator = ScriptValidator(temp_dirs["scripts"], context)

        # Phase 1: Structural validation
        dialog_result = dialog_validator.validate()
        script_result = script_validator.validate()

        assert dialog_result.errors == []
        assert script_result.errors == []

        # Phase 2: Cross-reference validation with empty context
        dialog_xref_result = dialog_validator.validate_cross_references()
        script_xref_result = script_validator.validate_cross_references()

        # All NPCs should be reported as missing
        assert len(dialog_xref_result.errors) == 1
        assert "NPC 'merchant' not found in map 'village.tmx'" in dialog_xref_result.errors[0]

        assert len(script_xref_result.errors) == 1
        assert "NPC 'merchant' not found in any map" in script_xref_result.errors[0]
