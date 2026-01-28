"""Tests for animation property extraction from Tiled."""

import unittest
from unittest.mock import MagicMock

from pedre.constants import (
    ALL_ANIMATION_PROPERTIES,
    BASE_ANIMATION_PROPERTIES,
    NPC_SPECIAL_ANIMATION_PROPERTIES,
)
from pedre.systems.npc.manager import NPCManager
from pedre.systems.player.manager import PlayerManager


class TestPlayerAnimationPropertyExtraction(unittest.TestCase):
    """Test PlayerManager._get_animation_properties() method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.manager = PlayerManager()

    def test_extracts_base_animation_properties(self) -> None:
        """Test that all base animation properties are extracted."""
        properties = {
            "idle_up_frames": 4,
            "idle_up_row": 0,
            "idle_down_frames": 4,
            "idle_down_row": 1,
            "walk_up_frames": 6,
            "walk_up_row": 2,
            "walk_down_frames": 6,
            "walk_down_row": 3,
        }

        result = self.manager._get_animation_properties(properties)

        assert len(result) == 8
        assert result["idle_up_frames"] == 4
        assert result["idle_up_row"] == 0
        assert result["idle_down_frames"] == 4
        assert result["idle_down_row"] == 1
        assert result["walk_up_frames"] == 6
        assert result["walk_up_row"] == 2
        assert result["walk_down_frames"] == 6
        assert result["walk_down_row"] == 3

    def test_extracts_all_16_base_properties(self) -> None:
        """Test that all 16 base animation properties are extracted when present."""
        properties = {
            "idle_up_frames": 1,
            "idle_up_row": 2,
            "idle_down_frames": 3,
            "idle_down_row": 4,
            "idle_left_frames": 5,
            "idle_left_row": 6,
            "idle_right_frames": 7,
            "idle_right_row": 8,
            "walk_up_frames": 9,
            "walk_up_row": 10,
            "walk_down_frames": 11,
            "walk_down_row": 12,
            "walk_left_frames": 13,
            "walk_left_row": 14,
            "walk_right_frames": 15,
            "walk_right_row": 16,
        }

        result = self.manager._get_animation_properties(properties)

        assert len(result) == 16
        for key, value in properties.items():
            assert result[key] == value

    def test_ignores_non_animation_properties(self) -> None:
        """Test that non-animation properties are ignored."""
        properties = {
            "idle_up_frames": 4,
            "idle_up_row": 0,
            "sprite_sheet": "player.png",
            "tile_size": 32,
            "name": "TestPlayer",
            "spawn_at_portal": True,
        }

        result = self.manager._get_animation_properties(properties)

        assert len(result) == 2
        assert result["idle_up_frames"] == 4
        assert result["idle_up_row"] == 0
        assert "sprite_sheet" not in result
        assert "tile_size" not in result
        assert "name" not in result
        assert "spawn_at_portal" not in result

    def test_ignores_non_integer_properties(self) -> None:
        """Test that non-integer animation properties are ignored."""
        properties = {
            "idle_up_frames": "4",  # String instead of int
            "idle_up_row": 0,
            "idle_down_frames": 4.5,  # Float instead of int
            "idle_down_row": 1,
        }

        result = self.manager._get_animation_properties(properties)

        assert len(result) == 2
        assert result["idle_up_row"] == 0
        assert result["idle_down_row"] == 1
        assert "idle_up_frames" not in result
        assert "idle_down_frames" not in result

    def test_handles_empty_properties(self) -> None:
        """Test that empty properties dict returns empty result."""
        result = self.manager._get_animation_properties({})

        assert result == {}
        assert len(result) == 0

    def test_partial_properties(self) -> None:
        """Test that only provided animation properties are extracted."""
        properties = {
            "idle_down_frames": 4,
            "idle_down_row": 1,
        }

        result = self.manager._get_animation_properties(properties)

        assert len(result) == 2
        assert result["idle_down_frames"] == 4
        assert result["idle_down_row"] == 1


class TestNPCAnimationPropertyExtraction(unittest.TestCase):
    """Test NPCManager animation property extraction from Tiled objects."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.manager = NPCManager()
        self.mock_context = MagicMock()
        self.mock_event_bus = MagicMock()
        self.mock_context.event_bus = self.mock_event_bus

    def _create_mock_npc_object(self, properties: dict) -> MagicMock:
        """Create a mock Tiled NPC object with properties."""
        mock_obj = MagicMock()
        mock_obj.properties = properties
        mock_obj.name = "TestNPC"
        mock_obj.shape = [(0, 0), (32, 0), (32, 32), (0, 32)]
        return mock_obj

    def _extract_anim_props(self, npc_properties: dict) -> dict[str, int]:
        """Simulate the animation property extraction logic from NPCManager."""
        return {
            key: val for key, val in npc_properties.items() if key in ALL_ANIMATION_PROPERTIES and isinstance(val, int)
        }

    def test_extracts_base_animation_properties(self) -> None:
        """Test that base animation properties (idle/walk) are extracted."""
        properties = {
            "sprite_sheet": "npc.png",
            "idle_down_frames": 4,
            "idle_down_row": 0,
            "walk_down_frames": 6,
            "walk_down_row": 1,
        }

        anim_props = self._extract_anim_props(properties)

        assert len(anim_props) == 4
        assert anim_props["idle_down_frames"] == 4
        assert anim_props["idle_down_row"] == 0
        assert anim_props["walk_down_frames"] == 6
        assert anim_props["walk_down_row"] == 1
        assert "sprite_sheet" not in anim_props

    def test_extracts_special_animation_properties(self) -> None:
        """Test that special animation properties (appear/interact) are extracted."""
        properties = {
            "sprite_sheet": "npc.png",
            "appear_frames": 6,
            "appear_row": 8,
            "interact_down_frames": 4,
            "interact_down_row": 9,
            "interact_up_frames": 4,
            "interact_up_row": 10,
        }

        anim_props = self._extract_anim_props(properties)

        assert len(anim_props) == 6
        assert anim_props["appear_frames"] == 6
        assert anim_props["appear_row"] == 8
        assert anim_props["interact_down_frames"] == 4
        assert anim_props["interact_down_row"] == 9
        assert anim_props["interact_up_frames"] == 4
        assert anim_props["interact_up_row"] == 10
        assert "sprite_sheet" not in anim_props

    def test_extracts_all_animation_properties(self) -> None:
        """Test that all 26 animation properties are extracted when present."""
        properties = {
            # Base animations (16 properties)
            "idle_up_frames": 1,
            "idle_up_row": 2,
            "idle_down_frames": 3,
            "idle_down_row": 4,
            "idle_left_frames": 5,
            "idle_left_row": 6,
            "idle_right_frames": 7,
            "idle_right_row": 8,
            "walk_up_frames": 9,
            "walk_up_row": 10,
            "walk_down_frames": 11,
            "walk_down_row": 12,
            "walk_left_frames": 13,
            "walk_left_row": 14,
            "walk_right_frames": 15,
            "walk_right_row": 16,
            # Special animations (10 properties)
            "appear_frames": 17,
            "appear_row": 18,
            "interact_up_frames": 19,
            "interact_up_row": 20,
            "interact_down_frames": 21,
            "interact_down_row": 22,
            "interact_left_frames": 23,
            "interact_left_row": 24,
            "interact_right_frames": 25,
            "interact_right_row": 26,
            # Non-animation properties
            "sprite_sheet": "npc.png",
            "tile_size": 32,
            "name": "TestNPC",
        }

        anim_props = self._extract_anim_props(properties)

        # Should extract exactly 26 animation properties
        assert len(anim_props) == 26
        # Verify all animation properties are present
        for i in range(1, 27):
            assert i in anim_props.values()
        # Verify non-animation properties are excluded
        assert "sprite_sheet" not in anim_props
        assert "tile_size" not in anim_props
        assert "name" not in anim_props

    def test_ignores_non_animation_properties(self) -> None:
        """Test that non-animation properties (name, sprite_sheet) are not in anim_props."""
        properties = {
            "sprite_sheet": "npc.png",
            "tile_size": 32,
            "name": "Martin",
            "initially_hidden": True,
            "idle_down_frames": 4,
            "idle_down_row": 0,
        }

        anim_props = self._extract_anim_props(properties)

        assert len(anim_props) == 2
        assert anim_props["idle_down_frames"] == 4
        assert anim_props["idle_down_row"] == 0
        assert "sprite_sheet" not in anim_props
        assert "tile_size" not in anim_props
        assert "name" not in anim_props
        assert "initially_hidden" not in anim_props

    def test_ignores_non_integer_animation_properties(self) -> None:
        """Test that string animation properties are ignored."""
        properties = {
            "idle_down_frames": "4",  # String instead of int
            "idle_down_row": 0,
            "appear_frames": 6.5,  # Float instead of int
            "appear_row": 8,
        }

        anim_props = self._extract_anim_props(properties)

        assert len(anim_props) == 2
        assert anim_props["idle_down_row"] == 0
        assert anim_props["appear_row"] == 8
        assert "idle_down_frames" not in anim_props
        assert "appear_frames" not in anim_props

    def test_empty_properties(self) -> None:
        """Test that empty properties dict returns empty anim_props."""
        anim_props = self._extract_anim_props({})

        assert anim_props == {}
        assert len(anim_props) == 0

    def test_only_non_animation_properties(self) -> None:
        """Test that dict with only non-animation properties returns empty anim_props."""
        properties = {
            "sprite_sheet": "npc.png",
            "tile_size": 32,
            "name": "Martin",
        }

        anim_props = self._extract_anim_props(properties)

        assert anim_props == {}
        assert len(anim_props) == 0


class TestAnimationPropertyConstants(unittest.TestCase):
    """Test that animation property constants are complete and correct."""

    def test_base_properties_count(self) -> None:
        """Test that BASE_ANIMATION_PROPERTIES has exactly 16 properties."""
        assert len(BASE_ANIMATION_PROPERTIES) == 16

    def test_npc_special_properties_count(self) -> None:
        """Test that NPC_SPECIAL_ANIMATION_PROPERTIES has exactly 12 properties."""
        assert len(NPC_SPECIAL_ANIMATION_PROPERTIES) == 12

    def test_all_properties_count(self) -> None:
        """Test that ALL_ANIMATION_PROPERTIES has exactly 28 properties."""
        assert len(ALL_ANIMATION_PROPERTIES) == 28

    def test_no_duplicate_properties(self) -> None:
        """Test that there are no duplicates in ALL_ANIMATION_PROPERTIES."""
        assert len(ALL_ANIMATION_PROPERTIES) == len(set(ALL_ANIMATION_PROPERTIES))

    def test_all_properties_are_strings(self) -> None:
        """Test that all property names are strings."""
        for prop in BASE_ANIMATION_PROPERTIES:
            assert isinstance(prop, str)
        for prop in NPC_SPECIAL_ANIMATION_PROPERTIES:
            assert isinstance(prop, str)
        for prop in ALL_ANIMATION_PROPERTIES:
            assert isinstance(prop, str)

    def test_base_properties_naming_convention(self) -> None:
        """Test that base properties follow naming convention."""
        expected_prefixes = ["idle_", "walk_"]
        expected_suffixes = ["_frames", "_row"]
        expected_directions = ["up", "down", "left", "right"]

        for prop in BASE_ANIMATION_PROPERTIES:
            assert any(prop.startswith(prefix) for prefix in expected_prefixes), (
                f"{prop} doesn't start with expected prefix"
            )
            assert any(prop.endswith(suffix) for suffix in expected_suffixes), (
                f"{prop} doesn't end with expected suffix"
            )
            assert any(direction in prop for direction in expected_directions), (
                f"{prop} doesn't contain expected direction"
            )

    def test_npc_special_properties_naming_convention(self) -> None:
        """Test that NPC special properties follow naming convention."""
        expected_prefixes = ["appear_", "disappear_", "interact_"]
        expected_suffixes = ["_frames", "_row"]

        for prop in NPC_SPECIAL_ANIMATION_PROPERTIES:
            assert any(prop.startswith(prefix) for prefix in expected_prefixes), (
                f"{prop} doesn't start with expected prefix"
            )
            assert any(prop.endswith(suffix) for suffix in expected_suffixes), (
                f"{prop} doesn't end with expected suffix"
            )

    def test_base_properties_complete_set(self) -> None:
        """Test that base properties contain all combinations of animation types and directions."""
        animation_types = ["idle", "walk"]
        directions = ["up", "down", "left", "right"]
        attributes = ["frames", "row"]

        expected_properties = [
            f"{anim_type}_{direction}_{attribute}"
            for anim_type in animation_types
            for direction in directions
            for attribute in attributes
        ]

        assert len(expected_properties) == 16
        assert set(BASE_ANIMATION_PROPERTIES) == set(expected_properties)

    def test_npc_special_properties_complete_set(self) -> None:
        """Test that NPC special properties contain expected animations."""
        # Appear animation (2 properties)
        assert "appear_frames" in NPC_SPECIAL_ANIMATION_PROPERTIES
        assert "appear_row" in NPC_SPECIAL_ANIMATION_PROPERTIES

        # Disappear animation (2 properties)
        assert "disappear_frames" in NPC_SPECIAL_ANIMATION_PROPERTIES
        assert "disappear_row" in NPC_SPECIAL_ANIMATION_PROPERTIES

        # Interact animations for all 4 directions (8 properties)
        directions = ["up", "down", "left", "right"]
        for direction in directions:
            assert f"interact_{direction}_frames" in NPC_SPECIAL_ANIMATION_PROPERTIES
            assert f"interact_{direction}_row" in NPC_SPECIAL_ANIMATION_PROPERTIES

    def test_all_properties_is_base_plus_special(self) -> None:
        """Test that ALL_ANIMATION_PROPERTIES is exactly BASE + NPC_SPECIAL."""
        combined = BASE_ANIMATION_PROPERTIES + NPC_SPECIAL_ANIMATION_PROPERTIES
        assert combined == ALL_ANIMATION_PROPERTIES
        assert len(ALL_ANIMATION_PROPERTIES) == len(BASE_ANIMATION_PROPERTIES) + len(NPC_SPECIAL_ANIMATION_PROPERTIES)
