"""Tests for MapValidator."""

import json
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock, patch

import pytest

from pedre.conf import settings
from pedre.validators.context import ValidationContext
from pedre.validators.map_validator import MapValidator

if TYPE_CHECKING:
    from pathlib import Path


class TestMapValidator:
    """Test MapValidator class."""

    @pytest.fixture
    def maps_dir(self, tmp_path: Path) -> Path:
        """Create a temporary maps directory."""
        maps_dir = tmp_path / "maps"
        maps_dir.mkdir(parents=True)
        return maps_dir

    @pytest.fixture
    def context(self) -> ValidationContext:
        """Create a validation context for tests."""
        return ValidationContext()

    def _create_mock_tilemap(
        self,
        object_lists: dict[str, list[Any]] | None = None,
        properties: dict[str, Any] | None = None,
    ) -> Mock:
        """Create a mock TileMap object.

        Args:
            object_lists: Dictionary of layer names to lists of objects
            properties: Map-level properties

        Returns:
            Mock TileMap object
        """
        tile_map = Mock()
        tile_map.object_lists = object_lists or {}
        tile_map.properties = properties or {}
        return tile_map

    def _create_mock_object(
        self,
        name: str | None = None,
        properties: dict[str, Any] | None = None,
        shape: list[float] | list[int | float | tuple[int | float, int | float]] | None = None,
    ) -> Mock:
        """Create a mock map object (waypoint, NPC, portal, etc).

        Args:
            name: Object name
            properties: Object properties
            shape: Object shape coordinates

        Returns:
            Mock object
        """
        obj = Mock()
        obj.name = name
        obj.properties = properties or {}
        obj.shape = shape
        return obj

    def test_validator_name(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test validator name property."""
        validator = MapValidator(maps_dir, context)
        assert validator.name == "Maps"

    def test_directory_not_found(self, tmp_path: Path, context: ValidationContext) -> None:
        """Test validate when directory doesn't exist."""
        nonexistent_dir = tmp_path / "nonexistent"
        validator = MapValidator(nonexistent_dir, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert f"Maps directory not found: {nonexistent_dir}" in result.errors
        assert result.item_count == 0
        assert result.metadata == {}

    def test_no_map_files(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test validate when no map files found."""
        validator = MapValidator(maps_dir, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 0
        assert result.metadata == {}

    def test_map_load_error(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test handling of map load errors."""
        # Create a dummy TMX file
        map_file = maps_dir / "broken.tmx"
        map_file.write_text("invalid tmx content")

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", side_effect=RuntimeError("Failed to load")):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "Failed to load map 'broken.tmx'" in result.errors[0]

    # Waypoint Layer Tests

    def test_waypoint_valid(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test valid waypoint with name and shape."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        waypoint = self._create_mock_object(name="spawn_point", shape=[100.0, 200.0])
        tile_map = self._create_mock_tilemap(object_lists={"Waypoints": [waypoint]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert result.errors == []
        assert "spawn_point" in context.get_map_waypoints("test")

    def test_waypoint_missing_name(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test waypoint without name property."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        waypoint = self._create_mock_object(name=None, shape=[100.0, 200.0])
        tile_map = self._create_mock_tilemap(object_lists={"Waypoints": [waypoint]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "waypoint missing required 'name' property" in result.errors[0]

    def test_waypoint_missing_shape(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test waypoint without shape."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        waypoint = self._create_mock_object(name="spawn_point", shape=None)
        tile_map = self._create_mock_tilemap(object_lists={"Waypoints": [waypoint]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "missing shape coordinates" in result.errors[0]

    def test_waypoint_layer_optional(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test that map without Waypoints layer is valid."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        tile_map = self._create_mock_tilemap(object_lists={})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert result.errors == []

    # NPC Layer Tests

    def test_npc_valid(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test valid NPC with required properties."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        npc = self._create_mock_object(name="merchant", properties={"sprite_sheet": "merchant.png"})
        tile_map = self._create_mock_tilemap(object_lists={"NPCs": [npc]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert result.errors == []
        assert "merchant" in context.get_map_npcs("test")

    def test_npc_missing_name(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test NPC without name property."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        npc = self._create_mock_object(name=None, properties={"sprite_sheet": "merchant.png"})
        tile_map = self._create_mock_tilemap(object_lists={"NPCs": [npc]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "NPC missing required 'name' property" in result.errors[0]

    def test_npc_invalid_initially_hidden_type(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test NPC with initially_hidden that is not bool."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        npc = self._create_mock_object(
            name="merchant",
            properties={"sprite_sheet": "merchant.png", "initially_hidden": "not_bool"},
        )
        tile_map = self._create_mock_tilemap(object_lists={"NPCs": [npc]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "'initially_hidden' must be bool" in result.errors[0]

    def test_npc_layer_optional(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test that map without NPCs layer is valid."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        tile_map = self._create_mock_tilemap(object_lists={})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert result.errors == []

    # Portal Layer Tests

    def test_portal_valid(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test valid portal with name, properties, and shape."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        portal = self._create_mock_object(
            name="exit_portal",
            properties={"destination_map": "village"},
            shape=[100.0, 200.0],
        )
        tile_map = self._create_mock_tilemap(object_lists={"Portals": [portal]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert result.errors == []

    def test_portal_missing_name(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test portal without name property."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        portal = self._create_mock_object(
            name=None,
            properties={"destination_map": "village"},
            shape=[100.0, 200.0],
        )
        tile_map = self._create_mock_tilemap(object_lists={"Portals": [portal]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "portal missing required 'name' property" in result.errors[0]

    def test_portal_missing_properties(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test portal without properties."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        portal = Mock()
        portal.name = "exit_portal"
        portal.properties = None
        portal.shape = [100.0, 200.0]

        tile_map = self._create_mock_tilemap(object_lists={"Portals": [portal]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "missing required properties" in result.errors[0]

    def test_portal_missing_shape(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test portal without shape."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        portal = Mock()
        portal.name = "exit_portal"
        portal.properties = {"destination_map": "village"}
        portal.shape = None

        tile_map = self._create_mock_tilemap(object_lists={"Portals": [portal]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "missing shape" in result.errors[0]

    def test_portal_layer_optional(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test that map without Portals layer is valid."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        tile_map = self._create_mock_tilemap(object_lists={})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert result.errors == []

    # Interactive Layer Tests

    def test_interactive_valid(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test valid interactive object."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        interactive = self._create_mock_object(name="treasure_chest", shape=[100.0, 200.0])
        tile_map = self._create_mock_tilemap(object_lists={"Interactive": [interactive]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert result.errors == []

    def test_interactive_missing_name(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test interactive object without name."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        interactive = self._create_mock_object(name=None, shape=[100.0, 200.0])
        tile_map = self._create_mock_tilemap(object_lists={"Interactive": [interactive]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "object missing required 'name' property" in result.errors[0]

    def test_interactive_missing_shape(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test interactive object without shape."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        interactive = self._create_mock_object(name="treasure_chest", shape=None)
        tile_map = self._create_mock_tilemap(object_lists={"Interactive": [interactive]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "missing shape" in result.errors[0]

    def test_interactive_layer_optional(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test that map without Interactive layer is valid."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        tile_map = self._create_mock_tilemap(object_lists={})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert result.errors == []

    # Property Type Validation Helper Tests

    def test_validate_property_type_valid_single(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test _validate_property_type with valid single type."""
        validator = MapValidator(maps_dir, context)

        error = validator._validate_property_type(42, int, "test_prop", "TestEntity")

        assert error is None

    def test_validate_property_type_valid_tuple(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test _validate_property_type with valid tuple of types."""
        validator = MapValidator(maps_dir, context)

        error_int = validator._validate_property_type(42, (int, float), "test_prop", "TestEntity")
        error_float = validator._validate_property_type(3.14, (int, float), "test_prop", "TestEntity")

        assert error_int is None
        assert error_float is None

    def test_validate_property_type_invalid_single(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test _validate_property_type with invalid single type."""
        validator = MapValidator(maps_dir, context)

        error = validator._validate_property_type("not_int", int, "test_prop", "TestEntity")

        assert error is not None
        assert "'test_prop' must be int" in error
        assert "got str" in error

    def test_validate_property_type_invalid_tuple(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test _validate_property_type with invalid tuple of types."""
        validator = MapValidator(maps_dir, context)

        error = validator._validate_property_type("not_numeric", (int, float), "test_prop", "TestEntity")

        assert error is not None
        assert "'test_prop' must be int or float" in error
        assert "got str" in error

    # Cross-Reference Validation Tests

    def test_validate_cross_references_no_maps_json(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test cross-references pass when maps.json does not exist."""
        validator = MapValidator(maps_dir, context)
        result = validator.validate_cross_references()

        assert result.errors == []
        assert result.item_count == 0
        assert result.metadata == {}

    def test_validate_cross_references_valid(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test cross-references pass when maps.json entry matches a known TMX."""
        content_dir = maps_dir.parent / settings.CONTENT_DIRECTORY
        content_dir.mkdir(parents=True)
        (content_dir / "maps.json").write_text(json.dumps({"village": {"music": "bg.ogg"}}))
        context.map_entities["village"] = {}

        validator = MapValidator(maps_dir, context)

        with patch("pedre.validators.map_validator.asset_exists", return_value=True):
            result = validator.validate_cross_references()

        assert result.errors == []

    def test_validate_cross_references_missing_tmx(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test cross-references fail when maps.json entry has no TMX file."""
        content_dir = maps_dir.parent / settings.CONTENT_DIRECTORY
        content_dir.mkdir(parents=True)
        (content_dir / "maps.json").write_text(json.dumps({"ghost_map": {}}))

        validator = MapValidator(maps_dir, context)
        result = validator.validate_cross_references()

        assert len(result.errors) == 1
        assert "ghost_map" in result.errors[0]
        assert "no corresponding TMX file" in result.errors[0]

    def test_validate_cross_references_invalid_music_type(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test cross-references fail when maps.json music field is not a string."""
        content_dir = maps_dir.parent / settings.CONTENT_DIRECTORY
        content_dir.mkdir(parents=True)
        (content_dir / "maps.json").write_text(json.dumps({"village": {"music": 123}}))

        validator = MapValidator(maps_dir, context)
        result = validator.validate_cross_references()

        assert len(result.errors) == 1
        assert "music" in result.errors[0]
        assert "string" in result.errors[0]

    def test_validate_cross_references_music_not_found(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test cross-references fail when maps.json music file does not exist."""
        content_dir = maps_dir.parent / settings.CONTENT_DIRECTORY
        content_dir.mkdir(parents=True)
        (content_dir / "maps.json").write_text(json.dumps({"village": {"music": "missing.ogg"}}))
        context.map_entities["village"] = {}

        validator = MapValidator(maps_dir, context)

        with patch("pedre.validators.map_validator.asset_exists", return_value=False):
            result = validator.validate_cross_references()

        assert len(result.errors) == 1
        assert f"music file '{settings.AUDIO_MUSIC_DIRECTORY}/missing.ogg' not found" in result.errors[0]

    def test_validate_cross_references_invalid_camera_follow(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test cross-references fail when camera_follow has an invalid value."""
        content_dir = maps_dir.parent / settings.CONTENT_DIRECTORY
        content_dir.mkdir(parents=True)
        (content_dir / "maps.json").write_text(json.dumps({"village": {"camera_follow": "invalid"}}))
        context.map_entities["village"] = {}

        validator = MapValidator(maps_dir, context)
        result = validator.validate_cross_references()

        assert len(result.errors) == 1
        assert "camera_follow" in result.errors[0]

    def test_validate_cross_references_camera_follow_npc(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test cross-references pass for valid npc: camera_follow format."""
        content_dir = maps_dir.parent / settings.CONTENT_DIRECTORY
        content_dir.mkdir(parents=True)
        (content_dir / "maps.json").write_text(json.dumps({"village": {"camera_follow": "npc:bob"}}))
        context.map_entities["village"] = {}

        validator = MapValidator(maps_dir, context)
        result = validator.validate_cross_references()

        assert result.errors == []

    def test_validate_cross_references_invalid_json(self, maps_dir: Path, context: ValidationContext) -> None:
        """Invalid JSON in maps.json during cross-reference returns empty result."""
        content_dir = maps_dir.parent / settings.CONTENT_DIRECTORY
        content_dir.mkdir(parents=True)
        (content_dir / "maps.json").write_text("not valid json{")

        validator = MapValidator(maps_dir, context)
        result = validator.validate_cross_references()

        assert result.errors == []

    def test_validate_cross_references_root_not_dict(self, maps_dir: Path, context: ValidationContext) -> None:
        """Non-dict root in maps.json during cross-reference returns empty result."""
        content_dir = maps_dir.parent / settings.CONTENT_DIRECTORY
        content_dir.mkdir(parents=True)
        (content_dir / "maps.json").write_text(json.dumps([{"music": "bg.ogg"}]))

        validator = MapValidator(maps_dir, context)
        result = validator.validate_cross_references()

        assert result.errors == []

    def test_validate_cross_references_map_entry_not_dict(self, maps_dir: Path, context: ValidationContext) -> None:
        """Map entry that is not a dict produces an error."""
        content_dir = maps_dir.parent / settings.CONTENT_DIRECTORY
        content_dir.mkdir(parents=True)
        (content_dir / "maps.json").write_text(json.dumps({"village": "not_a_dict"}))

        validator = MapValidator(maps_dir, context)
        result = validator.validate_cross_references()

        assert len(result.errors) == 1
        assert "village" in result.errors[0]
        assert "must be a dictionary" in result.errors[0]

    # Metadata and Multiple Maps Tests

    def test_metadata_counts(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test that metadata correctly counts entities."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        npc1 = self._create_mock_object(name="merchant", properties={"sprite_sheet": "merchant.png"})
        npc2 = self._create_mock_object(name="guard", properties={"sprite_sheet": "guard.png"})
        waypoint1 = self._create_mock_object(name="spawn", shape=[100.0, 200.0])
        waypoint2 = self._create_mock_object(name="exit", shape=[300.0, 400.0])
        portal = self._create_mock_object(name="portal", properties={"dest": "village"}, shape=[150.0, 250.0])
        interactive = self._create_mock_object(name="chest", shape=[200.0, 300.0])

        tile_map = self._create_mock_tilemap(
            object_lists={
                "NPCs": [npc1, npc2],
                "Waypoints": [waypoint1, waypoint2],
                "Portals": [portal],
                "Interactive": [interactive],
            }
        )

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert result.errors == []
        assert result.metadata["Total NPCs"] == 2
        assert result.metadata["Total Waypoints"] == 2
        assert result.metadata["Total Portals"] == 1
        assert result.metadata["Total Interactive Objects"] == 1

    def test_multiple_maps(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test validating multiple TMX files."""
        map_file1 = maps_dir / "village.tmx"
        map_file1.write_text("")
        map_file2 = maps_dir / "forest.tmx"
        map_file2.write_text("")

        npc1 = self._create_mock_object(name="merchant", properties={"sprite_sheet": "merchant.png"})
        npc2 = self._create_mock_object(name="hermit", properties={"sprite_sheet": "hermit.png"})

        tile_map1 = self._create_mock_tilemap(object_lists={"NPCs": [npc1]})
        tile_map2 = self._create_mock_tilemap(object_lists={"NPCs": [npc2]})

        validator = MapValidator(maps_dir, context)

        def mock_load_tilemap(path: str) -> Mock:
            if "village" in path:
                return tile_map1
            return tile_map2

        with patch("arcade.load_tilemap", side_effect=mock_load_tilemap):
            result = validator.validate()

        assert result.errors == []
        assert result.item_count == 2
        assert "merchant" in context.get_map_npcs("village")

    def test_waypoint_insufficient_coordinates(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test waypoint with insufficient coordinates (less than 2)."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        waypoint = self._create_mock_object(name="spawn_point", shape=[100.0])
        tile_map = self._create_mock_tilemap(object_lists={"Waypoints": [waypoint]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "shape must have at least 2 coordinates" in result.errors[0]

    def test_waypoint_non_numeric_coordinates(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test waypoint with invalid shape (e.g. Polygon instead of Point)."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        # Simulate a Polygon (list of points) which is invalid for a Waypoint (expects a single Point)
        # float([(0.0, 0.0)]) raises TypeError
        waypoint = self._create_mock_object(name="spawn_point", shape=[(0.0, 0.0), (10.0, 10.0)])
        tile_map = self._create_mock_tilemap(object_lists={"Waypoints": [waypoint]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "invalid shape coordinates" in result.errors[0]

    def test_npc_valid_optional_properties(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test NPC with valid optional properties."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        npc = self._create_mock_object(
            name="merchant",
            properties={
                "sprite_sheet": "merchant.png",
                "tile_size": 32,
                "scale": 1.5,
                "initially_hidden": True,
            },
        )
        tile_map = self._create_mock_tilemap(object_lists={"NPCs": [npc]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert result.errors == []

    def test_player_valid_optional_properties(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test Player with valid optional properties."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        player = self._create_mock_object(
            name="player",
            properties={
                "sprite_sheet": "player.png",
                "tile_size": 32,
                "scale": 1.0,
                "spawn_at_portal": True,
            },
        )
        tile_map = self._create_mock_tilemap(object_lists={"Player": [player]})

        validator = MapValidator(maps_dir, context)

        with (
            patch("arcade.load_tilemap", return_value=tile_map),
            patch("pedre.validators.map_validator.asset_exists", return_value=True),
        ):
            result = validator.validate()

        assert result.errors == []

    def test_map_with_prepopulated_context(self, maps_dir: Path, context: ValidationContext) -> None:
        """Test validation when context already has the map registered."""
        map_file = maps_dir / "test.tmx"
        map_file.write_text("")

        # Pre-populate the context with the map name
        context.map_entities["test"] = {"npcs": {"existing_npc"}}

        npc = self._create_mock_object(name="new_npc", properties={"sprite_sheet": "npc.png"})
        tile_map = self._create_mock_tilemap(object_lists={"NPCs": [npc]})

        validator = MapValidator(maps_dir, context)

        with patch("arcade.load_tilemap", return_value=tile_map):
            result = validator.validate()

        assert result.errors == []
        # Both the pre-existing and new NPC should be in context
        assert "existing_npc" in context.get_map_npcs("test")
        assert "new_npc" in context.get_map_npcs("test")
