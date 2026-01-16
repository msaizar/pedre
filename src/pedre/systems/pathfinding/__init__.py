"""Pathfinding system using A* algorithm.

This module provides the pathfinding system for navigating entities around obstacles
in the game world. It uses the A* algorithm with Manhattan distance heuristic for
optimal path calculation on a tile-based grid.

The pathfinding system consists of:
- PathfindingManager: Coordinates path calculation and collision detection
- A* algorithm implementation with tile-based navigation
- Automatic retry logic with NPC passthrough for blocked paths
"""

from pedre.systems.pathfinding.manager import PathfindingManager

__all__ = [
    "PathfindingManager",
]
