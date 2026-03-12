"""Tests for SpriteRegistry."""

import json
from typing import TYPE_CHECKING, Any

import pytest

from pedre.content.registries.sprite import SpriteRegistry
from pedre.content.registry import (
    ContentTypeRegistry,
    DuplicateIDError,
    InvalidDefinitionError,
)

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


@pytest.fixture(autouse=True)
def clean_registry() -> Generator[None]:
    """Clear ContentTypeRegistry before and after each test."""
    ContentTypeRegistry.clear()
    yield
    ContentTypeRegistry.clear()


@pytest.fixture
def registry() -> SpriteRegistry:
    """Return a fresh SpriteRegistry instance."""
    return SpriteRegistry()


VALID_STATE_NONDIRECTIONAL: dict[str, Any] = {
    "directional": False,
    "loop": True,
    "priority": 0,
    "frames": 4,
    "row": 0,
}

VALID_STATE_DIRECTIONAL: dict[str, Any] = {
    "directional": True,
    "loop": True,
    "priority": 0,
    "directions": {
        "down": {"frames": 4, "row": 0},
        "up": {"frames": 4, "row": 1},
    },
}


def make_sprite(states: object = None) -> dict[str, Any]:
    """Return a minimal valid sprite definition."""
    return {
        "sprite_sheet": "sprites/villager.png",
        "frame_width": 32,
        "frame_height": 32,
        "states": states if states is not None else {"idle": VALID_STATE_NONDIRECTIONAL},
    }


class TestSpriteRegistryMetadata:
    """Tests for SpriteRegistry class-level metadata attributes."""

    def test_name(self) -> None:
        """Registry name is 'sprites'."""
        assert SpriteRegistry.name == "sprites"

    def test_filename(self) -> None:
        """Registry loads from 'sprites.json'."""
        assert SpriteRegistry.filename == "sprites.json"

    def test_display_name(self) -> None:
        """Display name used in error messages is 'Sprite'."""
        assert SpriteRegistry.display_name == "Sprite"

    def test_registered_in_content_type_registry(self) -> None:
        """SpriteRegistry is discoverable by name after registration."""
        ContentTypeRegistry.register(SpriteRegistry)
        assert ContentTypeRegistry.is_registered("sprites")

    def test_valid_on_complete_values(self) -> None:
        """VALID_ON_COMPLETE contains the expected sentinel values."""
        assert {"idle", "hide"} == SpriteRegistry.VALID_ON_COMPLETE


class TestSpriteRegistryValidateTopLevel:
    """Tests for top-level required field validation."""

    def test_valid_minimal(self, registry: SpriteRegistry) -> None:
        """A definition with all required top-level fields passes validation."""
        registry.validate("villager", make_sprite())

    @pytest.mark.parametrize("missing_field", ["sprite_sheet", "frame_width", "frame_height", "states"])
    def test_missing_top_level_field(self, registry: SpriteRegistry, missing_field: str) -> None:
        """Missing any top-level required field raises InvalidDefinitionError."""
        defn = make_sprite()
        del defn[missing_field]
        with pytest.raises(InvalidDefinitionError, match=f"missing required field '{missing_field}'"):
            registry.validate("villager", defn)

    def test_states_not_dict_raises(self, registry: SpriteRegistry) -> None:
        """Non-dict 'states' value raises InvalidDefinitionError."""
        defn = make_sprite(states=["idle"])
        with pytest.raises(InvalidDefinitionError, match="states must be a dictionary"):
            registry.validate("villager", defn)


class TestSpriteRegistryValidateStateFields:
    """Tests for per-state required field validation."""

    @pytest.mark.parametrize("missing_field", ["directional", "loop", "priority"])
    def test_missing_state_required_field(self, registry: SpriteRegistry, missing_field: str) -> None:
        """Missing any of directional/loop/priority raises InvalidDefinitionError."""
        state = {**VALID_STATE_NONDIRECTIONAL}
        del state[missing_field]
        with pytest.raises(InvalidDefinitionError, match=f"missing required field '{missing_field}'"):
            registry.validate("villager", make_sprite(states={"idle": state}))

    def test_valid_non_directional_state(self, registry: SpriteRegistry) -> None:
        """A non-directional state with frames and row passes validation."""
        registry.validate("villager", make_sprite(states={"idle": VALID_STATE_NONDIRECTIONAL}))

    def test_valid_directional_state(self, registry: SpriteRegistry) -> None:
        """A directional state with a directions mapping passes validation."""
        registry.validate("villager", make_sprite(states={"walk": VALID_STATE_DIRECTIONAL}))

    def test_non_directional_missing_frames(self, registry: SpriteRegistry) -> None:
        """Non-directional state missing 'frames' raises InvalidDefinitionError."""
        state = {**VALID_STATE_NONDIRECTIONAL}
        del state["frames"]
        with pytest.raises(InvalidDefinitionError, match="missing required field 'frames'"):
            registry.validate("villager", make_sprite(states={"idle": state}))

    def test_non_directional_missing_row(self, registry: SpriteRegistry) -> None:
        """Non-directional state missing 'row' raises InvalidDefinitionError."""
        state = {**VALID_STATE_NONDIRECTIONAL}
        del state["row"]
        with pytest.raises(InvalidDefinitionError, match="missing required field 'row'"):
            registry.validate("villager", make_sprite(states={"idle": state}))

    def test_directional_missing_directions(self, registry: SpriteRegistry) -> None:
        """Directional state without 'directions' raises InvalidDefinitionError."""
        state = {**VALID_STATE_DIRECTIONAL}
        del state["directions"]
        with pytest.raises(InvalidDefinitionError, match="missing 'directions' mapping"):
            registry.validate("villager", make_sprite(states={"walk": state}))

    def test_directional_direction_missing_frames(self, registry: SpriteRegistry) -> None:
        """A direction entry missing 'frames' raises InvalidDefinitionError."""
        state = {
            **VALID_STATE_DIRECTIONAL,
            "directions": {"down": {"row": 0}},
        }
        with pytest.raises(InvalidDefinitionError, match="missing required field 'frames'"):
            registry.validate("villager", make_sprite(states={"walk": state}))

    def test_directional_direction_missing_row(self, registry: SpriteRegistry) -> None:
        """A direction entry missing 'row' raises InvalidDefinitionError."""
        state = {
            **VALID_STATE_DIRECTIONAL,
            "directions": {"down": {"frames": 4}},
        }
        with pytest.raises(InvalidDefinitionError, match="missing required field 'row'"):
            registry.validate("villager", make_sprite(states={"walk": state}))


class TestSpriteRegistryValidateStateOptions:
    """Tests for optional state fields: on_complete and auto_from."""

    def test_valid_on_complete_idle(self, registry: SpriteRegistry) -> None:
        """on_complete='idle' is accepted."""
        state = {**VALID_STATE_NONDIRECTIONAL, "on_complete": "idle"}
        registry.validate("villager", make_sprite(states={"attack": state}))

    def test_valid_on_complete_hide(self, registry: SpriteRegistry) -> None:
        """on_complete='hide' is accepted."""
        state = {**VALID_STATE_NONDIRECTIONAL, "on_complete": "hide"}
        registry.validate("villager", make_sprite(states={"attack": state}))

    def test_invalid_on_complete_raises(self, registry: SpriteRegistry) -> None:
        """An unknown on_complete value raises InvalidDefinitionError."""
        state = {**VALID_STATE_NONDIRECTIONAL, "on_complete": "explode"}
        with pytest.raises(InvalidDefinitionError, match="invalid on_complete 'explode'"):
            registry.validate("villager", make_sprite(states={"attack": state}))

    def test_auto_from_valid_reference(self, registry: SpriteRegistry) -> None:
        """auto_from referencing another state in the same definition passes."""
        states = {
            "walk": VALID_STATE_DIRECTIONAL,
            "walk_attack": {
                "directional": True,
                "loop": False,
                "priority": 1,
                "auto_from": "walk",
            },
        }
        registry.validate("villager", make_sprite(states=states))

    def test_auto_from_unknown_reference_raises(self, registry: SpriteRegistry) -> None:
        """auto_from referencing a non-existent state raises InvalidDefinitionError."""
        state = {
            "directional": False,
            "loop": False,
            "priority": 1,
            "auto_from": "nonexistent",
        }
        with pytest.raises(InvalidDefinitionError, match="auto_from references unknown state"):
            registry.validate("villager", make_sprite(states={"attack": state}))

    def test_auto_from_skips_frame_data_requirement(self, registry: SpriteRegistry) -> None:
        """A state with auto_from does not need frames/row/directions."""
        states = {
            "idle": VALID_STATE_NONDIRECTIONAL,
            "run": {
                "directional": False,
                "loop": True,
                "priority": 0,
                "auto_from": "idle",
                # no frames or row — should be fine
            },
        }
        registry.validate("villager", make_sprite(states=states))


class TestSpriteRegistryRegisterAndGet:
    """Tests for register(), get(), has(), and all() on SpriteRegistry."""

    def test_register_and_get(self, registry: SpriteRegistry) -> None:
        """Registered sprite can be retrieved by ID."""
        defn = make_sprite()
        registry.register("villager", defn)
        assert registry.get("villager") == defn

    def test_duplicate_raises(self, registry: SpriteRegistry) -> None:
        """Registering the same ID twice raises DuplicateIDError."""
        registry.register("villager", make_sprite())
        with pytest.raises(DuplicateIDError):
            registry.register("villager", make_sprite())

    def test_has(self, registry: SpriteRegistry) -> None:
        """has() returns True for registered IDs and False for unknown ones."""
        registry.register("villager", make_sprite())
        assert registry.has("villager")
        assert not registry.has("ghost")

    def test_all(self, registry: SpriteRegistry) -> None:
        """all() returns a dict of all registered sprites."""
        registry.register("villager", make_sprite())
        registry.register("guard", make_sprite())
        assert set(registry.all().keys()) == {"villager", "guard"}


class TestSpriteRegistryLoadFromFile:
    """Tests for SpriteRegistry.load_from_file()."""

    def test_load_valid_file(self, registry: SpriteRegistry, tmp_path: Path) -> None:
        """Valid sprites.json loads all sprites into the registry."""
        sprites_file = tmp_path / "sprites.json"
        sprites_file.write_text(
            json.dumps(
                {
                    "villager": make_sprite(),
                    "guard": make_sprite(),
                }
            )
        )
        registry.load_from_file(sprites_file)
        assert registry.has("villager")
        assert registry.has("guard")

    def test_load_invalid_sprite_raises(self, registry: SpriteRegistry, tmp_path: Path) -> None:
        """A sprite missing a required field raises InvalidDefinitionError during load."""
        sprites_file = tmp_path / "sprites.json"
        sprites_file.write_text(json.dumps({"bad": {"sprite_sheet": "x.png"}}))
        with pytest.raises(InvalidDefinitionError, match="missing required field"):
            registry.load_from_file(sprites_file)
