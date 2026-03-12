"""Tests for AnimatedSprite."""

import logging
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


def make_idle_state(row: int = 0, frames: int = 4) -> AnimationStateConfig:
    """Helper: create a basic directional idle state config."""
    return AnimationStateConfig(
        name="idle",
        directional=True,
        loop=True,
        priority=0,
        directions={"down": {"frames": frames, "row": row}},
    )


def make_walk_state(row: int = 1, frames: int = 4) -> AnimationStateConfig:
    """Helper: create a basic directional walk state config."""
    return AnimationStateConfig(
        name="walk",
        directional=True,
        loop=True,
        priority=1,
        directions={"down": {"frames": frames, "row": row}},
    )


class TestAnimatedSpriteInitialization:
    """Tests for AnimatedSprite initialization with the state-machine API."""

    def test_initialization_with_idle_state(self, sprite_sheet_path: Path) -> None:
        """Test basic initialization with a single idle state."""
        idle_cfg = AnimationStateConfig(
            name="idle",
            directional=True,
            loop=True,
            priority=0,
            directions={
                "down": {"frames": 4, "row": 0},
                "up": {"frames": 4, "row": 1},
                "right": {"frames": 4, "row": 2},
            },
        )
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": idle_cfg},
        )

        assert "idle_down" in sprite.animation_textures
        assert "idle_up" in sprite.animation_textures
        assert "idle_right" in sprite.animation_textures
        assert "idle_left" in sprite.animation_textures  # auto-flipped from right

    def test_initialization_with_walk_state(self, sprite_sheet_path: Path) -> None:
        """Test initialization with idle and walk states."""
        states = {
            "idle": AnimationStateConfig(
                name="idle",
                directional=True,
                loop=True,
                priority=0,
                directions={"down": {"frames": 4, "row": 0}},
            ),
            "walk": AnimationStateConfig(
                name="walk",
                directional=True,
                loop=True,
                priority=1,
                directions={"down": {"frames": 6, "row": 1}},
            ),
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        assert "idle_down" in sprite.animation_textures
        assert "walk_down" in sprite.animation_textures
        assert len(sprite.animation_textures["idle_down"]) == 4
        assert len(sprite.animation_textures["walk_down"]) == 6

    def test_initialization_position_and_scale(self, sprite_sheet_path: Path) -> None:
        """Test that position and scale are set correctly."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            scale=2.0,
            center_x=100.0,
            center_y=200.0,
            states={"idle": make_idle_state()},
        )

        assert sprite.center_x == 100.0
        assert sprite.center_y == 200.0
        assert sprite.scale == (2.0, 2.0)

    def test_initialization_only_right_walk_autogenerates_left(self, sprite_sheet_path: Path) -> None:
        """Test that defining only the right walk animation auto-generates left."""
        states = {
            "idle": AnimationStateConfig(
                name="idle",
                directional=True,
                loop=True,
                priority=0,
                directions={"right": {"frames": 4, "row": 0}},
            ),
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        assert sprite.animation_textures.get("idle_right")
        assert sprite.animation_textures.get("idle_left")

    def test_initialization_only_left_walk_autogenerates_right(self, sprite_sheet_path: Path) -> None:
        """Test that defining only the left animation auto-generates right."""
        states = {
            "idle": AnimationStateConfig(
                name="idle",
                directional=True,
                loop=True,
                priority=0,
                directions={"left": {"frames": 4, "row": 0}},
            ),
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        assert sprite.animation_textures.get("idle_left")
        assert sprite.animation_textures.get("idle_right")

    def test_initialization_default_direction_is_down(self, sprite_sheet_path: Path) -> None:
        """Test that default direction is down."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state()},
        )
        assert sprite.current_direction == "down"

    def test_initial_texture_set_from_idle_down(self, sprite_sheet_path: Path) -> None:
        """Test that initial texture is set from idle_down."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state(row=0, frames=4)},
        )
        assert sprite.texture is not None
        assert sprite.texture == sprite.animation_textures["idle_down"][0]


class TestAnimatedSpriteStateMachineAPI:
    """Tests for the state machine API: request_state, release_state, etc."""

    def test_has_state_returns_true_for_defined_state(self, sprite_sheet_path: Path) -> None:
        """Test has_state returns True for a defined state."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state(), "walk": make_walk_state()},
        )
        assert sprite.has_state("idle")
        assert sprite.has_state("walk")

    def test_has_state_returns_false_for_undefined_state(self, sprite_sheet_path: Path) -> None:
        """Test has_state returns False for an undefined state."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state()},
        )
        assert not sprite.has_state("appear")
        assert not sprite.has_state("nonexistent")

    def test_request_state_adds_to_active_states(self, sprite_sheet_path: Path) -> None:
        """Test request_state activates a state."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state(), "walk": make_walk_state()},
        )
        sprite.request_state("walk")
        assert "walk" in sprite._active_states

    def test_release_state_removes_from_active_states(self, sprite_sheet_path: Path) -> None:
        """Test release_state deactivates a continuous state."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state(), "walk": make_walk_state()},
        )
        sprite.request_state("walk")
        sprite.release_state("walk")
        assert "walk" not in sprite._active_states

    def test_idle_cannot_be_released(self, sprite_sheet_path: Path) -> None:
        """Test that idle state cannot be released."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state()},
        )
        sprite.release_state("idle")
        assert "idle" in sprite._active_states

    def test_request_unknown_state_logs_warning(self, sprite_sheet_path: Path) -> None:
        """Test that requesting an unknown state doesn't crash."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state()},
        )
        # Should not raise, just log a warning
        sprite.request_state("nonexistent")

    def test_is_state_complete_false_initially(self, sprite_sheet_path: Path) -> None:
        """Test that one-shot state completion starts as False."""
        appear_cfg = AnimationStateConfig(
            name="appear",
            directional=False,
            loop=False,
            priority=3,
            on_complete="idle",
            frames=5,
            row=8,
        )
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state(), "appear": appear_cfg},
        )
        assert not sprite.is_state_complete("appear")

    def test_mark_state_complete_sets_flag(self, sprite_sheet_path: Path) -> None:
        """Test mark_state_complete sets the completion flag."""
        appear_cfg = AnimationStateConfig(
            name="appear",
            directional=False,
            loop=False,
            priority=3,
            on_complete="idle",
            frames=5,
            row=8,
        )
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state(), "appear": appear_cfg},
        )
        sprite.mark_state_complete("appear")
        assert sprite.is_state_complete("appear")

    def test_reset_state_clears_completion_flag(self, sprite_sheet_path: Path) -> None:
        """Test reset_state clears the completion flag."""
        appear_cfg = AnimationStateConfig(
            name="appear",
            directional=False,
            loop=False,
            priority=3,
            on_complete="idle",
            frames=5,
            row=8,
        )
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state(), "appear": appear_cfg},
        )
        sprite.mark_state_complete("appear")
        sprite.reset_state("appear")
        assert not sprite.is_state_complete("appear")


class TestAnimatedSpriteDirection:
    """Tests for direction management."""

    def test_set_direction_changes_direction(self, sprite_sheet_path: Path) -> None:
        """Test direction changes via set_direction."""
        states = {
            "idle": AnimationStateConfig(
                name="idle",
                directional=True,
                loop=True,
                priority=0,
                directions={"down": {"frames": 4, "row": 0}, "up": {"frames": 4, "row": 1}},
            ),
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.current_direction = "up"
        sprite.set_direction("down")
        assert sprite.current_direction == "down"

    def test_set_direction_same_direction_no_change(self, sprite_sheet_path: Path) -> None:
        """Test no-op when setting the same direction."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state()},
        )
        sprite.current_direction = "down"
        sprite.set_direction("down")
        assert sprite.current_direction == "down"

    def test_set_direction_resets_frame(self, sprite_sheet_path: Path) -> None:
        """Test that changing direction resets the animation frame."""
        states = {
            "idle": AnimationStateConfig(
                name="idle",
                directional=True,
                loop=True,
                priority=0,
                directions={"down": {"frames": 4, "row": 0}, "up": {"frames": 4, "row": 1}},
            ),
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.current_frame = 3
        sprite.set_direction("up")
        assert sprite.current_frame == 0


class TestAnimatedSpriteUpdateAnimation:
    """Tests for update_animation behavior."""

    def test_update_animation_no_textures_returns_none(self, sprite_sheet_path: Path) -> None:
        """Test that update_animation returns None when no textures are loaded."""
        # A sprite with empty states should not crash
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state()},
        )
        # Manually clear textures to simulate no loaded textures
        sprite.animation_textures.clear()
        result = sprite.update_animation()
        assert result is None

    def test_update_animation_resets_frame_if_exceeds_animation_length(self, sprite_sheet_path: Path) -> None:
        """Test the animation resets frame if it exceeds animation length."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state(row=0, frames=4)},
        )
        sprite.current_frame = 8
        sprite.update_animation()
        assert sprite.current_frame == 0

    def test_update_animation_advances_timer(self, sprite_sheet_path: Path) -> None:
        """Test that update_animation advances the timer correctly."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state()},
        )
        sprite.animation_speed = 0.1
        sprite.update_animation(delta_time=0.05)
        assert sprite.animation_timer == 0.05

    def test_update_animation_advances_frame_when_timer_exceeded(self, sprite_sheet_path: Path) -> None:
        """Test that frame advances when timer exceeds animation_speed."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state(row=0, frames=4)},
        )
        sprite.animation_speed = 0.1
        sprite.update_animation(delta_time=0.05)
        assert sprite.current_frame == 0
        sprite.update_animation(delta_time=0.06)
        assert sprite.current_frame == 1
        assert sprite.animation_timer == 0.0

    def test_looping_animation_wraps_around(self, sprite_sheet_path: Path) -> None:
        """Test that looping animation wraps back to frame 0."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state(row=0, frames=2)},
        )
        sprite.animation_speed = 0.1
        # Advance 3 times (past end of 2-frame animation)
        for _ in range(3):
            sprite.update_animation(delta_time=0.11)
        assert sprite.current_frame == 1  # 3 % 2 = 1

    def test_walk_state_plays_when_requested(self, sprite_sheet_path: Path) -> None:
        """Test that walk state plays after request_state."""
        states = {
            "idle": make_idle_state(row=0),
            "walk": make_walk_state(row=1),
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.animation_speed = 0.1
        sprite.request_state("walk")
        sprite.update_animation(delta_time=0.11)
        # Walk state should be playing (priority 1 > idle priority 0)
        assert sprite._current_playing == "walk"

    def test_idle_plays_after_walk_released(self, sprite_sheet_path: Path) -> None:
        """Test that idle plays after walk state is released."""
        states = {
            "idle": make_idle_state(row=0),
            "walk": make_walk_state(row=1),
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.request_state("walk")
        sprite.update_animation(delta_time=0.11)
        sprite.release_state("walk")
        sprite.update_animation(delta_time=0.11)
        assert sprite._current_playing == "idle"


class TestAnimatedSpritePriority:
    """Tests for priority-based state resolution."""

    def test_higher_priority_state_plays(self, sprite_sheet_path: Path) -> None:
        """Test that highest-priority active state plays."""
        appear_cfg = AnimationStateConfig(
            name="appear",
            directional=False,
            loop=False,
            priority=3,
            on_complete="idle",
            frames=5,
            row=8,
        )
        states = {
            "idle": make_idle_state(row=0),
            "walk": make_walk_state(row=1),
            "appear": appear_cfg,
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.request_state("walk")
        sprite.request_state("appear")
        sprite.animation_speed = 0.1
        sprite.update_animation(delta_time=0.11)
        assert sprite._current_playing == "appear"

    def test_walk_plays_over_idle(self, sprite_sheet_path: Path) -> None:
        """Test that walk (priority 1) takes precedence over idle (priority 0)."""
        states = {
            "idle": make_idle_state(row=0),
            "walk": make_walk_state(row=1),
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.request_state("walk")
        sprite.animation_speed = 0.1
        sprite.update_animation(delta_time=0.11)
        assert sprite._current_playing == "walk"


class TestAnimatedSpriteOneShot:
    """Tests for one-shot animation state completion."""

    def test_one_shot_completes_and_sets_flag(self, sprite_sheet_path: Path) -> None:
        """Test that a one-shot state sets the completion flag when done."""
        appear_cfg = AnimationStateConfig(
            name="appear",
            directional=False,
            loop=False,
            priority=3,
            on_complete="idle",
            frames=3,
            row=8,
        )
        states = {
            "idle": make_idle_state(row=0),
            "appear": appear_cfg,
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.animation_speed = 0.1
        sprite.request_state("appear")

        # Advance through all 3 frames
        for _ in range(3):
            sprite.update_animation(delta_time=0.11)

        assert sprite.is_state_complete("appear")
        assert "appear" not in sprite._active_states

    def test_one_shot_on_complete_hide_makes_invisible(self, sprite_sheet_path: Path) -> None:
        """Test that on_complete='hide' makes sprite invisible."""
        disappear_cfg = AnimationStateConfig(
            name="disappear",
            directional=False,
            loop=False,
            priority=4,
            on_complete="hide",
            frames=3,
            row=8,
        )
        states = {
            "idle": make_idle_state(row=0),
            "disappear": disappear_cfg,
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.animation_speed = 0.1
        sprite.visible = True
        sprite.request_state("disappear")

        for _ in range(3):
            sprite.update_animation(delta_time=0.11)

        assert sprite.is_state_complete("disappear")
        assert not sprite.visible

    def test_request_state_resets_completion_flag(self, sprite_sheet_path: Path) -> None:
        """Test that re-requesting a completed one-shot state resets the flag."""
        appear_cfg = AnimationStateConfig(
            name="appear",
            directional=False,
            loop=False,
            priority=3,
            on_complete="idle",
            frames=3,
            row=8,
        )
        states = {
            "idle": make_idle_state(row=0),
            "appear": appear_cfg,
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.animation_speed = 0.1
        sprite.request_state("appear")

        for _ in range(3):
            sprite.update_animation(delta_time=0.11)

        assert sprite.is_state_complete("appear")

        # Re-request resets the flag
        sprite.request_state("appear")
        assert not sprite.is_state_complete("appear")


class TestAnimatedSpriteAutoFrom:
    """Tests for auto_from state generation (e.g. disappear from appear)."""

    def test_auto_from_generates_reversed_frames(self, sprite_sheet_path: Path) -> None:
        """Test that auto_from generates reversed frames from source state."""
        appear_cfg = AnimationStateConfig(
            name="appear",
            directional=False,
            loop=False,
            priority=3,
            on_complete="idle",
            frames=5,
            row=8,
        )
        disappear_cfg = AnimationStateConfig(
            name="disappear",
            directional=False,
            loop=False,
            priority=4,
            on_complete="hide",
            auto_from="appear",
        )
        states = {
            "idle": make_idle_state(row=0),
            "appear": appear_cfg,
            "disappear": disappear_cfg,
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        assert len(sprite.animation_textures["appear"]) == 5
        assert len(sprite.animation_textures["disappear"]) == 5
        # Disappear should be the reverse of appear
        assert sprite.animation_textures["disappear"] == list(reversed(sprite.animation_textures["appear"]))

    def test_auto_from_directional_generates_reversed_frames(self, sprite_sheet_path: Path) -> None:
        """Test that directional auto_from generates reversed frames per direction."""
        walk_cfg = AnimationStateConfig(
            name="walk",
            directional=True,
            loop=True,
            priority=1,
            directions={
                "down": {"frames": 4, "row": 1},
                "right": {"frames": 4, "row": 2},
            },
        )
        walk_back_cfg = AnimationStateConfig(
            name="walk_back",
            directional=True,
            loop=True,
            priority=2,
            auto_from="walk",
        )
        states = {
            "idle": make_idle_state(row=0),
            "walk": walk_cfg,
            "walk_back": walk_back_cfg,
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        assert sprite.animation_textures["walk_back_down"] == list(reversed(sprite.animation_textures["walk_down"]))
        assert sprite.animation_textures["walk_back_right"] == list(reversed(sprite.animation_textures["walk_right"]))

    def test_auto_from_missing_source_produces_empty_list(self, sprite_sheet_path: Path) -> None:
        """Test that auto_from with missing source leaves empty texture list."""
        ghost_cfg = AnimationStateConfig(
            name="ghost",
            directional=False,
            loop=False,
            priority=2,
            auto_from="nonexistent",
        )
        states = {
            "idle": make_idle_state(row=0),
            "ghost": ghost_cfg,
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        assert sprite.animation_textures.get("ghost") == []


class TestFromDefinition:
    """Tests for AnimatedSprite.from_definition classmethod."""

    def test_from_definition_basic(self, sprite_sheet_path: Path) -> None:
        """Test creating a sprite from a definition dict."""
        sprite_def = {
            "sprite_sheet": str(sprite_sheet_path),
            "frame_width": 16,
            "states": {
                "idle": {
                    "directional": True,
                    "loop": True,
                    "priority": 0,
                    "directions": {"down": {"frames": 4, "row": 0}},
                }
            },
        }
        sprite = AnimatedSprite.from_definition(sprite_def)
        assert "idle_down" in sprite.animation_textures

    def test_from_definition_with_scale_override(self, sprite_sheet_path: Path) -> None:
        """Test that scale override works in from_definition."""
        sprite_def = {
            "sprite_sheet": str(sprite_sheet_path),
            "frame_width": 16,
            "states": {
                "idle": {
                    "directional": True,
                    "loop": True,
                    "priority": 0,
                    "directions": {"down": {"frames": 4, "row": 0}},
                }
            },
        }
        sprite = AnimatedSprite.from_definition(sprite_def, scale=2.0, center_x=10.0, center_y=20.0)
        assert sprite.scale == (2.0, 2.0)
        assert sprite.center_x == 10.0
        assert sprite.center_y == 20.0

    def test_from_definition_with_tile_size_override(self, sprite_sheet_path: Path) -> None:
        """Test that tile_size override works in from_definition."""
        sprite_def = {
            "sprite_sheet": str(sprite_sheet_path),
            "frame_width": 32,
            "states": {
                "idle": {
                    "directional": True,
                    "loop": True,
                    "priority": 0,
                    "directions": {"down": {"frames": 2, "row": 0}},
                }
            },
        }
        sprite = AnimatedSprite.from_definition(sprite_def, tile_size=16)
        assert sprite.tile_size == 16

    def test_from_definition_uses_frame_width_when_no_tile_size(self, sprite_sheet_path: Path) -> None:
        """Test that frame_width is used as tile_size when tile_size is not given."""
        sprite_def = {
            "sprite_sheet": str(sprite_sheet_path),
            "frame_width": 16,
            "states": {
                "idle": {
                    "directional": True,
                    "loop": True,
                    "priority": 0,
                    "directions": {"down": {"frames": 4, "row": 0}},
                }
            },
        }
        sprite = AnimatedSprite.from_definition(sprite_def)
        assert sprite.tile_size == 16


class TestResolvingAndEdgeCases:
    """Tests for edge cases in state resolution and animation."""

    def test_update_animation_with_empty_active_states_returns_none(self, sprite_sheet_path: Path) -> None:
        """Test update_animation returns early when no active states resolve."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state()},
        )
        # Force empty active states to hit the _resolve_playing_state None branch
        sprite._active_states.clear()
        result = sprite.update_animation()
        assert result is None

    def test_request_state_same_playing_does_not_reset_frame(self, sprite_sheet_path: Path) -> None:
        """Test that request_state doesn't reset frame if playing state doesn't change."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state(row=0, frames=4)},
        )
        sprite.animation_speed = 0.1
        # Advance to frame 2
        for _ in range(2):
            sprite.update_animation(delta_time=0.11)
        assert sprite.current_frame == 2

        # Request idle again — playing state stays "idle", frame should not reset
        sprite.request_state("idle")
        assert sprite.current_frame == 2

    def test_reset_state_for_nonexistent_state_is_noop(self, sprite_sheet_path: Path) -> None:
        """Test that reset_state for an undefined state is a no-op."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state()},
        )
        sprite.reset_state("nonexistent")  # should not raise

    def test_mark_state_complete_for_nonexistent_state_is_noop(self, sprite_sheet_path: Path) -> None:
        """Test that mark_state_complete for an undefined state is a no-op."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state()},
        )
        sprite.mark_state_complete("nonexistent")  # should not raise

    def test_update_animation_clamps_frame_after_direction_change(self, sprite_sheet_path: Path) -> None:
        """Test frame clamping when switching to a shorter animation mid-playback."""
        states = {
            "idle": AnimationStateConfig(
                name="idle",
                directional=True,
                loop=True,
                priority=0,
                directions={
                    "down": {"frames": 4, "row": 0},
                    "up": {"frames": 2, "row": 1},
                },
            ),
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        # Establish idle as the current playing state
        sprite.update_animation(delta_time=0.01)
        assert sprite._current_playing == "idle"
        # Simulate a direction change mid-playback: set direction directly then force frame out of bounds
        sprite.current_direction = "up"
        sprite.current_frame = 3  # valid for down (4 frames) but not up (2 frames)
        sprite.update_animation(delta_time=0.01)
        assert sprite.current_frame == 0  # clamped


class TestLoadDirectionalEdgeCases:
    """Tests for directional loading edge cases."""

    def test_load_directional_state_no_directions_skips(self, sprite_sheet_path: Path) -> None:
        """Test that a directional state with no directions dict is skipped."""
        idle_cfg = AnimationStateConfig(
            name="idle",
            directional=True,
            loop=True,
            priority=0,
            directions=None,  # explicitly no directions
        )
        # Should not crash; no textures loaded for idle
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": idle_cfg},
        )
        assert sprite.animation_textures.get("idle_down") == []

    def test_reverse_load_loads_frames_in_reverse_order(self, sprite_sheet_path: Path) -> None:
        """Test that reverse_load loads frames in reverse order from the sprite sheet."""
        appear_cfg = AnimationStateConfig(
            name="appear",
            directional=False,
            loop=False,
            priority=3,
            frames=4,
            row=5,
            reverse_load=True,
        )
        normal_cfg = AnimationStateConfig(
            name="normal",
            directional=False,
            loop=False,
            priority=2,
            frames=4,
            row=5,
        )
        states = {
            "idle": make_idle_state(row=0),
            "appear": appear_cfg,
            "normal": normal_cfg,
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        # reverse_load should produce the same frames as normal load but in reverse order
        assert len(sprite.animation_textures["appear"]) == 4
        appear_images = [t.image.tobytes() for t in sprite.animation_textures["appear"]]
        normal_images = [t.image.tobytes() for t in sprite.animation_textures["normal"]]
        assert appear_images == list(reversed(normal_images))

    def test_load_nondirectional_state_no_frames_skips(self, sprite_sheet_path: Path) -> None:
        """Test that a non-directional state with no frames/row is skipped."""
        appear_cfg = AnimationStateConfig(
            name="appear",
            directional=False,
            loop=False,
            priority=3,
            frames=None,
            row=None,
        )
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            states={"idle": make_idle_state(), "appear": appear_cfg},
        )
        assert sprite.animation_textures.get("appear") == []

    def test_load_paired_both_sides_defined(self, sprite_sheet_path: Path) -> None:
        """Test that when both left and right rows are defined, both are loaded independently."""
        idle_cfg = AnimationStateConfig(
            name="idle",
            directional=True,
            loop=True,
            priority=0,
            directions={
                "left": {"frames": 4, "row": 0},
                "right": {"frames": 4, "row": 1},
            },
        )
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states={"idle": idle_cfg})

        # Both loaded from distinct rows — pixels should differ
        assert len(sprite.animation_textures["idle_left"]) == 4
        assert len(sprite.animation_textures["idle_right"]) == 4
        # They come from different rows so the image data should differ
        left_img = sprite.animation_textures["idle_left"][0].image
        right_img = sprite.animation_textures["idle_right"][0].image
        assert left_img.tobytes() != right_img.tobytes()


class TestSetInitialTextureFallbacks:
    """Tests for _set_initial_texture fallback logic."""

    def test_initial_texture_falls_back_to_walk_down(self, sprite_sheet_path: Path) -> None:
        """Test _set_initial_texture falls back to walk_down when no idle."""
        walk_cfg = AnimationStateConfig(
            name="walk",
            directional=True,
            loop=True,
            priority=1,
            directions={"down": {"frames": 4, "row": 1}},
        )
        idle_cfg = AnimationStateConfig(
            name="idle",
            directional=True,
            loop=True,
            priority=0,
            directions=None,  # no textures
        )
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states={"idle": idle_cfg, "walk": walk_cfg})
        assert sprite.texture == sprite.animation_textures["walk_down"][0]

    def test_initial_texture_falls_back_to_nondirectional_state(self, sprite_sheet_path: Path) -> None:
        """Test _set_initial_texture falls back to any non-directional state."""
        idle_cfg = AnimationStateConfig(
            name="idle",
            directional=True,
            loop=True,
            priority=0,
            directions=None,  # no textures
        )
        appear_cfg = AnimationStateConfig(
            name="appear",
            directional=False,
            loop=False,
            priority=3,
            frames=3,
            row=8,
        )
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states={"idle": idle_cfg, "appear": appear_cfg})
        assert sprite.texture == sprite.animation_textures["appear"][0]

    def test_initial_texture_logs_warning_when_no_textures(
        self, sprite_sheet_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test _set_initial_texture logs a warning when no textures can be found."""
        idle_cfg = AnimationStateConfig(
            name="idle",
            directional=True,
            loop=True,
            priority=0,
            directions=None,
        )
        with caplog.at_level(logging.WARNING, logger="pedre.sprites.animated_sprite"):
            AnimatedSprite(str(sprite_sheet_path), tile_size=16, states={"idle": idle_cfg})

        assert any("No animation textures" in r.message for r in caplog.records)
