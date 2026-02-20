"""Tests for AnimatedSprite."""

from typing import TYPE_CHECKING

import pytest
from PIL import Image

from pedre.sprites import AnimatedSprite

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="module")
def sprite_sheet_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a test sprite sheet shared across all tests in this module."""
    tmp_path = tmp_path_factory.mktemp("sprites")
    path = tmp_path / "test_animated_sprite.png"

    tile_size = 16
    rows = 10
    cols = 10

    image = Image.new("RGBA", (cols * tile_size, rows * tile_size), (0, 0, 0, 0))

    for row in range(rows):
        for col in range(cols):
            for x in range(tile_size):
                for y in range(tile_size):
                    pixel_x = col * tile_size + x
                    pixel_y = row * tile_size + y
                    color = (row * 25, col * 25, 128, 255)
                    image.putpixel((pixel_x, pixel_y), color)

    image.save(path)
    return path


class TestAnimatedSprite:
    """Test Suite for AnimatedSprite sprite class."""

    def test_initialization_basic(self, sprite_sheet_path: Path) -> None:
        """Test basic initialization of AnimatedSprite."""
        animated_sprite = AnimatedSprite(
            str(sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            tile_size=16,
        )

        # Check animation texture keys exist
        assert "idle_up" in animated_sprite.animation_textures
        assert "idle_down" in animated_sprite.animation_textures
        assert "idle_left" in animated_sprite.animation_textures
        assert "idle_right" in animated_sprite.animation_textures
        assert "walk_up" in animated_sprite.animation_textures
        assert "walk_down" in animated_sprite.animation_textures
        assert "walk_left" in animated_sprite.animation_textures
        assert "walk_right" in animated_sprite.animation_textures

    def test_only_walk_animation_defined(self, sprite_sheet_path: Path) -> None:
        """Test when only the walk animations are defined."""
        animated_sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            walk_down_row=0,
            walk_down_frames=4,
        )
        assert animated_sprite.current_direction == "down"

    def test_left_walk_animation_defined(self, sprite_sheet_path: Path) -> None:
        """Test when only the left walk animations are defined."""
        animated_sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            walk_left_row=0,
            walk_left_frames=4,
        )
        assert animated_sprite.current_direction == "right"

    def test_right_walk_animation_defined(self, sprite_sheet_path: Path) -> None:
        """Test when only the right walk animations are defined."""
        animated_sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            walk_right_row=0,
            walk_right_frames=4,
        )
        assert animated_sprite.current_direction == "right"

    def test_skip_animation_update_when_animation_doesnt_exist(self, sprite_sheet_path: Path) -> None:
        """Test the animation skips when it doesn't exist."""
        animated_sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
        )
        assert animated_sprite.update_animation() is None

    def test_reset_frame_if_exceeds_current_animation(self, sprite_sheet_path: Path) -> None:
        """Test the animation skips when it doesn't exist."""
        animated_sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            idle_right_row=0,
            idle_right_frames=4,
        )
        animated_sprite.current_frame = 8
        animated_sprite.update_animation()
        assert animated_sprite.current_frame == 0

    def test_set_direction_changes(self, sprite_sheet_path: Path) -> None:
        """Test direction changes."""
        animated_sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            idle_right_row=0,
            idle_right_frames=4,
        )
        animated_sprite.current_direction = "up"
        animated_sprite.set_direction("down")
        assert animated_sprite.current_direction == "down"

    def test_set_direction_doesnt_change(self, sprite_sheet_path: Path) -> None:
        """Test no direction changes."""
        animated_sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            idle_right_row=0,
            idle_right_frames=4,
        )
        animated_sprite.current_direction = "up"
        animated_sprite.set_direction("up")
        assert animated_sprite.current_direction == "up"
