"""Helper functions for sprite animation loading."""

from typing import TYPE_CHECKING

import arcade
from PIL.Image import Transpose

if TYPE_CHECKING:
    from PIL import Image


def load_animation_frames(
    sprite_sheet: Image.Image,
    texture_name_prefix: str,
    dict_key: str,
    frame_count: int,
    row_index: int,
    tile_size: int,
    animation_textures: dict[str, list[arcade.Texture]],
    *,
    flip: bool = False,
) -> None:
    """Load animation frames from a sprite sheet row.

    Args:
        sprite_sheet: The PIL Image object of the sprite sheet.
        texture_name_prefix: Prefix for texture names (e.g., "player_idle_left").
        dict_key: Key to use in animation_textures dict (e.g., "idle_left").
        frame_count: Number of frames to load from the row.
        row_index: Row index in the sprite sheet.
        tile_size: Size of each frame in pixels.
        animation_textures: Dictionary to append loaded textures to.
        flip: Whether to flip the image horizontally.
    """
    for frame_num in range(frame_count):
        left = frame_num * tile_size
        top = row_index * tile_size
        right = left + tile_size
        bottom = top + tile_size

        frame_image = sprite_sheet.crop((left, top, right, bottom))

        if flip:
            frame_image = frame_image.transpose(Transpose.FLIP_LEFT_RIGHT)

        texture = arcade.Texture(
            name=f"{texture_name_prefix}_{frame_num}",
            image=frame_image,
        )
        animation_textures[dict_key].append(texture)
