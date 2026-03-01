"""Factory for creating AnimatedSprite instances from registry definitions."""

from typing import Any

from pedre.sprites.animated_sprite import AnimatedSprite
from pedre.sprites.types import AnimationStateConfig


def create_sprite_from_definition(
    sprite_def: dict[str, Any],
    *,
    center_x: float = 0.0,
    center_y: float = 0.0,
    scale: float | None = None,
    tile_size: int | None = None,
) -> AnimatedSprite:
    """Create an AnimatedSprite from a sprite registry definition dict.

    The definition should follow the sprites.json schema:
        {
            "sprite_sheet": "path/to/sheet.png",
            "frame_width": 16,   # used as tile_size when tile_size not overridden
            "frame_height": 16,
            "states": {
                "idle": { "directional": true, "loop": true, "priority": 0, ... },
                ...
            }
        }

    Args:
        sprite_def: Sprite definition dict from the content registry.
        center_x: Initial X position in world coordinates.
        center_y: Initial Y position in world coordinates.
        scale: Override the sprite scale. If None, defaults to 1.0.
        tile_size: Override the tile size. If None, uses frame_width from definition.

    Returns:
        Configured AnimatedSprite ready for use.
    """
    sprite_sheet = sprite_def["sprite_sheet"]
    resolved_tile_size = tile_size if tile_size is not None else int(sprite_def["frame_width"])

    states: dict[str, AnimationStateConfig] = {}
    for state_name, state_data in sprite_def.get("states", {}).items():
        states[state_name] = AnimationStateConfig.from_dict(state_name, state_data)

    return AnimatedSprite(
        sprite_sheet,
        tile_size=resolved_tile_size,
        scale=scale if scale is not None else 1.0,
        center_x=center_x,
        center_y=center_y,
        states=states,
    )
