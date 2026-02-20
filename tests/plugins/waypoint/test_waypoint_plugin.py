"""Unit tests for WaypointPlugin in src/pedre/plugins/waypoint/plugin.py."""

from unittest.mock import MagicMock

import pytest

from pedre.plugins.waypoint.plugin import WaypointPlugin


@pytest.fixture
def plugin() -> WaypointPlugin:
    """Fixture to provide a clean WaypointPlugin instance."""
    return WaypointPlugin()


@pytest.fixture
def mock_context() -> MagicMock:
    """Fixture to provide a mock GameContext."""
    return MagicMock()


class TestWaypointPlugin:
    """Test Suite for WaypointPlugin."""

    @pytest.fixture(autouse=True)
    def setup_context(self, plugin: WaypointPlugin, mock_context: MagicMock) -> None:
        """Set up the WaypointPlugin and mock context automatically for tests."""
        plugin.setup(mock_context)

    def test_initialization(self, plugin: WaypointPlugin) -> None:
        """Test proper initialization of the plugin."""
        assert plugin.name == "waypoint"
        assert plugin.dependencies == []
        assert plugin.waypoints == {}

    def test_setup(self, plugin: WaypointPlugin, mock_context: MagicMock) -> None:
        """Test setup assigns context."""
        assert plugin.context == mock_context

    def test_reset(self, plugin: WaypointPlugin) -> None:
        """Test reset clears waypoints."""
        plugin.waypoints = {"spawn": (10, 20), "portal": (30, 40)}
        plugin.reset()
        assert plugin.waypoints == {}

    def test_get_waypoints_empty(self, plugin: WaypointPlugin) -> None:
        """Test get_waypoints returns empty dict initially."""
        result = plugin.get_waypoints()
        assert result == {}

    def test_get_waypoints_with_data(self, plugin: WaypointPlugin) -> None:
        """Test get_waypoints returns waypoints dictionary."""
        plugin.waypoints = {"spawn": (10, 20), "exit": (50, 60)}
        result = plugin.get_waypoints()
        assert result == {"spawn": (10, 20), "exit": (50, 60)}

    def test_get_waypoint_found(self, plugin: WaypointPlugin) -> None:
        """Test get_waypoint returns position when found."""
        plugin.waypoints = {"spawn": (10, 20), "exit": (50, 60)}
        result = plugin.get_waypoint("spawn")
        assert result == (10, 20)

    def test_get_waypoint_not_found(self, plugin: WaypointPlugin) -> None:
        """Test get_waypoint returns None when not found."""
        plugin.waypoints = {"spawn": (10, 20)}
        result = plugin.get_waypoint("nonexistent")
        assert result is None

    def test_load_from_tiled_no_waypoint_layer(self, plugin: WaypointPlugin) -> None:
        """Test load_from_tiled when no Waypoints layer exists."""
        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {}
        mock_arcade_scene = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert plugin.waypoints == {}

    def test_load_from_tiled_empty_waypoint_layer(self, plugin: WaypointPlugin) -> None:
        """Test load_from_tiled with empty Waypoints layer."""
        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": []}
        mock_arcade_scene = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert plugin.waypoints == {}

    def test_load_from_tiled_valid_waypoint(self, plugin: WaypointPlugin) -> None:
        """Test load_from_tiled with a valid waypoint."""
        # Create mock waypoint with 32x32 tile size
        mock_waypoint = MagicMock()
        mock_waypoint.name = "spawn"
        mock_waypoint.shape = [64.0, 96.0]  # Pixel coordinates

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Waypoints are now stored as pixel coordinates
        assert "spawn" in plugin.waypoints
        assert plugin.waypoints["spawn"] == (64.0, 96.0)

    def test_load_from_tiled_multiple_waypoints(self, plugin: WaypointPlugin) -> None:
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

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Waypoints are now stored as pixel coordinates
        assert len(plugin.waypoints) == 2
        assert plugin.waypoints["spawn"] == (32.0, 32.0)
        assert plugin.waypoints["exit"] == (128.0, 64.0)

    def test_load_from_tiled_waypoint_without_name(self, plugin: WaypointPlugin) -> None:
        """Test load_from_tiled skips waypoint without name."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = None
        mock_waypoint.shape = [64.0, 64.0]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert plugin.waypoints == {}

    def test_load_from_tiled_waypoint_empty_name(self, plugin: WaypointPlugin) -> None:
        """Test load_from_tiled skips waypoint with empty name."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = ""
        mock_waypoint.shape = [64.0, 64.0]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert plugin.waypoints == {}

    def test_load_from_tiled_waypoint_invalid_shape_none(self, plugin: WaypointPlugin) -> None:
        """Test load_from_tiled skips waypoint with None shape."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = "spawn"
        mock_waypoint.shape = None

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert plugin.waypoints == {}

    def test_load_from_tiled_waypoint_invalid_shape_not_list(self, plugin: WaypointPlugin) -> None:
        """Test load_from_tiled skips waypoint with non-list shape."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = "spawn"
        mock_waypoint.shape = "invalid"

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert plugin.waypoints == {}

    def test_load_from_tiled_waypoint_invalid_shape_too_short(self, plugin: WaypointPlugin) -> None:
        """Test load_from_tiled skips waypoint with shape < 2 elements."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = "spawn"
        mock_waypoint.shape = [64.0]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert plugin.waypoints == {}

    def test_load_from_tiled_waypoint_non_numeric_x(self, plugin: WaypointPlugin) -> None:
        """Test load_from_tiled skips waypoint with non-numeric x coordinate."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = "spawn"
        mock_waypoint.shape = ["invalid", 64.0]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert plugin.waypoints == {}

    def test_load_from_tiled_waypoint_non_numeric_y(self, plugin: WaypointPlugin) -> None:
        """Test load_from_tiled skips waypoint with non-numeric y coordinate."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = "spawn"
        mock_waypoint.shape = [64.0, "invalid"]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert plugin.waypoints == {}

    def test_load_from_tiled_waypoint_integer_coordinates(self, plugin: WaypointPlugin) -> None:
        """Test load_from_tiled handles integer coordinates."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = "spawn"
        mock_waypoint.shape = [64, 96]  # Integers instead of floats

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert "spawn" in plugin.waypoints
        assert plugin.waypoints["spawn"] == (64.0, 96.0)

    def test_load_from_tiled_waypoint_at_origin(self, plugin: WaypointPlugin) -> None:
        """Test load_from_tiled with waypoint at origin."""
        mock_waypoint = MagicMock()
        mock_waypoint.name = "origin"
        mock_waypoint.shape = [0.0, 0.0]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert "origin" in plugin.waypoints
        assert plugin.waypoints["origin"] == (0.0, 0.0)

    def test_load_from_tiled_waypoint_floating_point_precision(self, plugin: WaypointPlugin) -> None:
        """Test load_from_tiled correctly preserves floating point coordinates."""
        # Test that floating point pixel coordinates are preserved
        mock_waypoint = MagicMock()
        mock_waypoint.name = "test"
        mock_waypoint.shape = [63.9, 31.9]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Waypoints are now stored as pixel coordinates (not tiles)
        assert plugin.waypoints["test"] == (63.9, 31.9)

    def test_load_from_tiled_clears_previous_waypoints(self, plugin: WaypointPlugin) -> None:
        """Test load_from_tiled clears previous waypoints before loading new ones."""
        # Set initial waypoints
        plugin.waypoints = {"old": (1, 1)}

        mock_waypoint = MagicMock()
        mock_waypoint.name = "new"
        mock_waypoint.shape = [64.0, 64.0]

        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {"Waypoints": [mock_waypoint]}
        mock_arcade_scene = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Old waypoint should be gone
        assert "old" not in plugin.waypoints
        assert "new" in plugin.waypoints

    def test_load_from_tiled_partial_failures(self, plugin: WaypointPlugin) -> None:
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

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Only valid waypoint should be loaded
        assert len(plugin.waypoints) == 1
        assert "valid" in plugin.waypoints
        assert "invalid" not in plugin.waypoints

    def test_load_from_tiled_duplicate_waypoint_names(self, plugin: WaypointPlugin) -> None:
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

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Last waypoint with duplicate name should win
        assert len(plugin.waypoints) == 1
        assert plugin.waypoints["spawn"] == (96.0, 96.0)
