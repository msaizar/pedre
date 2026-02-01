"""Pathfinding plugin using A* algorithm.

This module provides the pathfinding plugin for navigating entities around obstacles
in the game world. It uses the A* algorithm with Manhattan distance heuristic for
optimal path calculation on a tile-based grid.

The pathfinding plugin consists of:
- PathfindingPlugin: Coordinates path calculation and collision detection
- A* algorithm implementation with tile-based navigation
- Automatic retry logic with NPC passthrough for blocked paths
"""

from pedre.plugins.pathfinding.base import PathfindingBasePlugin
from pedre.plugins.pathfinding.plugin import PathfindingPlugin

__all__ = ["PathfindingBasePlugin", "PathfindingPlugin"]
