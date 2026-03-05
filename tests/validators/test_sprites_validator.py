"""Tests for SpritesValidator."""

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from pedre.validators.context import ValidationContext
from pedre.validators.sprites_validator import SpritesValidator

if TYPE_CHECKING:
    from pathlib import Path


VALID_SPRITE = {
    "sprite_sheet": "path/to/sheet.png",
    "frame_width": 32,
    "frame_height": 32,
    "states": {
        "idle": {
            "directional": False,
            "loop": True,
            "priority": 0,
            "frames": 4,
            "row": 0,
        }
    },
}

VALID_DIRECTIONAL_SPRITE = {
    "sprite_sheet": "path/to/sheet.png",
    "frame_width": 32,
    "frame_height": 32,
    "states": {
        "walk": {
            "directional": True,
            "loop": True,
            "priority": 1,
            "directions": {
                "down": {"frames": 4, "row": 0},
                "up": {"frames": 4, "row": 1},
            },
        }
    },
}


class TestSpritesValidator:
    """Test SpritesValidator."""

    @pytest.fixture
    def context(self) -> ValidationContext:
        """Create a fresh ValidationContext for each test."""
        return ValidationContext()

    @pytest.fixture
    def valid_sprites_file(self, tmp_path: Path) -> Path:
        """Create a valid sprites.json file."""
        data = {
            "villager": VALID_SPRITE,
            "guard": VALID_DIRECTIONAL_SPRITE,
        }
        sprites_file = tmp_path / "sprites.json"
        sprites_file.write_text(json.dumps(data))
        return sprites_file

    def test_name_property(self, context: ValidationContext, valid_sprites_file: Path) -> None:
        """Validator name is 'Sprites'."""
        validator = SpritesValidator(valid_sprites_file, context)
        assert validator.name == "Sprites"

    def test_validate_valid_file_registers_sprites(self, context: ValidationContext, valid_sprites_file: Path) -> None:
        """Valid sprites are registered in context after validation."""
        validator = SpritesValidator(valid_sprites_file, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 2
        assert "villager" in context.get_sprite_ids()
        assert "guard" in context.get_sprite_ids()

    def test_validate_file_not_found(self, context: ValidationContext, tmp_path: Path) -> None:
        """Missing file produces a 'not found' error."""
        validator = SpritesValidator(tmp_path / "nonexistent.json", context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "not found" in result.errors[0]
        assert result.item_count == 0

    def test_validate_invalid_json(self, context: ValidationContext, tmp_path: Path) -> None:
        """Malformed JSON produces a 'Failed to parse' error."""
        sprites_file = tmp_path / "sprites.json"
        sprites_file.write_text("not valid json{")
        validator = SpritesValidator(sprites_file, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Failed to parse" in result.errors[0]

    def test_validate_root_not_dict(self, context: ValidationContext, tmp_path: Path) -> None:
        """Root JSON value that is not a dict produces a 'root must be a dictionary' error."""
        sprites_file = tmp_path / "sprites.json"
        sprites_file.write_text(json.dumps([VALID_SPRITE]))
        validator = SpritesValidator(sprites_file, context)
        result = validator.validate()

        assert any("root must be a dictionary" in e for e in result.errors)

    def test_validate_sprite_not_dict(self, context: ValidationContext, tmp_path: Path) -> None:
        """Sprite value that is not a dict produces an error; valid sprites are still registered."""
        data = {
            "bad_sprite": "not_a_dict",
            "valid_sprite": VALID_SPRITE,
        }
        sprites_file = tmp_path / "sprites.json"
        sprites_file.write_text(json.dumps(data))
        validator = SpritesValidator(sprites_file, context)
        result = validator.validate()

        assert any("must be a dictionary" in e for e in result.errors)
        assert result.item_count == 1
        assert "valid_sprite" in context.get_sprite_ids()

    def test_validate_sprite_missing_required_field(self, context: ValidationContext, tmp_path: Path) -> None:
        """Sprite missing required field produces an error and is not registered."""
        data = {"incomplete": {"sprite_sheet": "path.png", "frame_width": 32}}
        sprites_file = tmp_path / "sprites.json"
        sprites_file.write_text(json.dumps(data))
        validator = SpritesValidator(sprites_file, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert result.item_count == 0
        assert "incomplete" not in context.get_sprite_ids()

    def test_validate_state_invalid_on_complete(self, context: ValidationContext, tmp_path: Path) -> None:
        """State with invalid on_complete value produces an error."""
        sprite = {
            "sprite_sheet": "path.png",
            "frame_width": 32,
            "frame_height": 32,
            "states": {
                "idle": {
                    "directional": False,
                    "loop": True,
                    "priority": 0,
                    "frames": 4,
                    "row": 0,
                    "on_complete": "invalid_value",
                }
            },
        }
        sprites_file = tmp_path / "sprites.json"
        sprites_file.write_text(json.dumps({"bad": sprite}))
        validator = SpritesValidator(sprites_file, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert result.item_count == 0

    def test_validate_empty_file_is_valid(self, context: ValidationContext, tmp_path: Path) -> None:
        """An empty sprites dict is valid and registers no sprites."""
        sprites_file = tmp_path / "sprites.json"
        sprites_file.write_text(json.dumps({}))
        validator = SpritesValidator(sprites_file, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 0
        assert context.get_sprite_ids() == set()

    def test_validate_partial_errors_still_registers_valid_sprites(
        self, context: ValidationContext, tmp_path: Path
    ) -> None:
        """Valid sprites are registered even when other sprites in the file have errors."""
        data = {
            "valid_sprite": VALID_SPRITE,
            "invalid_sprite": {"sprite_sheet": "path.png"},
        }
        sprites_file = tmp_path / "sprites.json"
        sprites_file.write_text(json.dumps(data))
        validator = SpritesValidator(sprites_file, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert result.item_count == 1
        assert "valid_sprite" in context.get_sprite_ids()
        assert "invalid_sprite" not in context.get_sprite_ids()

    def test_validate_cross_references_returns_empty(
        self, context: ValidationContext, valid_sprites_file: Path
    ) -> None:
        """validate_cross_references returns an empty result (sprites are the authority)."""
        validator = SpritesValidator(valid_sprites_file, context)
        validator.validate()
        result = validator.validate_cross_references()

        assert result.errors == []
        assert result.item_count == 0

    def test_validate_os_error(self, context: ValidationContext, tmp_path: Path) -> None:
        """OSError while reading the file produces a 'Failed to load' error."""
        sprites_file = tmp_path / "sprites.json"
        sprites_file.write_text(json.dumps({}))
        validator = SpritesValidator(sprites_file, context)

        with patch("pathlib.Path.open", side_effect=PermissionError("Permission denied")):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "Failed to load" in result.errors[0]
        assert result.item_count == 0
