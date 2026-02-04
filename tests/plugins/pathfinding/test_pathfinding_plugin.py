"""Unit tests for PathfindingPlugin in src/pedre/plugins/pathfinding/plugin.py."""

import unittest
from collections import deque
from unittest.mock import MagicMock

from pedre.conf import settings
from pedre.plugins.pathfinding.plugin import PathfindingPlugin


class TestPathfindingPlugin(unittest.TestCase):
    """Test Suite for PathfindingPlugin."""

    def setUp(self) -> None:
        """Set up the PathfindingPlugin and mock context."""
        self.plugin = PathfindingPlugin()
        self.mock_context = MagicMock()
        self.plugin.setup(self.mock_context)

        # Default tile size (from settings, or mocked if needed)
        self.tile_size = settings.TILE_SIZE

        # Mock scene plugin and wall list
        self.mock_scene_plugin = self.mock_context.scene_plugin
        self.mock_wall_list = []
        self.mock_scene_plugin.get_wall_list.return_value = self.mock_wall_list

    def test_initialization(self) -> None:
        """Test proper initialization of the plugin."""
        assert self.plugin.name == "pathfinding"
        assert self.plugin.tile_size == settings.TILE_SIZE
        assert self.plugin.context == self.mock_context

    def test_is_tile_walkable_no_walls(self) -> None:
        """Test walkability when there are no walls."""
        self.mock_scene_plugin.get_wall_list.return_value = None
        assert self.plugin.is_tile_walkable(10, 10) is True

        self.mock_scene_plugin.get_wall_list.return_value = []
        assert self.plugin.is_tile_walkable(10, 10) is True

    def test_is_tile_walkable_collision(self) -> None:
        """Test collision detection with walls."""
        # Create a wall sprite at tile (5, 5)
        wall = MagicMock()
        wall.center_x = 5 * self.tile_size + self.tile_size / 2
        wall.center_y = 5 * self.tile_size + self.tile_size / 2
        wall.width = self.tile_size
        wall.height = self.tile_size
        self.mock_wall_list.append(wall)

        # Check collision at (5, 5) -> Should be False (blocked)
        assert self.plugin.is_tile_walkable(5, 5) is False

        # Check collision at (4, 5) -> Should be True (free)
        assert self.plugin.is_tile_walkable(4, 5) is True

    def test_is_tile_walkable_exclusions(self) -> None:
        """Test exclusion of specific sprites from collision check."""
        wall = MagicMock()
        wall.center_x = 5 * self.tile_size + self.tile_size / 2
        wall.center_y = 5 * self.tile_size + self.tile_size / 2
        wall.width = self.tile_size
        wall.height = self.tile_size
        self.mock_wall_list.append(wall)

        # Normally blocked
        assert self.plugin.is_tile_walkable(5, 5) is False

        # Excluded single sprite
        assert self.plugin.is_tile_walkable(5, 5, exclude_sprite=wall) is True

        # Excluded list
        assert self.plugin.is_tile_walkable(5, 5, exclude_sprites=[wall]) is True

    def test_find_path_simple(self) -> None:
        """Test finding a simple straight path."""
        # Path from (0,0) to (2,0)
        # Start pixel: center of (0,0)
        start_x = self.tile_size / 2
        start_y = self.tile_size / 2

        # End tile: (2, 0)
        end_tile_x = 2
        end_tile_y = 0

        path = self.plugin.find_path(start_x, start_y, end_tile_x, end_tile_y)

        # Expected path tiles: (1,0), (2,0) -> Converted to pixels
        assert len(path) == 2

        p1 = path[0]  # Tile (1,0)
        assert p1 == (1 * self.tile_size + self.tile_size / 2, 0 * self.tile_size + self.tile_size / 2)

        p2 = path[1]  # Tile (2,0)
        assert p2 == (2 * self.tile_size + self.tile_size / 2, 0 * self.tile_size + self.tile_size / 2)

    def test_find_path_obstacle(self) -> None:
        """Test pathfinding around an obstacle."""
        # Block tile (1, 0)
        wall = MagicMock()
        wall.center_x = 1 * self.tile_size + self.tile_size / 2
        wall.center_y = 0 * self.tile_size + self.tile_size / 2
        wall.width = self.tile_size
        wall.height = self.tile_size
        self.mock_wall_list.append(wall)

        # Path from (0,0) to (2,0)
        # Should go around: (0,0) -> (0,1) -> (1,1) -> (2,1) -> (2,0) OR similar
        # A* might choose simplest valid path around
        start_x = self.tile_size / 2
        start_y = self.tile_size / 2

        path = self.plugin.find_path(start_x, start_y, 2, 0)

        assert len(path) > 2  # Must go around, so longer than direct path
        # Verify destination reached
        dest = path[-1]
        assert dest == (2 * self.tile_size + self.tile_size / 2, 0 * self.tile_size + self.tile_size / 2)

    def test_find_path_blocked_retry_passthrough(self) -> None:
        """Test retry logic with NPC passthrough when blocked."""
        # Surround (0,0) completely.
        # (1,0) is NPC.
        # Others are Walls.

        # NPC at (1,0)
        npc = MagicMock()
        npc.center_x = 1 * self.tile_size + self.tile_size / 2
        npc.center_y = 0 * self.tile_size + self.tile_size / 2
        npc.width = self.tile_size
        npc.height = self.tile_size
        npc.properties = {"name": "guard"}
        self.mock_wall_list.append(npc)

        # Walls at other neighbors: (0,1), (0,-1), (-1,0)
        for dx, dy in [(0, 1), (0, -1), (-1, 0)]:
            wall = MagicMock()
            wall.center_x = dx * self.tile_size + self.tile_size / 2
            wall.center_y = dy * self.tile_size + self.tile_size / 2
            wall.width = self.tile_size
            wall.height = self.tile_size
            wall.properties = {}
            self.mock_wall_list.append(wall)

        start_x = self.tile_size / 2
        start_y = self.tile_size / 2

        # Target tile is (2,0)
        # Normal pathfinding should fail (all neighbors blocked).
        # Retry with passthrough should allow passing (1,0) NPC.

        path = self.plugin.find_path(start_x, start_y, 2, 0)

        assert len(path) > 0
        p1 = path[0]
        expected = (1 * self.tile_size + self.tile_size / 2, 0 * self.tile_size + self.tile_size / 2)
        assert p1 == expected

    def test_no_path_possible(self) -> None:
        """Test that empty deque is returned when no path exists."""
        # Surround (0,0) completely with walls
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            wall = MagicMock()
            wall.center_x = dx * self.tile_size + self.tile_size / 2
            wall.center_y = dy * self.tile_size + self.tile_size / 2
            wall.width = self.tile_size
            wall.height = self.tile_size
            wall.properties = {}  # Ensure not treated as NPC
            self.mock_wall_list.append(wall)

        start_x = self.tile_size / 2
        start_y = self.tile_size / 2

        # Verify barriers are actually blocking
        assert self.plugin.is_tile_walkable(0, 1) is False, "Tile (0,1) should be blocked"

        path = self.plugin.find_path(start_x, start_y, 5, 5)

        assert len(path) == 0
        assert isinstance(path, deque)


if __name__ == "__main__":
    unittest.main()
