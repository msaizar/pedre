"""Tests for PlayerValidator."""

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from pedre.validators.context import ValidationContext
from pedre.validators.player_validator import PlayerValidator

if TYPE_CHECKING:
    from pathlib import Path


class TestPlayerValidator:
    """Test PlayerValidator."""

    @pytest.fixture
    def context(self) -> ValidationContext:
        """Create a fresh ValidationContext for each test."""
        return ValidationContext()

    @pytest.fixture
    def context_with_sprites(self) -> ValidationContext:
        """Create a ValidationContext pre-populated with sprite IDs."""
        ctx = ValidationContext()
        ctx.add_sprite_id("hero")
        ctx.add_sprite_id("archer")
        return ctx

    @pytest.fixture
    def valid_players_file(self, tmp_path: Path) -> Path:
        """Create a valid players.json file."""
        data = {
            "player1": {"sprite_id": "hero"},
            "player2": {"sprite_id": "archer"},
        }
        players_file = tmp_path / "players.json"
        players_file.write_text(json.dumps(data))
        return players_file

    def test_name_property(self, context: ValidationContext, valid_players_file: Path) -> None:
        """Validator name is 'Players'."""
        validator = PlayerValidator(valid_players_file, context)
        assert validator.name == "Players"

    def test_validate_valid_file_registers_players(self, context: ValidationContext, valid_players_file: Path) -> None:
        """Valid players are registered in context after validation."""
        validator = PlayerValidator(valid_players_file, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 2
        assert "player1" in context.get_player_ids()
        assert "player2" in context.get_player_ids()

    def test_validate_file_not_found(self, context: ValidationContext, tmp_path: Path) -> None:
        """Missing file produces a 'not found' error."""
        validator = PlayerValidator(tmp_path / "nonexistent.json", context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "not found" in result.errors[0]
        assert result.item_count == 0

    def test_validate_invalid_json(self, context: ValidationContext, tmp_path: Path) -> None:
        """Malformed JSON produces a 'Failed to parse' error."""
        players_file = tmp_path / "players.json"
        players_file.write_text("not valid json{")
        validator = PlayerValidator(players_file, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Failed to parse" in result.errors[0]

    def test_validate_root_not_dict(self, context: ValidationContext, tmp_path: Path) -> None:
        """Root JSON value that is not a dict produces a 'root must be a dictionary' error."""
        players_file = tmp_path / "players.json"
        players_file.write_text(json.dumps([{"sprite_id": "hero"}]))
        validator = PlayerValidator(players_file, context)
        result = validator.validate()

        assert any("root must be a dictionary" in e for e in result.errors)

    def test_validate_player_not_dict(self, context: ValidationContext, tmp_path: Path) -> None:
        """Player value that is not a dict produces an error; valid players are still registered."""
        data = {
            "bad_player": "not_a_dict",
            "valid_player": {"sprite_id": "hero"},
        }
        players_file = tmp_path / "players.json"
        players_file.write_text(json.dumps(data))
        validator = PlayerValidator(players_file, context)
        result = validator.validate()

        assert any("must be a dictionary" in e for e in result.errors)
        assert result.item_count == 1
        assert "valid_player" in context.get_player_ids()

    def test_validate_player_missing_sprite_id(self, context: ValidationContext, tmp_path: Path) -> None:
        """Player missing sprite_id produces an error and is not registered."""
        players_file = tmp_path / "players.json"
        players_file.write_text(json.dumps({"hero": {}}))
        validator = PlayerValidator(players_file, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert result.item_count == 0
        assert "hero" not in context.get_player_ids()

    def test_validate_player_with_spawn_at_position(self, context: ValidationContext, tmp_path: Path) -> None:
        """Player with valid spawn_at_position is accepted."""
        players_file = tmp_path / "players.json"
        players_file.write_text(json.dumps({"hero": {"sprite_id": "hero", "spawn_at_position": ["portal1", "map1"]}}))
        validator = PlayerValidator(players_file, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 1

    def test_validate_player_spawn_at_position_not_list(self, context: ValidationContext, tmp_path: Path) -> None:
        """Player with spawn_at_position that is not a list produces an error."""
        players_file = tmp_path / "players.json"
        players_file.write_text(json.dumps({"hero": {"sprite_id": "hero", "spawn_at_position": "portal1"}}))
        validator = PlayerValidator(players_file, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "hero" not in context.get_player_ids()

    def test_validate_player_spawn_at_position_non_string_item(
        self, context: ValidationContext, tmp_path: Path
    ) -> None:
        """Player with spawn_at_position containing non-string items produces an error."""
        players_file = tmp_path / "players.json"
        players_file.write_text(json.dumps({"hero": {"sprite_id": "hero", "spawn_at_position": [1, 2]}}))
        validator = PlayerValidator(players_file, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "hero" not in context.get_player_ids()

    def test_validate_empty_file_is_valid(self, context: ValidationContext, tmp_path: Path) -> None:
        """An empty players dict is valid and registers no players."""
        players_file = tmp_path / "players.json"
        players_file.write_text(json.dumps({}))
        validator = PlayerValidator(players_file, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 0
        assert context.get_player_ids() == set()

    def test_validate_os_error(self, context: ValidationContext, tmp_path: Path) -> None:
        """OSError while reading the file produces a 'Failed to load' error."""
        players_file = tmp_path / "players.json"
        players_file.write_text(json.dumps({}))
        validator = PlayerValidator(players_file, context)

        with patch("pathlib.Path.open", side_effect=PermissionError("Permission denied")):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "Failed to load" in result.errors[0]
        assert result.item_count == 0

    def test_validate_cross_references_valid(
        self, context_with_sprites: ValidationContext, valid_players_file: Path
    ) -> None:
        """Players referencing valid sprites pass cross-reference validation."""
        validator = PlayerValidator(valid_players_file, context_with_sprites)
        validator.validate()
        result = validator.validate_cross_references()

        assert result.errors == []

    def test_validate_cross_references_unknown_sprite(self, context: ValidationContext, tmp_path: Path) -> None:
        """Player referencing an unknown sprite produces a cross-reference error."""
        players_file = tmp_path / "players.json"
        players_file.write_text(json.dumps({"hero": {"sprite_id": "ghost_sprite"}}))
        validator = PlayerValidator(players_file, context)
        validator.validate()
        result = validator.validate_cross_references()

        assert len(result.errors) == 1
        assert "hero" in result.errors[0]
        assert "ghost_sprite" in result.errors[0]

    def test_validate_cross_references_no_sprites_in_context(
        self, context: ValidationContext, valid_players_file: Path
    ) -> None:
        """When no sprites are in context, all sprite references fail cross-reference."""
        validator = PlayerValidator(valid_players_file, context)
        validator.validate()
        result = validator.validate_cross_references()

        assert len(result.errors) == 2

    def test_validate_cross_references_file_not_found(
        self, context_with_sprites: ValidationContext, tmp_path: Path
    ) -> None:
        """Missing file during cross-reference returns empty result."""
        validator = PlayerValidator(tmp_path / "nonexistent.json", context_with_sprites)
        result = validator.validate_cross_references()

        assert result.errors == []

    def test_validate_cross_references_invalid_json(
        self, context_with_sprites: ValidationContext, tmp_path: Path
    ) -> None:
        """Invalid JSON during cross-reference returns empty result."""
        players_file = tmp_path / "players.json"
        players_file.write_text("not valid json{")
        validator = PlayerValidator(players_file, context_with_sprites)
        result = validator.validate_cross_references()

        assert result.errors == []

    def test_validate_cross_references_root_not_dict(
        self, context_with_sprites: ValidationContext, tmp_path: Path
    ) -> None:
        """Non-dict root during cross-reference returns empty result."""
        players_file = tmp_path / "players.json"
        players_file.write_text(json.dumps([{"sprite_id": "hero"}]))
        validator = PlayerValidator(players_file, context_with_sprites)
        result = validator.validate_cross_references()

        assert result.errors == []

    def test_validate_cross_references_skips_player_not_in_file(
        self, context_with_sprites: ValidationContext, tmp_path: Path
    ) -> None:
        """Player registered in context but absent from file is skipped gracefully."""
        players_file = tmp_path / "players.json"
        players_file.write_text(json.dumps({"other_player": {"sprite_id": "hero"}}))
        context_with_sprites.add_player_id("ghost_player")  # registered but not in file
        validator = PlayerValidator(players_file, context_with_sprites)
        result = validator.validate_cross_references()

        assert result.errors == []
