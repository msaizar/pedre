"""Types for NPC plugin."""

from typing import TypedDict


class NPCInitKwargs(TypedDict, total=False):
    """Type-safe kwargs for AnimatedNPC initialization."""

    center_x: float
    center_y: float
    scale: float
    tile_size: int
