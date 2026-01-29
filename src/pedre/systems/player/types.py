"""Types for Player system."""

from typing import TypedDict


class PlayerInitKwargs(TypedDict, total=False):
    """Type-safe kwargs for AnimatedPlayer initialization."""

    center_x: float
    center_y: float
    scale: float
    tile_size: int
