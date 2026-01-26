"""Pathfinding system using Arcade's built-in A* algorithm.

This module provides efficient pathfinding for NPCs and other game entities that need
to navigate around obstacles in the game world. It leverages Arcade 3.3.3's built-in
AStarBarrierList and astar_calculate_path for optimal path calculation on a grid.

The pathfinding system consists of:
- PathfindingManager: Coordinates path calculation using Arcade's A* implementation
- Dynamic sprite exclusion for flexible obstacle handling
- Automatic retry logic with NPC passthrough for blocked paths

Key features:
- Arcade's optimized A* pathfinding with 4-directional movement
- Grid-based collision detection against wall sprites (configurable grid size)
- Sprite exclusion system to ignore specific entities during pathfinding
- Automatic fallback to NPC passthrough when normal pathfinding fails
- Direct pixel-to-pixel pathfinding for clean coordinate handling

NPCs can be excluded from collision checks
to allow them to pathfind through each other when necessary.

Pathfinding workflow:
1. Filter wall sprites to exclude specified sprites (moving entity, other NPCs)
2. Create AStarBarrierList with filtered obstacles and map boundaries
3. Use Arcade's astar_calculate_path to find optimal pixel path avoiding walls
4. Return path as deque for efficient pop operations during movement

Integration with other systems:
- NPCManager calls find_path when moving NPCs to waypoints
- MoveNPCAction triggers pathfinding via NPC manager
- Wall list is shared with the physics/collision system

Example usage:
    # Get pathfinding manager from context
    pathfinding = context.get_system("pathfinding")

    # Find path from pixel position to pixel position
    path = pathfinding.find_path(
        start_x=player.center_x,
        start_y=player.center_y,
        end_x=320.0,
        end_y=480.0,
        exclude_sprite=npc_sprite
    )

    # Path is a deque of (x, y) pixel positions
    while path:
        next_pos = path.popleft()
        # Move sprite toward next_pos
"""

import logging
from collections import deque
from typing import TYPE_CHECKING, ClassVar

import arcade

from pedre.systems.pathfinding.base import PathfindingBaseManager
from pedre.systems.registry import SystemRegistry

if TYPE_CHECKING:
    from pedre.systems.game_context import GameContext

logger = logging.getLogger(__name__)


@SystemRegistry.register
class PathfindingManager(PathfindingBaseManager):
    """Manages pathfinding calculations using Arcade's built-in A* algorithm.

    The PathfindingManager provides efficient navigation for game entities by
    leveraging Arcade 3.3.3's AStarBarrierList and astar_calculate_path functions.
    It handles dynamic sprite exclusion and automatic NPC passthrough.

    The manager works entirely in pixel coordinates for simplicity:
    - Input: start and end positions in pixel coordinates
    - Output: path as deque of pixel coordinates

    Key responsibilities:
    - Calculate optimal paths between start and end positions
    - Check walkability using wall sprite collision detection
    - Exclude specific sprites from collision (e.g., the moving entity itself)
    - Automatic retry with NPC passthrough when paths are blocked

    The NPC passthrough feature allows NPCs to pathfind through each other when
    their direct path is blocked by other NPCs. This prevents permanent deadlocks
    where NPCs block each other's paths.
    """

    name: ClassVar[str] = "pathfinding"
    dependencies: ClassVar[list[str]] = []

    def __init__(self) -> None:
        """Initialize the pathfinding manager.

        Creates a pathfinding manager. Tile size is dynamically retrieved from
        the scene manager's current map during pathfinding operations.
        """

    def setup(self, context: GameContext) -> None:
        """Initialize the pathfinding system with game context.

        This method is called by the SystemLoader after all systems have been
        instantiated.

        Args:
            context: Game context providing access to other systems.
        """
        self.context = context
        logger.debug("PathfindingManager setup complete")

    def cleanup(self) -> None:
        """Clean up pathfinding resources when the scene unloads.

        Clears the wall list reference.
        """
        logger.debug("PathfindingManager cleanup complete")

    def _get_map_boundaries(self) -> tuple[float, float, float, float]:
        """Get playfield boundaries for pathfinding.

        Calculates the boundaries of the game world for pathfinding operations.
        First tries to use the tile map dimensions, then falls back to estimating
        from the wall sprite list, and finally uses a safe default.

        Returns:
            Tuple of (left, right, bottom, top) in pixel coordinates.
        """
        tile_map = self.context.scene_manager.get_tile_map()
        if tile_map:
            map_width = tile_map.width * tile_map.tile_width
            map_height = tile_map.height * tile_map.tile_height
            return (0, map_width, 0, map_height)

        # Fallback: estimate from wall_list
        wall_list = self.context.scene_manager.get_wall_list()
        if wall_list:
            max_x = max((s.center_x + s.width / 2 for s in wall_list), default=1000)
            max_y = max((s.center_y + s.height / 2 for s in wall_list), default=1000)
            return (0, max_x, 0, max_y)

        return (0, 1000, 0, 1000)  # Safe default

    def find_path(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        exclude_sprite: arcade.Sprite | None = None,
        exclude_sprites: list[arcade.Sprite] | None = None,
    ) -> deque[tuple[float, float]]:
        """Find a path using Arcade's A* pathfinding with automatic retry logic.

        Calculates the optimal path from a start position to a target position using
        Arcade's built-in A* algorithm. If the initial pathfinding fails (typically
        due to NPC blocking), automatically retries with NPC passthrough enabled.

        The two-phase approach:
        1. First attempt: Normal pathfinding with only specified exclusions
        2. Second attempt: Retry with all NPCs excluded if first attempt fails

        This prevents permanent deadlocks where NPCs block each other's paths. The
        NPC passthrough allows entities to pathfind "through" NPCs, with the expectation
        that NPCs will move out of the way before collision occurs.

        The returned path is a deque of pixel coordinates representing waypoints from
        start to destination. The path excludes the starting position but includes the
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
            end_x: Target pixel x position (world coordinates).
            end_y: Target pixel y position (world coordinates).
            exclude_sprite: The sprite that is moving, excluded from blocking itself.
            exclude_sprites: Additional sprites to exclude from collision detection.

        Returns:
            Deque of (x, y) pixel position tuples representing the path. Empty deque
            if no path exists even with NPC passthrough.
        """
        # Try normal pathfinding first
        path = self._find_path_internal(start_x, start_y, end_x, end_y, exclude_sprite, exclude_sprites)

        # If no path found, retry with NPC passthrough enabled
        scene_manager = self.context.scene_manager
        wall_list = scene_manager.get_wall_list()
        if not path:
            logger.info("  No path found, retrying with NPC passthrough enabled")
            # Collect all NPC sprites from wall_list to exclude them temporarily
            if wall_list:
                all_npcs = [
                    sprite
                    for sprite in wall_list
                    if hasattr(sprite, "properties") and sprite.properties and sprite.properties.get("name")
                ]
                if exclude_sprites:
                    all_npcs.extend(exclude_sprites)

                path = self._find_path_internal(start_x, start_y, end_x, end_y, exclude_sprite, all_npcs)
                if path:
                    logger.info("  Path found with NPC passthrough (length: %d)", len(path))

        return path

    def _find_path_internal(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        exclude_sprite: arcade.Sprite | None = None,
        exclude_sprites: list[arcade.Sprite] | None = None,
    ) -> deque[tuple[float, float]]:
        """Internal pathfinding implementation using Arcade's A* algorithm.

        Uses Arcade's built-in AStarBarrierList and astar_calculate_path to find
        optimal paths. This method is called internally by find_path() and should
        not be called directly.

        The implementation:
        - Creates a filtered sprite list excluding specified sprites
        - Builds an AStarBarrierList with map boundaries
        - Calls Arcade's astar_calculate_path with diagonal_movement=False
        - Converts result to deque, skipping the start position

        Args:
            start_x: Starting pixel x position.
            start_y: Starting pixel y position.
            end_x: Target pixel x position.
            end_y: Target pixel y position.
            exclude_sprite: The sprite that is moving (excluded from collision).
            exclude_sprites: List of sprites to exclude (e.g., all moving NPCs).

        Returns:
            Deque of (x, y) pixel positions to follow. Empty deque if no path found.
        """
        logger.debug("  Finding path from (%.1f, %.1f) to (%.1f, %.1f)", start_x, start_y, end_x, end_y)

        # Get wall list
        wall_list = self.context.scene_manager.get_wall_list()
        if not wall_list:
            # No obstacles - return direct path
            logger.debug("  No wall list, returning direct path")
            return deque([(end_x, end_y)])

        # Build excluded sprite set
        excluded = set()
        if exclude_sprite:
            excluded.add(exclude_sprite)
        if exclude_sprites:
            excluded.update(exclude_sprites)

        # Create filtered blocking sprite list
        blocking_sprites = arcade.SpriteList()
        for sprite in wall_list:
            if sprite not in excluded:
                blocking_sprites.append(sprite)

        # Get map boundaries and tile size
        left, right, bottom, top = self._get_map_boundaries()
        tile_size = self.context.scene_manager.get_tile_size()
        logger.debug("  Map boundaries: left=%.1f, right=%.1f, bottom=%.1f, top=%.1f", left, right, bottom, top)
        logger.debug("  Grid size (tile size): %d", tile_size)

        # Create AStarBarrierList
        # Use exclude_sprite if available, otherwise create a dummy sprite
        moving_sprite = exclude_sprite if exclude_sprite else arcade.Sprite()
        barrier_list = arcade.AStarBarrierList(
            moving_sprite=moving_sprite,
            blocking_sprites=blocking_sprites,
            grid_size=tile_size,
            left=int(left),
            right=int(right),
            bottom=int(bottom),
            top=int(top),
        )

        # Calculate path using Arcade's A* implementation
        path_list = arcade.astar_calculate_path(
            start_point=(start_x, start_y),
            end_point=(end_x, end_y),
            astar_barrier_list=barrier_list,
            diagonal_movement=False,  # Preserve 4-directional movement
        )

        # Convert to deque, skip start point (match current behavior)
        if path_list is None:
            logger.warning("  No path found from (%.1f, %.1f) to (%.1f, %.1f)", start_x, start_y, end_x, end_y)
            return deque()

        # Skip first point (start position) to match existing behavior
        path = deque(path_list[1:]) if len(path_list) > 1 else deque()
        logger.debug("  Path found with %d waypoints", len(path))
        return path
