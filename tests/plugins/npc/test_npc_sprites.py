"""Tests for AnimatedSprite with NPC-type animation states.

AnimatedNPC has been removed. NPCs now use the generic AnimatedSprite with
data-driven state configs (appear, disappear, interact, idle, walk).
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
    tmp_path = tmp_path_factory.mktemp("npc_sprites")
    path = tmp_path / "test_npc_sprite.png"
    tile_size = 16
    rows = 12
    cols = 10

    image = Image.new("RGBA", (cols * tile_size, rows * tile_size), (0, 0, 0, 0))

    for row in range(rows):
        for col in range(cols):
            for x in range(tile_size):
                for y in range(tile_size):
                    pixel_x = col * tile_size + x
                    pixel_y = row * tile_size + y
                    color = (row * 20, col * 25, 128, 255)
                    image.putpixel((pixel_x, pixel_y), color)

    image.save(path)
    return path


def make_npc_states(
    *,
    include_appear: bool = False,
    include_disappear: bool = False,
    include_interact: bool = False,
    disappear_auto_from: bool = False,
) -> dict[str, AnimationStateConfig]:
    """Build a standard NPC state config dict."""
    states: dict[str, AnimationStateConfig] = {
        "idle": AnimationStateConfig(
            name="idle",
            directional=True,
            loop=True,
            priority=0,
            directions={"down": {"frames": 4, "row": 0}},
        ),
    }
    if include_appear:
        states["appear"] = AnimationStateConfig(
            name="appear",
            directional=False,
            loop=False,
            priority=3,
            on_complete="idle",
            reverse_load=True,
            frames=5,
            row=8,
        )
    if include_disappear:
        if disappear_auto_from and "appear" in states:
            states["disappear"] = AnimationStateConfig(
                name="disappear",
                directional=False,
                loop=False,
                priority=4,
                on_complete="hide",
                auto_from="appear",
            )
        else:
            states["disappear"] = AnimationStateConfig(
                name="disappear",
                directional=False,
                loop=False,
                priority=4,
                on_complete="hide",
                frames=5,
                row=8,
            )
    if include_interact:
        states["interact"] = AnimationStateConfig(
            name="interact",
            directional=True,
            loop=False,
            priority=5,
            on_complete="idle",
            directions={"down": {"frames": 3, "row": 2}},
        )
    return states


class TestNPCAnimatedSpriteInitialization:
    """Test NPC-type AnimatedSprite initialization."""

    def test_basic_initialization_idle_only(self, sprite_sheet_path: Path) -> None:
        """Test basic NPC sprite with idle state only."""
        states = make_npc_states()
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        assert sprite.has_state("idle")
        assert not sprite.has_state("appear")
        assert not sprite.has_state("disappear")
        assert not sprite.has_state("interact")
        assert "idle_down" in sprite.animation_textures

    def test_initialization_with_appear_state(self, sprite_sheet_path: Path) -> None:
        """Test NPC sprite with appear animation."""
        states = make_npc_states(include_appear=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        assert sprite.has_state("appear")
        assert len(sprite.animation_textures["appear"]) == 5
        assert not sprite.is_state_complete("appear")

    def test_initialization_with_disappear_auto_from_appear(self, sprite_sheet_path: Path) -> None:
        """Test NPC sprite with disappear auto-generated from appear."""
        states = make_npc_states(include_appear=True, include_disappear=True, disappear_auto_from=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        assert sprite.has_state("appear")
        assert sprite.has_state("disappear")
        assert len(sprite.animation_textures["appear"]) == 5
        assert len(sprite.animation_textures["disappear"]) == 5
        # Disappear frames should be the reverse of appear frames
        assert sprite.animation_textures["disappear"] == list(reversed(sprite.animation_textures["appear"]))

    def test_initialization_with_explicit_disappear(self, sprite_sheet_path: Path) -> None:
        """Test NPC sprite with independently defined disappear animation."""
        states = make_npc_states(include_appear=True, include_disappear=True, disappear_auto_from=False)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        assert len(sprite.animation_textures["appear"]) == 5
        assert len(sprite.animation_textures["disappear"]) == 5

    def test_initialization_with_interact_state(self, sprite_sheet_path: Path) -> None:
        """Test NPC sprite with interact animation."""
        states = make_npc_states(include_interact=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        assert sprite.has_state("interact")
        assert "interact_down" in sprite.animation_textures
        assert len(sprite.animation_textures["interact_down"]) == 3

    def test_initialization_with_all_npc_states(self, sprite_sheet_path: Path) -> None:
        """Test NPC sprite with all standard NPC states."""
        states = make_npc_states(
            include_appear=True,
            include_disappear=True,
            include_interact=True,
            disappear_auto_from=True,
        )
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        assert sprite.has_state("idle")
        assert sprite.has_state("appear")
        assert sprite.has_state("disappear")
        assert sprite.has_state("interact")

    def test_initial_completion_flags_false(self, sprite_sheet_path: Path) -> None:
        """Test that all one-shot states start with completion False."""
        states = make_npc_states(include_appear=True, include_disappear=True, include_interact=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        assert not sprite.is_state_complete("appear")
        assert not sprite.is_state_complete("disappear")
        assert not sprite.is_state_complete("interact")

    def test_position_and_scale(self, sprite_sheet_path: Path) -> None:
        """Test position and scale initialization."""
        sprite = AnimatedSprite(
            str(sprite_sheet_path),
            tile_size=16,
            scale=2.0,
            center_x=100,
            center_y=200,
            states=make_npc_states(),
        )
        assert sprite.center_x == 100
        assert sprite.center_y == 200
        assert sprite.scale == (2.0, 2.0)


class TestNPCAppearAnimation:
    """Tests for appear animation via state machine."""

    def test_request_appear_activates_state(self, sprite_sheet_path: Path) -> None:
        """Test that requesting appear state activates it."""
        states = make_npc_states(include_appear=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        sprite.request_state("appear")
        assert "appear" in sprite._active_states
        assert not sprite.is_state_complete("appear")

    def test_appear_advances_through_frames(self, sprite_sheet_path: Path) -> None:
        """Test appear animation advances through frames."""
        states = make_npc_states(include_appear=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.animation_speed = 0.1
        sprite.request_state("appear")

        # First update — advances timer
        sprite.update_animation(delta_time=0.05)
        assert sprite.current_frame == 0
        assert sprite.animation_timer == 0.05

        # Second update — advances frame
        sprite.update_animation(delta_time=0.06)
        assert sprite.current_frame == 1
        assert sprite.animation_timer == 0.0

    def test_appear_completes_after_all_frames(self, sprite_sheet_path: Path) -> None:
        """Test appear animation completes and sets flag."""
        states = make_npc_states(include_appear=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.animation_speed = 0.1
        sprite.request_state("appear")

        for _ in range(5):
            sprite.update_animation(delta_time=0.11)

        assert sprite.is_state_complete("appear")
        assert "appear" not in sprite._active_states
        assert sprite.current_frame == 0

    def test_appear_returns_to_idle_after_completion(self, sprite_sheet_path: Path) -> None:
        """Test that after appear completes, idle plays."""
        states = make_npc_states(include_appear=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.animation_speed = 0.1
        sprite.request_state("appear")

        for _ in range(5):
            sprite.update_animation(delta_time=0.11)

        # Next update should play idle
        sprite.update_animation(delta_time=0.11)
        assert sprite._current_playing == "idle"


class TestNPCDisappearAnimation:
    """Tests for disappear animation via state machine."""

    def test_request_disappear_activates_state(self, sprite_sheet_path: Path) -> None:
        """Test that requesting disappear state activates it."""
        states = make_npc_states(include_disappear=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        sprite.request_state("disappear")
        assert "disappear" in sprite._active_states
        assert not sprite.is_state_complete("disappear")

    def test_disappear_advances_through_frames(self, sprite_sheet_path: Path) -> None:
        """Test disappear animation advances through frames."""
        states = make_npc_states(include_disappear=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.animation_speed = 0.1
        sprite.request_state("disappear")

        sprite.update_animation(delta_time=0.05)
        assert sprite.current_frame == 0

        sprite.update_animation(delta_time=0.06)
        assert sprite.current_frame == 1

    def test_disappear_completes_and_hides_sprite(self, sprite_sheet_path: Path) -> None:
        """Test disappear animation completes and sets visible=False."""
        states = make_npc_states(include_disappear=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.animation_speed = 0.1
        sprite.visible = True
        sprite.request_state("disappear")

        for _ in range(5):
            sprite.update_animation(delta_time=0.11)

        assert sprite.is_state_complete("disappear")
        assert not sprite.visible
        assert sprite.current_frame == 0


class TestNPCInteractAnimation:
    """Tests for interact animation via state machine."""

    def test_request_interact_activates_state(self, sprite_sheet_path: Path) -> None:
        """Test that requesting interact state activates it."""
        states = make_npc_states(include_interact=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        sprite.request_state("interact")
        assert "interact" in sprite._active_states
        assert not sprite.is_state_complete("interact")

    def test_interact_advances_through_frames(self, sprite_sheet_path: Path) -> None:
        """Test interact animation advances through frames."""
        states = make_npc_states(include_interact=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.animation_speed = 0.1
        sprite.current_direction = "down"
        sprite.request_state("interact")

        sprite.update_animation(delta_time=0.05)
        assert sprite.current_frame == 0
        assert sprite.animation_timer == 0.05

        # This call advances current_frame to 1 but texture is updated at start of next call
        sprite.update_animation(delta_time=0.06)
        assert sprite.current_frame == 1
        assert sprite.animation_timer == 0.0

        # Texture for frame 1 is applied at the start of the next update_animation call
        sprite.update_animation(delta_time=0.05)
        assert sprite.texture == sprite.animation_textures["interact_down"][1]

    def test_interact_completes_and_returns_to_idle(self, sprite_sheet_path: Path) -> None:
        """Test interact animation completes and returns to idle."""
        states = make_npc_states(include_interact=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.animation_speed = 0.1
        sprite.current_direction = "down"
        sprite.request_state("interact")

        for _ in range(3):
            sprite.update_animation(delta_time=0.11)

        assert sprite.is_state_complete("interact")
        assert "interact" not in sprite._active_states
        assert sprite.current_frame == 0


class TestNPCAnimationPriority:
    """Tests for priority resolution among NPC states."""

    def test_interact_takes_priority_over_walk(self, sprite_sheet_path: Path) -> None:
        """Test interact (priority 5) takes priority over walk (priority 1)."""
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
                directions={"down": {"frames": 4, "row": 1}},
            ),
            "interact": AnimationStateConfig(
                name="interact",
                directional=True,
                loop=False,
                priority=5,
                on_complete="idle",
                directions={"down": {"frames": 3, "row": 2}},
            ),
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.animation_speed = 0.1
        sprite.current_direction = "down"
        sprite.request_state("walk")
        sprite.request_state("interact")
        sprite.update_animation(delta_time=0.11)
        assert sprite._current_playing == "interact"

    def test_disappear_takes_priority_over_appear(self, sprite_sheet_path: Path) -> None:
        """Test disappear (priority 4) takes priority over appear (priority 3)."""
        states = make_npc_states(include_appear=True, include_disappear=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.animation_speed = 0.1
        sprite.request_state("appear")
        sprite.request_state("disappear")
        sprite.update_animation(delta_time=0.11)
        assert sprite._current_playing == "disappear"

    def test_appear_takes_priority_over_walk(self, sprite_sheet_path: Path) -> None:
        """Test appear (priority 3) takes priority over walk (priority 1)."""
        walk_cfg = AnimationStateConfig(
            name="walk",
            directional=True,
            loop=True,
            priority=1,
            directions={"down": {"frames": 4, "row": 1}},
        )
        states = {
            "idle": AnimationStateConfig(
                name="idle",
                directional=True,
                loop=True,
                priority=0,
                directions={"down": {"frames": 4, "row": 0}},
            ),
            "walk": walk_cfg,
            "appear": AnimationStateConfig(
                name="appear",
                directional=False,
                loop=False,
                priority=3,
                on_complete="idle",
                frames=5,
                row=8,
            ),
        }
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.animation_speed = 0.1
        sprite.request_state("walk")
        sprite.request_state("appear")
        sprite.update_animation(delta_time=0.11)
        assert sprite._current_playing == "appear"


class TestNPCStatePersistence:
    """Tests for save/restore state machine persistence."""

    def test_mark_state_complete_for_save_restore(self, sprite_sheet_path: Path) -> None:
        """Test mark_state_complete can be used to restore saved appear state."""
        states = make_npc_states(include_appear=True, include_disappear=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)

        # Simulate restoring a saved state where appear was already complete
        sprite.mark_state_complete("appear")

        assert sprite.is_state_complete("appear")
        assert not sprite.is_state_complete("disappear")

    def test_reset_state_allows_replaying(self, sprite_sheet_path: Path) -> None:
        """Test reset_state allows one-shot animation to be played again."""
        states = make_npc_states(include_appear=True)
        sprite = AnimatedSprite(str(sprite_sheet_path), tile_size=16, states=states)
        sprite.animation_speed = 0.1
        sprite.request_state("appear")

        for _ in range(5):
            sprite.update_animation(delta_time=0.11)

        assert sprite.is_state_complete("appear")

        sprite.reset_state("appear")
        assert not sprite.is_state_complete("appear")

        # Should be able to replay
        sprite.request_state("appear")
        assert "appear" in sprite._active_states
