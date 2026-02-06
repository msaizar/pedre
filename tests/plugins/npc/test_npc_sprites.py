"""Unit tests for AnimatedNPC in src/pedre/plugins/npc/sprites.py."""

import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from pedre.plugins.npc.sprites import AnimatedNPC


class TestAnimatedNPC(unittest.TestCase):
    """Test Suite for AnimatedNPC sprite class."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create a test sprite sheet for all tests."""
        # Create a temporary sprite sheet (16x16 tiles, 10 rows, 10 columns)
        cls.sprite_sheet_path = Path(__file__).parent / "test_npc_sprite.png"
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
        """Test basic initialization of AnimatedNPC."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            tile_size=16,
        )

        # Check NPC-specific state
        assert not npc.is_appearing
        assert not npc.appear_complete
        assert not npc.is_disappearing
        assert not npc.disappear_complete
        assert not npc.is_interacting
        assert not npc.interact_complete

        # Check animation texture keys exist
        assert "appear" in npc.animation_textures
        assert "disappear" in npc.animation_textures
        assert "interact_up" in npc.animation_textures
        assert "interact_down" in npc.animation_textures
        assert "interact_left" in npc.animation_textures
        assert "interact_right" in npc.animation_textures

    def test_initialization_with_all_idle_and_walk_animations(self) -> None:
        """Test initialization with all 4-directional idle and walk animations."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_up_frames=4,
            idle_up_row=0,
            idle_down_frames=4,
            idle_down_row=1,
            idle_left_frames=4,
            idle_left_row=2,
            idle_right_frames=4,
            idle_right_row=3,
            walk_up_frames=6,
            walk_up_row=4,
            walk_down_frames=6,
            walk_down_row=5,
            walk_left_frames=6,
            walk_left_row=6,
            walk_right_frames=6,
            walk_right_row=7,
            tile_size=16,
            scale=2.0,
            center_x=100,
            center_y=200,
        )

        # Check position and scale (scale is a tuple in arcade)
        assert npc.center_x == 100
        assert npc.center_y == 200
        assert npc.scale == (2.0, 2.0)

        # Check that base animations were loaded (via parent class)
        assert len(npc.animation_textures["idle_up"]) == 4
        assert len(npc.animation_textures["idle_down"]) == 4
        assert len(npc.animation_textures["walk_up"]) == 6
        assert len(npc.animation_textures["walk_down"]) == 6

    def test_initialization_with_appear_animation(self) -> None:
        """Test initialization with appear animation."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            appear_frames=5,
            appear_row=8,
            tile_size=16,
        )

        # Appear animation should be loaded
        assert len(npc.animation_textures["appear"]) == 5
        # Disappear should be auto-generated (reversed)
        assert len(npc.animation_textures["disappear"]) == 5
        assert npc.appear_frames == 5
        assert npc.appear_row == 8

    def test_initialization_with_disappear_animation(self) -> None:
        """Test initialization with disappear animation (appear auto-generated)."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            disappear_frames=5,
            disappear_row=8,
            tile_size=16,
        )

        # Disappear animation should be loaded
        assert len(npc.animation_textures["disappear"]) == 5
        # Appear should be auto-generated (reversed)
        assert len(npc.animation_textures["appear"]) == 5
        assert npc.disappear_frames == 5
        assert npc.disappear_row == 8

    def test_initialization_with_both_appear_and_disappear(self) -> None:
        """Test initialization with both appear and disappear animations."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            appear_frames=5,
            appear_row=8,
            disappear_frames=6,
            disappear_row=9,
            tile_size=16,
        )

        # Both animations should be loaded independently
        assert len(npc.animation_textures["appear"]) == 5
        assert len(npc.animation_textures["disappear"]) == 6
        assert npc.appear_frames == 5
        assert npc.disappear_frames == 6

    def test_initialization_with_interact_animations(self) -> None:
        """Test initialization with interact animations for all directions."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            interact_up_frames=3,
            interact_up_row=1,
            interact_down_frames=3,
            interact_down_row=2,
            interact_left_frames=3,
            interact_left_row=3,
            interact_right_frames=3,
            interact_right_row=4,
            tile_size=16,
        )

        # All interact animations should be loaded
        assert len(npc.animation_textures["interact_up"]) == 3
        assert len(npc.animation_textures["interact_down"]) == 3
        assert len(npc.animation_textures["interact_left"]) == 3
        assert len(npc.animation_textures["interact_right"]) == 3

    def test_initialization_without_base_animations_uses_appear_texture(self) -> None:
        """Test that appear texture is used when no idle/walk animations are provided."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            appear_frames=5,
            appear_row=8,
            tile_size=16,
        )

        # Should use first appear frame as initial texture
        assert npc.texture is not None
        assert npc.texture == npc.animation_textures["appear"][0]

    def test_start_appear_animation(self) -> None:
        """Test starting the appear animation."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            appear_frames=5,
            appear_row=8,
            tile_size=16,
        )

        npc.start_appear_animation()

        assert npc.is_appearing
        assert not npc.appear_complete
        assert npc.current_frame == 0
        assert npc.animation_timer == 0.0
        assert npc.texture == npc.animation_textures["appear"][0]

    def test_start_appear_animation_without_textures(self) -> None:
        """Test starting appear animation when no appear textures are loaded."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            tile_size=16,
        )

        npc.visible = False
        npc.start_appear_animation()

        # Should set visible and complete immediately
        assert npc.visible
        assert npc.appear_complete
        assert not npc.is_appearing

    def test_start_disappear_animation(self) -> None:
        """Test starting the disappear animation."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            disappear_frames=5,
            disappear_row=8,
            tile_size=16,
        )

        npc.start_disappear_animation()

        assert npc.is_disappearing
        assert not npc.disappear_complete
        assert npc.current_frame == 0
        assert npc.animation_timer == 0.0
        assert npc.texture == npc.animation_textures["disappear"][0]

    def test_start_disappear_animation_without_textures(self) -> None:
        """Test starting disappear animation when no disappear textures are loaded."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            tile_size=16,
        )

        npc.visible = True
        npc.start_disappear_animation()

        # Should set invisible and complete immediately
        assert not npc.visible
        assert npc.disappear_complete
        assert not npc.is_disappearing

    def test_start_interact_animation(self) -> None:
        """Test starting the interact animation."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            interact_down_frames=3,
            interact_down_row=2,
            tile_size=16,
        )

        npc.current_direction = "down"
        npc.start_interact_animation()

        assert npc.is_interacting
        assert not npc.interact_complete
        assert npc.current_frame == 0
        assert npc.animation_timer == 0.0
        assert npc.texture == npc.animation_textures["interact_down"][0]

    def test_start_interact_animation_without_textures(self) -> None:
        """Test starting interact animation when no textures exist for the direction."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            tile_size=16,
        )

        npc.current_direction = "down"
        npc.start_interact_animation()

        # Should not start animation
        assert not npc.is_interacting
        assert not npc.interact_complete

    def test_update_animation_interact(self) -> None:
        """Test update_animation during interact animation."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            interact_down_frames=3,
            interact_down_row=2,
            tile_size=16,
        )

        npc.current_direction = "down"
        npc.animation_speed = 0.1
        npc.start_interact_animation()

        # First update - should advance timer but not frame
        npc.update_animation(delta_time=0.05)
        assert npc.current_frame == 0
        assert npc.animation_timer == 0.05

        # Second update - should advance frame (timer resets to 0 when frame advances)
        npc.update_animation(delta_time=0.06)
        assert npc.current_frame == 1
        assert npc.animation_timer == 0.0
        assert npc.texture == npc.animation_textures["interact_down"][1]

    def test_update_animation_interact_completion(self) -> None:
        """Test interact animation completion and return to idle."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            interact_down_frames=3,
            interact_down_row=2,
            tile_size=16,
        )

        npc.current_direction = "down"
        npc.animation_speed = 0.1
        npc.start_interact_animation()

        # Advance through all frames
        for _ in range(3):
            npc.update_animation(delta_time=0.1)

        # Should complete and return to idle
        assert not npc.is_interacting
        assert npc.interact_complete
        assert npc.current_frame == 0
        assert npc.texture == npc.animation_textures["idle_down"][0]

    def test_update_animation_disappear(self) -> None:
        """Test update_animation during disappear animation."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            disappear_frames=5,
            disappear_row=8,
            tile_size=16,
        )

        npc.animation_speed = 0.1
        npc.start_disappear_animation()

        # First update - should advance timer but not frame
        npc.update_animation(delta_time=0.05)
        assert npc.current_frame == 0
        assert npc.animation_timer == 0.05

        # Second update - should advance frame (timer resets to 0 when frame advances)
        npc.update_animation(delta_time=0.06)
        assert npc.current_frame == 1
        assert npc.animation_timer == 0.0
        assert npc.texture == npc.animation_textures["disappear"][1]

    def test_update_animation_disappear_completion(self) -> None:
        """Test disappear animation completion and becoming invisible."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            disappear_frames=5,
            disappear_row=8,
            tile_size=16,
        )

        npc.animation_speed = 0.1
        npc.start_disappear_animation()

        # Advance through all frames
        for _ in range(5):
            npc.update_animation(delta_time=0.1)

        # Should complete and become invisible
        assert not npc.is_disappearing
        assert npc.disappear_complete
        assert not npc.visible
        assert npc.current_frame == 0

    def test_update_animation_appear(self) -> None:
        """Test update_animation during appear animation."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            appear_frames=5,
            appear_row=8,
            tile_size=16,
        )

        npc.animation_speed = 0.1
        npc.start_appear_animation()

        # First update - should advance timer but not frame
        npc.update_animation(delta_time=0.05)
        assert npc.current_frame == 0
        assert npc.animation_timer == 0.05

        # Second update - should advance frame (timer resets to 0 when frame advances)
        npc.update_animation(delta_time=0.06)
        assert npc.current_frame == 1
        assert npc.animation_timer == 0.0
        assert npc.texture == npc.animation_textures["appear"][1]

    def test_update_animation_appear_completion(self) -> None:
        """Test appear animation completion."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            appear_frames=5,
            appear_row=8,
            tile_size=16,
        )

        npc.animation_speed = 0.1
        npc.start_appear_animation()

        # Advance through all frames
        for _ in range(5):
            npc.update_animation(delta_time=0.1)

        # Should complete
        assert not npc.is_appearing
        assert npc.appear_complete
        assert npc.current_frame == 0

    def test_update_animation_falls_back_to_parent(self) -> None:
        """Test that update_animation delegates to parent when no special animation is active."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            walk_down_frames=6,
            walk_down_row=1,
            tile_size=16,
        )

        npc.current_direction = "down"
        npc.animation_speed = 0.1

        # Should use idle animation when not moving
        npc.update_animation(delta_time=0.1, moving=False)

        # Should use walk animation when moving
        npc.update_animation(delta_time=0.1, moving=True)

    def test_animation_priority_interact_over_disappear(self) -> None:
        """Test that interact animation has priority over disappear."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            disappear_frames=5,
            disappear_row=8,
            interact_down_frames=3,
            interact_down_row=2,
            tile_size=16,
        )

        npc.current_direction = "down"
        npc.animation_speed = 0.1

        # Start both animations
        npc.start_disappear_animation()
        npc.start_interact_animation()

        # Interact should play first
        npc.update_animation(delta_time=0.1)
        assert npc.is_interacting
        assert npc.texture == npc.animation_textures["interact_down"][1]

    def test_load_npc_textures_logging(self) -> None:
        """Test that _load_npc_textures logs appropriate messages."""
        with patch("pedre.plugins.npc.sprites.logger") as mock_logger:
            AnimatedNPC(
                str(self.sprite_sheet_path),
                idle_down_frames=4,
                idle_down_row=0,
                appear_frames=5,
                appear_row=8,
                interact_down_frames=3,
                interact_down_row=2,
                tile_size=16,
            )

            # Should have logged info about animations being loaded
            assert mock_logger.info.called
            assert mock_logger.debug.called

    def test_interact_animation_different_directions(self) -> None:
        """Test interact animation works for all four directions."""
        npc = AnimatedNPC(
            str(self.sprite_sheet_path),
            idle_down_frames=4,
            idle_down_row=0,
            interact_up_frames=3,
            interact_up_row=1,
            interact_down_frames=3,
            interact_down_row=2,
            interact_left_frames=3,
            interact_left_row=3,
            interact_right_frames=3,
            interact_right_row=4,
            tile_size=16,
        )

        # Test each direction
        for direction in ["up", "down", "left", "right"]:
            npc.current_direction = direction
            npc.start_interact_animation()

            assert npc.is_interacting
            assert npc.texture == npc.animation_textures[f"interact_{direction}"][0]

            # Reset for next direction
            npc.is_interacting = False
            npc.current_frame = 0


if __name__ == "__main__":
    unittest.main()
