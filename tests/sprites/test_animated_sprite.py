"""Tests for AnimatedSprite."""

import unittest
from pathlib import Path

from PIL import Image

from pedre.sprites import AnimatedSprite


class TestAnimatedSprite(unittest.TestCase):
    """Test Suite for AnimatedSprite sprite class."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create a test sprite sheet for all tests."""
        # Create a temporary sprite sheet (16x16 tiles, 10 rows, 10 columns)
        cls.sprite_sheet_path = Path(__file__).parent / "test_animated_sprite.png"
        tile_size = 16
        rows = 10
        cols = 10

        # Create a simple test sprite sheet
        image = Image.new("RGBA", (cols * tile_size, rows * tile_size), (0, 0, 0, 0))

        # Fill each tile with a slightly different color for testing
        for row in range(rows):
            for col in range(cols):
                for x in range(tile_size):
                    for y in range(tile_size):
                        pixel_x = col * tile_size + x
                        pixel_y = row * tile_size + y
                        # Create a unique color based on row and col
                        color = (row * 25, col * 25, 128, 255)
                        image.putpixel((pixel_x, pixel_y), color)

        image.save(cls.sprite_sheet_path)

    @classmethod
    def tearDownClass(cls) -> None:
        """Clean up test sprite sheet."""
        if cls.sprite_sheet_path.exists():
            cls.sprite_sheet_path.unlink()

    def test_initialization_basic(self) -> None:
        """Test basic initialization of AnimatedSprite."""
        animated_sprite = AnimatedSprite(
            str(self.sprite_sheet_path),
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

    def test_only_walk_animation_defined(self) -> None:
        """Test when only the walk animations are defined."""
        animated_sprite = AnimatedSprite(
            str(self.sprite_sheet_path),
            tile_size=16,
            walk_down_row=0,
            walk_down_frames=4,
        )
        assert animated_sprite.current_direction == "down"

    def test_left_walk_animation_defined(self) -> None:
        """Test when only the left walk animations are defined."""
        animated_sprite = AnimatedSprite(
            str(self.sprite_sheet_path),
            tile_size=16,
            walk_left_row=0,
            walk_left_frames=4,
        )
        assert animated_sprite.current_direction == "right"

    def test_right_walk_animation_defined(self) -> None:
        """Test when only the right walk animations are defined."""
        animated_sprite = AnimatedSprite(
            str(self.sprite_sheet_path),
            tile_size=16,
            walk_right_row=0,
            walk_right_frames=4,
        )
        assert animated_sprite.current_direction == "right"

    def test_skip_animation_update_when_animation_doesnt_exist(self) -> None:
        """Test the animation skips when it doesn't exist."""
        animated_sprite = AnimatedSprite(
            str(self.sprite_sheet_path),
            tile_size=16,
        )
        assert animated_sprite.update_animation() is None

    def test_reset_frame_if_exceeds_current_animation(self) -> None:
        """Test the animation skips when it doesn't exist."""
        animated_sprite = AnimatedSprite(
            str(self.sprite_sheet_path),
            tile_size=16,
            idle_right_row=0,
            idle_right_frames=4,
        )
        animated_sprite.current_frame = 8
        animated_sprite.update_animation()
        assert animated_sprite.current_frame == 0

    def test_set_direction_changes(self) -> None:
        """Test direction changes."""
        animated_sprite = AnimatedSprite(
            str(self.sprite_sheet_path),
            tile_size=16,
            idle_right_row=0,
            idle_right_frames=4,
        )
        animated_sprite.current_direction = "up"
        animated_sprite.set_direction("down")
        assert animated_sprite.current_direction == "down"

    def test_set_direction_doesnt_change(self) -> None:
        """Test no direction changes."""
        animated_sprite = AnimatedSprite(
            str(self.sprite_sheet_path),
            tile_size=16,
            idle_right_row=0,
            idle_right_frames=4,
        )
        animated_sprite.current_direction = "up"
        animated_sprite.set_direction("up")
        assert animated_sprite.current_direction == "up"
