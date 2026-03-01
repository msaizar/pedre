"""Tests for player sprite creation via AnimatedSprite with player-type states.

AnimatedPlayer has been removed. Player sprites now use the generic AnimatedSprite
with data-driven state configs (idle, walk) loaded from the content registry.
"""

from typing import TYPE_CHECKING

import pytest
from PIL import Image

from pedre.sprites import AnimatedSprite
from pedre.sprites.types import AnimationStateConfig

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(scope="module")
def sprite_sheet_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a test sprite sheet shared across all tests in this module."""
    tmp_path = tmp_path_factory.mktemp("player_sprites")
    path = tmp_path / "test_player_sprite.png"
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
                    color = (row * 25, col * 25, 200, 255)
                    image.putpixel((pixel_x, pixel_y), color)

    image.save(path)
    return path


def make_player_states() -> dict[str, AnimationStateConfig]:
    """Build typical player state configs (idle + walk, 4-directional)."""
    return {
        "idle": AnimationStateConfig(
            name="idle",
            directional=True,
            loop=True,
            priority=0,
            directions={
                "down": {"frames": 4, "row": 0},
                "up": {"frames": 4, "row": 1},
                "right": {"frames": 4, "row": 2},
            },
        ),
        "walk": AnimationStateConfig(
            name="walk",
            directional=True,
            loop=True,
            priority=1,
            directions={
                "down": {"frames": 6, "row": 4},
                "up": {"frames": 6, "row": 5},
                "right": {"frames": 6, "row": 6},
            },
        ),
    }


class TestPlayerAnimatedSprite:
    """Tests for player sprite using AnimatedSprite with player-type states."""

    def test_player_sprite_initialization(self, sprite_sheet_path: Path) -> None:
        """Test basic player sprite initialization."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states=make_player_states(),
        )

        assert sprite.has_state("idle")
        assert sprite.has_state("walk")
        assert "idle_down" in sprite.animation_textures
        assert "idle_up" in sprite.animation_textures
        assert "walk_down" in sprite.animation_textures
        assert "walk_up" in sprite.animation_textures

    def test_player_sprite_position_and_scale(self, sprite_sheet_path: Path) -> None:
        """Test player sprite position and scale."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            scale=2.0,
            center_x=100.0,
            center_y=200.0,
            states=make_player_states(),
        )

        assert sprite.center_x == 100.0
        assert sprite.center_y == 200.0
        assert sprite.scale == (2.0, 2.0)

    def test_player_walk_state_activates(self, sprite_sheet_path: Path) -> None:
        """Test that requesting walk state activates it."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states=make_player_states(),
        )
        sprite.request_state("walk")
        assert "walk" in sprite._active_states

    def test_player_walk_state_deactivates(self, sprite_sheet_path: Path) -> None:
        """Test that releasing walk state deactivates it."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states=make_player_states(),
        )
        sprite.request_state("walk")
        sprite.release_state("walk")
        assert "walk" not in sprite._active_states

    def test_player_walk_takes_priority_over_idle(self, sprite_sheet_path: Path) -> None:
        """Test that walk (priority 1) takes priority over idle (priority 0)."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states=make_player_states(),
        )
        sprite.animation_speed = 0.1
        sprite.request_state("walk")
        sprite.update_animation(delta_time=0.11)
        assert sprite._current_playing == "walk"

    def test_player_idle_after_walk_released(self, sprite_sheet_path: Path) -> None:
        """Test that idle plays after walk is released."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states=make_player_states(),
        )
        sprite.animation_speed = 0.1
        sprite.request_state("walk")
        sprite.update_animation(delta_time=0.11)
        sprite.release_state("walk")
        sprite.update_animation(delta_time=0.11)
        assert sprite._current_playing == "idle"

    def test_player_left_animation_autogenerated(self, sprite_sheet_path: Path) -> None:
        """Test that left animation is auto-generated by flipping right."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states=make_player_states(),
        )

        assert sprite.animation_textures.get("idle_left")
        assert sprite.animation_textures.get("walk_left")

    def test_player_direction_changes(self, sprite_sheet_path: Path) -> None:
        """Test that player direction can be changed."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states=make_player_states(),
        )
        sprite.set_direction("up")
        assert sprite.current_direction == "up"

        sprite.set_direction("down")
        assert sprite.current_direction == "down"

    def test_player_frame_counts(self, sprite_sheet_path: Path) -> None:
        """Test that frame counts match the config."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states=make_player_states(),
        )

        assert len(sprite.animation_textures["idle_down"]) == 4
        assert len(sprite.animation_textures["idle_up"]) == 4
        assert len(sprite.animation_textures["walk_down"]) == 6
        assert len(sprite.animation_textures["walk_up"]) == 6
