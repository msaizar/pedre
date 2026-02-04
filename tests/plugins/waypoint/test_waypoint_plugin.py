"""Unit tests for WaypointPlugin in src/pedre/plugins/waypoint/plugin.py."""

import unittest
from unittest.mock import MagicMock

from pedre.plugins.waypoint.plugin import WaypointPlugin


class TestWaypointPlugin(unittest.TestCase):
    """Test Suite for WaypointPlugin."""

    def setUp(self) -> None:
        """Set up the WaypointPlugin and mock context."""
        self.plugin = WaypointPlugin()
        self.mock_context = MagicMock()

    def test_initialization(self) -> None:
        """Test proper initialization of the plugin."""
        plugin = WaypointPlugin()
        assert plugin.name == "waypoint"
        assert plugin.dependencies == []
        assert plugin.waypoints == {}

    def test_setup(self) -> None:
        """Test setup assigns context."""
        self.plugin.setup(self.mock_context)
        assert self.plugin.context == self.mock_context

    def test_reset(self) -> None:
        """Test reset clears waypoints."""
        self.plugin.waypoints = {"spawn": (10, 20), "portal": (30, 40)}
        self.plugin.reset()
        assert self.plugin.waypoints == {}

    def test_get_waypoints_empty(self) -> None:
        """Test get_waypoints returns empty dict initially."""
        result = self.plugin.get_waypoints()
        assert result == {}

    def test_get_waypoints_with_data(self) -> None:
        """Test get_waypoints returns waypoints dictionary."""
        self.plugin.waypoints = {"spawn": (10, 20), "exit": (50, 60)}
        result = self.plugin.get_waypoints()
        assert result == {"spawn": (10, 20), "exit": (50, 60)}

    def test_get_waypoint_found(self) -> None:
        """Test get_waypoint returns position when found."""
        self.plugin.waypoints = {"spawn": (10, 20), "exit": (50, 60)}
        result = self.plugin.get_waypoint("spawn")
        assert result == (10, 20)

    def test_get_waypoint_not_found(self) -> None:
        """Test get_waypoint returns None when not found."""
        self.plugin.waypoints = {"spawn": (10, 20)}
        result = self.plugin.get_waypoint("nonexistent")
        assert result is None

    def test_load_from_tiled_no_waypoint_layer(self) -> None:
        """Test load_from_tiled when no Waypoints layer exists."""
        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert self.plugin.waypoints == {}

    def test_load_from_tiled_empty_waypoint_layer(self) -> None:
        """Test load_from_tiled with empty Waypoints layer."""
        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": []}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert self.plugin.waypoints == {}

    def test_load_from_tiled_valid_waypoint(self) -> None:
        """Test load_from_tiled with a valid waypoint."""
        # Create mock waypoint with 32x32 tile size
        mock_waypoint = MagicMock()
        mock_waypoint.name = "spawn"
        mock_waypoint.shape = [64.0, 96.0]  # Pixel coordinates

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # With TILE_SIZE = 32, (64, 96) -> tile (2, 3)
        assert "spawn" in self.plugin.waypoints
        assert self.plugin.waypoints["spawn"] == (2, 3)

    def test_load_from_tiled_multiple_waypoints(self) -> None:
        """Test load_from_tiled with multiple waypoints."""
        mock_waypoint1 = MagicMock()
        mock_waypoint1.name = "spawn"
        mock_waypoint1.shape = [32.0, 32.0]

        mock_waypoint2 = MagicMock()
        mock_waypoint2.name = "exit"
        mock_waypoint2.shape = [128.0, 64.0]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint1, mock_waypoint2]}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # With TILE_SIZE = 32:
        # (32, 32) -> tile (1, 1)
        # (128, 64) -> tile (4, 2)
        assert len(self.plugin.waypoints) == 2
        assert self.plugin.waypoints["spawn"] == (1, 1)
        assert self.plugin.waypoints["exit"] == (4, 2)

    def test_load_from_tiled_waypoint_without_name(self) -> None:
        """Test load_from_tiled skips waypoint without name."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = None
        mock_waypoint.shape = [64.0, 64.0]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert self.plugin.waypoints == {}

    def test_load_from_tiled_waypoint_empty_name(self) -> None:
        """Test load_from_tiled skips waypoint with empty name."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = ""
        mock_waypoint.shape = [64.0, 64.0]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert self.plugin.waypoints == {}

    def test_load_from_tiled_waypoint_invalid_shape_none(self) -> None:
        """Test load_from_tiled skips waypoint with None shape."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = "spawn"
        mock_waypoint.shape = None

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert self.plugin.waypoints == {}

    def test_load_from_tiled_waypoint_invalid_shape_not_list(self) -> None:
        """Test load_from_tiled skips waypoint with non-list shape."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = "spawn"
        mock_waypoint.shape = "invalid"

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert self.plugin.waypoints == {}

    def test_load_from_tiled_waypoint_invalid_shape_too_short(self) -> None:
        """Test load_from_tiled skips waypoint with shape < 2 elements."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = "spawn"
        mock_waypoint.shape = [64.0]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert self.plugin.waypoints == {}

    def test_load_from_tiled_waypoint_non_numeric_x(self) -> None:
        """Test load_from_tiled skips waypoint with non-numeric x coordinate."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = "spawn"
        mock_waypoint.shape = ["invalid", 64.0]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert self.plugin.waypoints == {}

    def test_load_from_tiled_waypoint_non_numeric_y(self) -> None:
        """Test load_from_tiled skips waypoint with non-numeric y coordinate."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = "spawn"
        mock_waypoint.shape = [64.0, "invalid"]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert self.plugin.waypoints == {}

    def test_load_from_tiled_waypoint_integer_coordinates(self) -> None:
        """Test load_from_tiled handles integer coordinates."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = "spawn"
        mock_waypoint.shape = [64, 96]  # Integers instead of floats

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert "spawn" in self.plugin.waypoints
        assert self.plugin.waypoints["spawn"] == (2, 3)

    def test_load_from_tiled_waypoint_at_origin(self) -> None:
        """Test load_from_tiled with waypoint at origin."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = "origin"
        mock_waypoint.shape = [0.0, 0.0]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert "origin" in self.plugin.waypoints
        assert self.plugin.waypoints["origin"] == (0, 0)

    def test_load_from_tiled_waypoint_floating_point_conversion(self) -> None:
        """Test load_from_tiled correctly converts to tile coordinates."""
        # Test that 63.9 pixels rounds down to tile 1 (floor division)
        mock_waypoint = MagicMock()
        mock_waypoint.name = "test"
        mock_waypoint.shape = [63.9, 31.9]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # 63.9 // 32 = 1, 31.9 // 32 = 0
        assert self.plugin.waypoints["test"] == (1, 0)

    def test_load_from_tiled_clears_previous_waypoints(self) -> None:
        """Test load_from_tiled clears previous waypoints before loading new ones."""
        # Set initial waypoints
        self.plugin.waypoints = {"old": (1, 1)}

        mock_waypoint = MagicMock()
        mock_waypoint.name = "new"
        mock_waypoint.shape = [64.0, 64.0]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Old waypoint should be gone
        assert "old" not in self.plugin.waypoints
        assert "new" in self.plugin.waypoints

    def test_load_from_tiled_partial_failures(self) -> None:
        """Test load_from_tiled loads valid waypoints even if some fail."""
        mock_waypoint_valid = MagicMock()
        mock_waypoint_valid.name = "valid"
        mock_waypoint_valid.shape = [64.0, 64.0]

        mock_waypoint_invalid = MagicMock()
        mock_waypoint_invalid.name = "invalid"
        mock_waypoint_invalid.shape = None

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint_invalid, mock_waypoint_valid]}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Only valid waypoint should be loaded
        assert len(self.plugin.waypoints) == 1
        assert "valid" in self.plugin.waypoints
        assert "invalid" not in self.plugin.waypoints

    def test_load_from_tiled_duplicate_waypoint_names(self) -> None:
        """Test load_from_tiled with duplicate waypoint names (later one wins)."""
        mock_waypoint1 = MagicMock()
        mock_waypoint1.name = "spawn"
        mock_waypoint1.shape = [32.0, 32.0]

        mock_waypoint2 = MagicMock()
        mock_waypoint2.name = "spawn"  # Same name
        mock_waypoint2.shape = [96.0, 96.0]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint1, mock_waypoint2]}
        mock_arcade_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Last waypoint with duplicate name should win
        assert len(self.plugin.waypoints) == 1
        assert self.plugin.waypoints["spawn"] == (3, 3)  # 96 // 32 = 3


if __name__ == "__main__":
    unittest.main()
