"""Tests for NPCValidator."""

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from pedre.validators.context import ValidationContext
from pedre.validators.npc_validator import NPCValidator

if TYPE_CHECKING:
    from pathlib import Path


class TestNPCValidator:
    """Test NPCValidator."""

    @pytest.fixture
    def context(self) -> ValidationContext:
        """Create a fresh ValidationContext for each test."""
        return ValidationContext()

    @pytest.fixture
    def context_with_sprites(self) -> ValidationContext:
        """Create a ValidationContext pre-populated with sprite IDs."""
        ctx = ValidationContext()
        ctx.add_sprite_id("villager")
        ctx.add_sprite_id("guard")
        return ctx

    @pytest.fixture
    def valid_npcs_file(self, tmp_path: Path) -> Path:
        """Create a valid npcs.json file."""
        data = {
            "bob": {"sprite_id": "villager"},
            "alice": {"sprite_id": "guard"},
        }
        npcs_file = tmp_path / "npcs.json"
        npcs_file.write_text(json.dumps(data))
        return npcs_file

    def test_name_property(self, context: ValidationContext, valid_npcs_file: Path) -> None:
        """Validator name is 'NPCs'."""
        validator = NPCValidator(valid_npcs_file, context)
        assert validator.name == "NPCs"

    def test_validate_valid_file_registers_npcs(self, context: ValidationContext, valid_npcs_file: Path) -> None:
        """Valid NPCs are registered in context after validation."""
        validator = NPCValidator(valid_npcs_file, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 2
        assert "bob" in context.get_npc_ids()
        assert "alice" in context.get_npc_ids()

    def test_validate_file_not_found(self, context: ValidationContext, tmp_path: Path) -> None:
        """Missing file produces a 'not found' error."""
        validator = NPCValidator(tmp_path / "nonexistent.json", context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "not found" in result.errors[0]
        assert result.item_count == 0

    def test_validate_invalid_json(self, context: ValidationContext, tmp_path: Path) -> None:
        """Malformed JSON produces a 'Failed to parse' error."""
        npcs_file = tmp_path / "npcs.json"
        npcs_file.write_text("not valid json{")
        validator = NPCValidator(npcs_file, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Failed to parse" in result.errors[0]

    def test_validate_root_not_dict(self, context: ValidationContext, tmp_path: Path) -> None:
        """Root JSON value that is not a dict produces a 'root must be a dictionary' error."""
        npcs_file = tmp_path / "npcs.json"
        npcs_file.write_text(json.dumps([{"sprite_id": "villager"}]))
        validator = NPCValidator(npcs_file, context)
        result = validator.validate()

        assert any("root must be a dictionary" in e for e in result.errors)

    def test_validate_npc_not_dict(self, context: ValidationContext, tmp_path: Path) -> None:
        """NPC value that is not a dict produces an error; valid NPCs are still registered."""
        data = {
            "bad_npc": "not_a_dict",
            "valid_npc": {"sprite_id": "villager"},
        }
        npcs_file = tmp_path / "npcs.json"
        npcs_file.write_text(json.dumps(data))
        validator = NPCValidator(npcs_file, context)
        result = validator.validate()

        assert any("must be a dictionary" in e for e in result.errors)
        assert result.item_count == 1
        assert "valid_npc" in context.get_npc_ids()

    def test_validate_npc_missing_sprite_id(self, context: ValidationContext, tmp_path: Path) -> None:
        """NPC missing sprite_id produces an error and is not registered."""
        npcs_file = tmp_path / "npcs.json"
        npcs_file.write_text(json.dumps({"npc_01": {}}))
        validator = NPCValidator(npcs_file, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert result.item_count == 0
        assert "npc_01" not in context.get_npc_ids()

    def test_validate_empty_file_is_valid(self, context: ValidationContext, tmp_path: Path) -> None:
        """An empty NPCs dict is valid and registers no NPCs."""
        npcs_file = tmp_path / "npcs.json"
        npcs_file.write_text(json.dumps({}))
        validator = NPCValidator(npcs_file, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 0
        assert context.get_npc_ids() == set()

    def test_validate_os_error(self, context: ValidationContext, tmp_path: Path) -> None:
        """OSError while reading the file produces a 'Failed to load' error."""
        npcs_file = tmp_path / "npcs.json"
        npcs_file.write_text(json.dumps({}))
        validator = NPCValidator(npcs_file, context)

        with patch("pathlib.Path.open", side_effect=PermissionError("Permission denied")):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "Failed to load" in result.errors[0]
        assert result.item_count == 0

    def test_validate_cross_references_valid(
        self, context_with_sprites: ValidationContext, valid_npcs_file: Path
    ) -> None:
        """NPCs referencing valid sprites pass cross-reference validation."""
        validator = NPCValidator(valid_npcs_file, context_with_sprites)
        validator.validate()
        result = validator.validate_cross_references()

        assert result.errors == []

    def test_validate_cross_references_unknown_sprite(self, context: ValidationContext, tmp_path: Path) -> None:
        """NPC referencing an unknown sprite produces a cross-reference error."""
        npcs_file = tmp_path / "npcs.json"
        npcs_file.write_text(json.dumps({"npc_01": {"sprite_id": "ghost"}}))
        validator = NPCValidator(npcs_file, context)
        validator.validate()
        result = validator.validate_cross_references()

        assert len(result.errors) == 1
        assert "npc_01" in result.errors[0]
        assert "ghost" in result.errors[0]

    def test_validate_cross_references_no_sprites_in_context(
        self, context: ValidationContext, valid_npcs_file: Path
    ) -> None:
        """When no sprites are in context, all sprite references fail cross-reference."""
        validator = NPCValidator(valid_npcs_file, context)
        validator.validate()
        result = validator.validate_cross_references()

        assert len(result.errors) == 2

    def test_validate_cross_references_file_not_found(
        self, context_with_sprites: ValidationContext, tmp_path: Path
    ) -> None:
        """Missing file during cross-reference returns empty result."""
        validator = NPCValidator(tmp_path / "nonexistent.json", context_with_sprites)
        result = validator.validate_cross_references()

        assert result.errors == []

    def test_validate_cross_references_invalid_json(
        self, context_with_sprites: ValidationContext, tmp_path: Path
    ) -> None:
        """Invalid JSON during cross-reference reports a parse error."""
        npcs_file = tmp_path / "npcs.json"
        npcs_file.write_text("not valid json{")
        validator = NPCValidator(npcs_file, context_with_sprites)
        result = validator.validate_cross_references()

        assert len(result.errors) == 1
        assert "Failed to parse" in result.errors[0]

    def test_validate_cross_references_os_error(self, context_with_sprites: ValidationContext, tmp_path: Path) -> None:
        """OSError during cross-reference reports a load error."""
        npcs_file = tmp_path / "npcs.json"
        npcs_file.write_text("{}")
        validator = NPCValidator(npcs_file, context_with_sprites)

        with patch("pathlib.Path.open", side_effect=PermissionError("Permission denied")):
            result = validator.validate_cross_references()

        assert len(result.errors) == 1
        assert "Failed to load" in result.errors[0]

    def test_validate_cross_references_root_not_dict(
        self, context_with_sprites: ValidationContext, tmp_path: Path
    ) -> None:
        """Non-dict root during cross-reference returns empty result."""
        npcs_file = tmp_path / "npcs.json"
        npcs_file.write_text(json.dumps([{"sprite_id": "villager"}]))
        validator = NPCValidator(npcs_file, context_with_sprites)
        result = validator.validate_cross_references()

        assert result.errors == []

    def test_validate_cross_references_skips_npc_not_in_file(
        self, context_with_sprites: ValidationContext, tmp_path: Path
    ) -> None:
        """NPC registered in context but absent from file is skipped gracefully."""
        npcs_file = tmp_path / "npcs.json"
        npcs_file.write_text(json.dumps({"other_npc": {"sprite_id": "villager"}}))
        context_with_sprites.add_npc_id("ghost_npc")  # registered but not in file
        validator = NPCValidator(npcs_file, context_with_sprites)
        result = validator.validate_cross_references()

        assert result.errors == []
