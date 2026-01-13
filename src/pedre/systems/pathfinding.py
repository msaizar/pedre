"""Pathfinding system using A* algorithm.

This module provides efficient pathfinding for NPCs and other game entities that need
to navigate around obstacles in the game world. It uses the A* algorithm with Manhattan
distance heuristic for optimal path calculation on a tile-based grid.

The pathfinding system consists of:
- PathfindingManager: Coordinates path calculation and collision detection
- A* algorithm implementation with tile-based navigation
- Automatic retry logic with NPC passthrough for blocked paths

Key features:
- Efficient A* pathfinding with priority queue optimization
- Tile-based collision detection against wall sprites
- Sprite exclusion system to ignore specific entities during pathfinding
- Automatic fallback to NPC passthrough when normal pathfinding fails
- Converts tile paths to pixel coordinates for smooth sprite movement

The manager maintains a reference to the game's wall_list (collision layer) and uses
it to determine which tiles are walkable. NPCs can be excluded from collision checks
to allow them to pathfind through each other when necessary.

Pathfinding workflow:
1. Convert start position (pixels) to tile coordinates
2. Use A* to find optimal tile path avoiding walls
3. Convert tile path back to pixel coordinates
4. Return path as deque for efficient pop operations during movement

Integration with other systems:
- NPCManager calls find_path when moving NPCs to waypoints
- MoveNPCAction triggers pathfinding via NPC manager
- Wall list is shared with the physics/collision system

Example usage:
    # Create pathfinding manager
    pathfinding = PathfindingManager(tile_size=32)
    pathfinding.set_wall_list(wall_sprite_list)

    # Find path from pixel position to tile coordinates
    path = pathfinding.find_path(
        start_x=player.center_x,
        start_y=player.center_y,
        end_tile_x=10,
        end_tile_y=15,
        exclude_sprite=npc_sprite
    )

    # Path is a deque of (x, y) pixel positions
    while path:
        next_pos = path.popleft()
        # Move sprite toward next_pos
"""

import logging
from collections import deque
from heapq import heappop, heappush
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import arcade

logger = logging.getLogger(__name__)


class PathfindingManager:
    """Manages pathfinding calculations using A* algorithm.

    The PathfindingManager provides efficient navigation for game entities across a
    tile-based grid world. It uses the A* search algorithm with Manhattan distance
    heuristic to find optimal paths while avoiding obstacles.

    The manager operates in two coordinate systems:
    - Pixel coordinates: World positions used by sprites (e.g., 320.0, 240.0)
    - Tile coordinates: Grid positions used for pathfinding (e.g., 10, 7)

    All pathfinding happens in tile space for efficiency, then results are converted
    back to pixel positions for sprite movement.

    Key responsibilities:
    - Calculate optimal paths between start and end positions
    - Check tile walkability using wall sprite collision detection
    - Exclude specific sprites from collision (e.g., the moving entity itself)
    - Automatic retry with NPC passthrough when paths are blocked

    The NPC passthrough feature allows NPCs to pathfind through each other when
    their direct path is blocked by other NPCs. This prevents permanent deadlocks
    where NPCs block each other's paths.

    Attributes:
        tile_size: Size of each tile in pixels (default 32).
        wall_list: SpriteList containing all collision objects (walls, NPCs, etc.).
    """

    def __init__(self, tile_size: int = 32) -> None:
        """Initialize the pathfinding manager.

        Creates a pathfinding manager for the given tile size. The wall_list must
        be set separately via set_wall_list() before pathfinding can be performed.

        Args:
            tile_size: Size of tiles in pixels (default 32). Must match the game's
                      tile map configuration.
        """
        self.tile_size = tile_size
        self.wall_list: arcade.SpriteList | None = None

    def set_wall_list(self, wall_list: arcade.SpriteList) -> None:
        """Set the wall list for collision detection.

        Configures which sprites should be considered as obstacles during pathfinding.
        The wall list typically includes:
        - Static wall tiles from the map
        - Obstacle objects (trees, rocks, furniture)
        - NPC sprites (can be excluded per-path via exclude_sprites)
        - Any other sprites that should block movement

        This method should be called once during game initialization, after the map
        and collision layers have been loaded.

        Args:
            wall_list: SpriteList containing all walls and obstacles. NPCs are often
                      included in this list but can be excluded during pathfinding.
        """
        self.wall_list = wall_list

    def is_tile_walkable(
        self,
        tile_x: int,
        tile_y: int,
        exclude_sprite: arcade.Sprite | None = None,
        exclude_sprites: list[arcade.Sprite] | None = None,
    ) -> bool:
        """Check if a tile position is walkable.

        Determines whether a given tile coordinate is free of obstacles. A tile is
        considered walkable if no sprites from the wall_list overlap with its center point.

        The exclusion system allows specific sprites to be ignored during the check:
        - exclude_sprite: Single sprite to ignore (typically the moving entity itself)
        - exclude_sprites: Multiple sprites to ignore (e.g., all NPCs during passthrough)

        This is essential for preventing entities from blocking their own paths and
        for implementing the NPC passthrough feature.

        Implementation details:
        - Converts tile coordinates to pixel center point
        - Checks collision using sprite bounding boxes (width/height)
        - Returns True if wall_list is not set (fail-safe behavior)

        Args:
            tile_x: Tile x coordinate in grid space.
            tile_y: Tile y coordinate in grid space.
            exclude_sprite: Single sprite to exclude from collision check, typically
                           the sprite that is moving.
            exclude_sprites: List of sprites to exclude from collision check, used
                            during NPC passthrough retry.

        Returns:
            True if the tile is walkable, False if blocked by any wall sprite.
        """
        if not self.wall_list:
            return True

        # Convert tile to pixel center
        pixel_x = tile_x * self.tile_size + self.tile_size / 2
        pixel_y = tile_y * self.tile_size + self.tile_size / 2

        # Build set of sprites to exclude for faster lookup
        excluded = set()
        if exclude_sprite:
            excluded.add(exclude_sprite)
        if exclude_sprites:
            excluded.update(exclude_sprites)

        # Check if any wall sprites overlap this position
        for wall in self.wall_list:
            if wall in excluded:
                continue

            dx = abs(wall.center_x - pixel_x)
            dy = abs(wall.center_y - pixel_y)

            if dx < (wall.width / 2) and dy < (wall.height / 2):
                return False

        return True

    def find_path(
        self,
        start_x: float,
        start_y: float,
        end_tile_x: int,
        end_tile_y: int,
        exclude_sprite: arcade.Sprite | None = None,
        exclude_sprites: list[arcade.Sprite] | None = None,
    ) -> deque[tuple[float, float]]:
        """Find a path using A* pathfinding with automatic retry logic.

        Calculates the optimal path from a pixel position to a target tile using the
        A* algorithm. If the initial pathfinding fails (typically due to NPC blocking),
        automatically retries with NPC passthrough enabled.

        The two-phase approach:
        1. First attempt: Normal pathfinding with only specified exclusions
        2. Second attempt: Retry with all NPCs excluded if first attempt fails

        This prevents permanent deadlocks where NPCs block each other's paths. The
        NPC passthrough allows entities to pathfind "through" NPCs, with the expectation
        that NPCs will move out of the way before collision occurs.

        The returned path is a deque of pixel coordinates representing waypoints from
        start to destination. The path excludes the starting tile but includes the
        destination. Using a deque allows efficient removal of waypoints as they're
        reached via popleft().

        Common usage pattern:
            path = find_path(npc.x, npc.y, target_x, target_y, exclude_sprite=npc)
            while path:
                next_waypoint = path[0]
                # Move toward next_waypoint
                if reached(next_waypoint):
                    path.popleft()

        Args:
            start_x: Starting pixel x position (world coordinates).
            start_y: Starting pixel y position (world coordinates).
            end_tile_x: Target tile x coordinate (grid space).
            end_tile_y: Target tile y coordinate (grid space).
            exclude_sprite: The sprite that is moving, excluded from blocking itself.
            exclude_sprites: Additional sprites to exclude from collision detection.

        Returns:
            Deque of (x, y) pixel position tuples representing the path. Empty deque
            if no path exists even with NPC passthrough.
        """
        # Try normal pathfinding first
        path = self._find_path_internal(start_x, start_y, end_tile_x, end_tile_y, exclude_sprite, exclude_sprites)

        # If no path found, retry with NPC passthrough enabled
        if not path:
            logger.info("  No path found, retrying with NPC passthrough enabled")
            # Collect all NPC sprites from wall_list to exclude them temporarily
            if self.wall_list:
                all_npcs = [
                    sprite
                    for sprite in self.wall_list
                    if hasattr(sprite, "properties") and sprite.properties and sprite.properties.get("name")
                ]
                if exclude_sprites:
                    all_npcs.extend(exclude_sprites)

                path = self._find_path_internal(start_x, start_y, end_tile_x, end_tile_y, exclude_sprite, all_npcs)
                if path:
                    logger.info("  Path found with NPC passthrough (length: %d)", len(path))

        return path

    def _find_path_internal(
        self,
        start_x: float,
        start_y: float,
        end_tile_x: int,
        end_tile_y: int,
        exclude_sprite: arcade.Sprite | None = None,
        exclude_sprites: list[arcade.Sprite] | None = None,
    ) -> deque[tuple[float, float]]:
        """Internal A* pathfinding implementation.

        Core pathfinding algorithm using A* search with Manhattan distance heuristic.
        This method is called internally by find_path() and should not be called directly.

        A* Algorithm overview:
        - Uses a priority queue (heap) to explore tiles in order of estimated total cost
        - f_score = g_score + heuristic, where:
          - g_score: Actual cost from start to current tile
          - heuristic: Estimated cost from current to goal (Manhattan distance)
        - Explores 4-directional movement (up, down, left, right)
        - Maintains came_from map to reconstruct path when goal is reached

        The algorithm only considers tiles that pass the is_tile_walkable check, which
        respects the exclusion lists provided.

        Path reconstruction:
        - Starts at goal and follows came_from links back to start
        - Reverses to get start-to-goal ordering
        - Converts tile coordinates to pixel centers
        - Skips starting tile (entity is already there)

        Args:
            start_x: Starting pixel x position.
            start_y: Starting pixel y position.
            end_tile_x: Target tile x coordinate.
            end_tile_y: Target tile y coordinate.
            exclude_sprite: The sprite that is moving (excluded from collision).
            exclude_sprites: List of sprites to exclude (e.g., all moving NPCs).

        Returns:
            Deque of (x, y) pixel positions to follow. Empty deque if no path found.
        """
        # Convert pixel positions to tile coordinates
        start_tile_x = int(start_x / self.tile_size)
        start_tile_y = int(start_y / self.tile_size)

        logger.debug("  Starting tile: (%d, %d)", start_tile_x, start_tile_y)
        start_walkable = self.is_tile_walkable(start_tile_x, start_tile_y, exclude_sprite, exclude_sprites)
        end_walkable = self.is_tile_walkable(end_tile_x, end_tile_y, exclude_sprite, exclude_sprites)
        logger.debug("  Start tile walkable: %s", start_walkable)
        logger.debug("  End tile walkable: %s", end_walkable)

        if not end_walkable:
            logger.warning("  End tile blocked at (%d, %d)!", end_tile_x, end_tile_y)

        # A* pathfinding
        def heuristic(ax: int, ay: int, bx: int, by: int) -> float:
            """Manhattan distance heuristic.

            Calculates the estimated cost from point A to point B using Manhattan
            (taxicab) distance. This is optimal for 4-directional grid movement
            where diagonal movement is not allowed.

            Args:
                ax: Point A x coordinate.
                ay: Point A y coordinate.
                bx: Point B x coordinate.
                by: Point B y coordinate.

            Returns:
                Manhattan distance as number of tile steps.
            """
            return abs(ax - bx) + abs(ay - by)

        # Priority queue: (f_score, tile_x, tile_y)
        open_set: list[tuple[float, int, int]] = []
        heappush(open_set, (0, start_tile_x, start_tile_y))

        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], float] = {(start_tile_x, start_tile_y): 0}

        while open_set:
            _, current_x, current_y = heappop(open_set)

            # Reached goal
            if current_x == end_tile_x and current_y == end_tile_y:
                # Reconstruct path
                tile_path = [(end_tile_x, end_tile_y)]
                current = (end_tile_x, end_tile_y)
                while current in came_from:
                    current = came_from[current]
                    tile_path.append(current)
                tile_path.reverse()

                # Convert tile path to pixel path
                path: deque[tuple[float, float]] = deque()
                for tx, ty in tile_path[1:]:  # Skip start tile
                    pixel_x = tx * self.tile_size + self.tile_size / 2
                    pixel_y = ty * self.tile_size + self.tile_size / 2
                    path.append((pixel_x, pixel_y))

                return path

            # Check all 4 neighbors (up, down, left, right)
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                neighbor_x = current_x + dx
                neighbor_y = current_y + dy

                if not self.is_tile_walkable(neighbor_x, neighbor_y, exclude_sprite, exclude_sprites):
                    continue

                tentative_g = g_score[(current_x, current_y)] + 1

                if (neighbor_x, neighbor_y) not in g_score or tentative_g < g_score[(neighbor_x, neighbor_y)]:
                    came_from[(neighbor_x, neighbor_y)] = (current_x, current_y)
                    g_score[(neighbor_x, neighbor_y)] = tentative_g
                    f_score = tentative_g + heuristic(neighbor_x, neighbor_y, end_tile_x, end_tile_y)
                    heappush(open_set, (f_score, neighbor_x, neighbor_y))

        # No path found
        logger.warning(
            "  No path found from (%d, %d) to (%d, %d)",
            start_tile_x,
            start_tile_y,
            end_tile_x,
            end_tile_y,
        )
        return deque()
