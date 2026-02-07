"""Unit tests for PathfindingPlugin in src/pedre/plugins/pathfinding/plugin.py."""

import logging
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

        # End pixel: center of tile (2, 0)
        end_x = 2 * self.tile_size + self.tile_size / 2
        end_y = 0 * self.tile_size + self.tile_size / 2

        path = self.plugin.find_path(start_x, start_y, end_x, end_y)

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

        # End position in pixels (tile 2,0)
        end_x = 2 * self.tile_size + self.tile_size / 2
        end_y = 0 * self.tile_size + self.tile_size / 2
        path = self.plugin.find_path(start_x, start_y, end_x, end_y)

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

        # Target tile is (2,0) in pixels
        # Normal pathfinding should fail (all neighbors blocked).
        # Retry with passthrough should allow passing (1,0) NPC.
        end_x = 2 * self.tile_size + self.tile_size / 2
        end_y = 0 * self.tile_size + self.tile_size / 2

        path = self.plugin.find_path(start_x, start_y, end_x, end_y)

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

        # Target position in pixels (tile 5,5)
        end_x = 5 * self.tile_size + self.tile_size / 2
        end_y = 5 * self.tile_size + self.tile_size / 2
        path = self.plugin.find_path(start_x, start_y, end_x, end_y)

        assert len(path) == 0
        assert isinstance(path, deque)

    def test_cleanup(self) -> None:
        """Test cleanup method logs correctly."""
        with self.assertLogs("pedre.plugins.pathfinding.plugin", level=logging.DEBUG) as log_context:
            self.plugin.cleanup()

        assert any("PathfindingPlugin cleanup complete" in message for message in log_context.output)

    def test_find_path_with_exclude_sprites_in_retry(self) -> None:
        """Test retry logic extends exclude_sprites with NPCs."""
        # Create an NPC at (1,0)
        npc = MagicMock()
        npc.center_x = 1 * self.tile_size + self.tile_size / 2
        npc.center_y = 0 * self.tile_size + self.tile_size / 2
        npc.width = self.tile_size
        npc.height = self.tile_size
        npc.properties = {"name": "guard"}
        self.mock_wall_list.append(npc)

        # Create a wall at (0,1)
        wall = MagicMock()
        wall.center_x = 0 * self.tile_size + self.tile_size / 2
        wall.center_y = 1 * self.tile_size + self.tile_size / 2
        wall.width = self.tile_size
        wall.height = self.tile_size
        wall.properties = {}
        self.mock_wall_list.append(wall)

        # Create an additional exclude sprite (not the moving sprite)
        extra_exclude = MagicMock()
        extra_exclude.center_x = -1 * self.tile_size + self.tile_size / 2
        extra_exclude.center_y = 0 * self.tile_size + self.tile_size / 2
        extra_exclude.width = self.tile_size
        extra_exclude.height = self.tile_size

        # Surround the start position with walls except for the path through NPC
        for dx, dy in [(0, -1), (-1, 0)]:
            w = MagicMock()
            w.center_x = dx * self.tile_size + self.tile_size / 2
            w.center_y = dy * self.tile_size + self.tile_size / 2
            w.width = self.tile_size
            w.height = self.tile_size
            w.properties = {}
            self.mock_wall_list.append(w)

        start_x = self.tile_size / 2
        start_y = self.tile_size / 2

        # Target tile is (2,0)
        end_x = 2 * self.tile_size + self.tile_size / 2
        end_y = 0 * self.tile_size + self.tile_size / 2

        # Call with exclude_sprites parameter
        path = self.plugin.find_path(start_x, start_y, end_x, end_y, exclude_sprites=[extra_exclude])

        # Should succeed due to NPC passthrough (line 240 is executed)
        assert len(path) > 0

    def test_find_path_no_retry_when_no_wall_list(self) -> None:
        """Test that retry doesn't happen when wall_list is None and no path found."""
        # Set wall_list to None
        self.mock_scene_plugin.get_wall_list.return_value = None

        start_x = self.tile_size / 2
        start_y = self.tile_size / 2

        # This won't matter since all tiles are walkable with no wall_list
        # But trying to path from the same tile should return empty path
        end_x = self.tile_size / 2
        end_y = self.tile_size / 2

        path = self.plugin.find_path(start_x, start_y, end_x, end_y)

        # Path should be empty since start == end
        assert len(path) == 0
        assert isinstance(path, deque)

    def test_find_path_with_blocked_end_tile(self) -> None:
        """Test warning log when end tile is blocked."""
        # Create a small bounded area with walls
        # Start at (1,1), end at (3,1) which will be blocked
        # Create walls forming a small box to limit search space

        # Create outer walls to bound the search space (0-4 in x and y)
        for x in range(-1, 6):
            for y in range(-1, 6):
                # Create walls on the perimeter
                if x in (-1, 5) or y in (-1, 5):
                    wall = MagicMock()
                    wall.center_x = x * self.tile_size + self.tile_size / 2
                    wall.center_y = y * self.tile_size + self.tile_size / 2
                    wall.width = self.tile_size
                    wall.height = self.tile_size
                    wall.properties = {}
                    self.mock_wall_list.append(wall)

        # Place wall at target position (3, 1)
        target_wall = MagicMock()
        target_wall.center_x = 3 * self.tile_size + self.tile_size / 2
        target_wall.center_y = 1 * self.tile_size + self.tile_size / 2
        target_wall.width = self.tile_size
        target_wall.height = self.tile_size
        target_wall.properties = {}
        self.mock_wall_list.append(target_wall)

        # Start at (1, 1)
        start_x = 1 * self.tile_size + self.tile_size / 2
        start_y = 1 * self.tile_size + self.tile_size / 2

        # Target at (3, 1) - blocked
        end_x = 3 * self.tile_size + self.tile_size / 2
        end_y = 1 * self.tile_size + self.tile_size / 2

        with self.assertLogs("pedre.plugins.pathfinding.plugin", level=logging.WARNING) as log_context:
            path = self.plugin.find_path(start_x, start_y, end_x, end_y)

        # Check that warning was logged (line 303)
        assert any("End tile blocked at" in message for message in log_context.output)
        # Path should still be empty since end is blocked
        assert len(path) == 0


if __name__ == "__main__":
    unittest.main()
