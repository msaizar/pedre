"""Tests for ItemsValidator."""

import json
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from pedre.validators.context import ValidationContext
from pedre.validators.items_validator import ItemsValidator

if TYPE_CHECKING:
    from pathlib import Path


class TestItemsValidator:
    """Test ItemsValidator."""

    @pytest.fixture
    def context(self) -> ValidationContext:
        """Create a fresh ValidationContext for each test."""
        return ValidationContext()

    @pytest.fixture
    def valid_items_file(self, tmp_path: Path) -> Path:
        """Create a valid items.json file in content registry dict format."""
        data = {
            "rusty_key": {"name": "Rusty Key", "description": "Opens the old lock."},
            "health_potion": {"name": "Health Potion", "description": "Restores health."},
        }
        items_file = tmp_path / "items.json"
        items_file.write_text(json.dumps(data))
        return items_file

    def test_name_property(self, context: ValidationContext, valid_items_file: Path) -> None:
        """Validator name is 'Inventory Items'."""
        validator = ItemsValidator(valid_items_file, context)
        assert validator.name == "Inventory Items"

    def test_validate_valid_file_registers_items(self, context: ValidationContext, valid_items_file: Path) -> None:
        """Valid items are registered in context after validation."""
        validator = ItemsValidator(valid_items_file, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 2
        assert "rusty_key" in context.get_inventory_items()
        assert "health_potion" in context.get_inventory_items()

    def test_validate_file_not_found(self, context: ValidationContext, tmp_path: Path) -> None:
        """Missing file produces a 'not found' error."""
        validator = ItemsValidator(tmp_path / "nonexistent.json", context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "not found" in result.errors[0]
        assert result.item_count == 0

    def test_validate_invalid_json(self, context: ValidationContext, tmp_path: Path) -> None:
        """Malformed JSON produces a 'Failed to parse' error."""
        items_file = tmp_path / "items.json"
        items_file.write_text("not valid json{")
        validator = ItemsValidator(items_file, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Failed to parse" in result.errors[0]

    def test_validate_root_not_dict(self, context: ValidationContext, tmp_path: Path) -> None:
        """Root JSON value that is not a dict produces a 'root must be a dictionary' error."""
        items_file = tmp_path / "items.json"
        items_file.write_text(json.dumps([{"name": "Key", "description": "A key."}]))
        validator = ItemsValidator(items_file, context)
        result = validator.validate()

        assert any("root must be a dictionary" in e for e in result.errors)

    def test_validate_item_missing_name(self, context: ValidationContext, tmp_path: Path) -> None:
        """Item missing 'name' field produces an error and is not registered."""
        items_file = tmp_path / "items.json"
        items_file.write_text(json.dumps({"key_01": {"description": "A key."}}))
        validator = ItemsValidator(items_file, context)
        result = validator.validate()

        assert any("missing required 'name' field" in e for e in result.errors)
        assert result.item_count == 0

    def test_validate_item_missing_description(self, context: ValidationContext, tmp_path: Path) -> None:
        """Item missing 'description' field produces an error and is not registered."""
        items_file = tmp_path / "items.json"
        items_file.write_text(json.dumps({"key_01": {"name": "Key"}}))
        validator = ItemsValidator(items_file, context)
        result = validator.validate()

        assert any("missing required 'description' field" in e for e in result.errors)
        assert result.item_count == 0

    def test_validate_empty_file_is_valid(self, context: ValidationContext, tmp_path: Path) -> None:
        """An empty items dict is valid and registers no items."""
        items_file = tmp_path / "items.json"
        items_file.write_text(json.dumps({}))
        validator = ItemsValidator(items_file, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 0
        assert context.get_inventory_items() == set()

    def test_validate_partial_errors_still_registers_valid_items(
        self, context: ValidationContext, tmp_path: Path
    ) -> None:
        """Valid items are registered even when other items in the file have errors."""
        data = {
            "valid_item": {"name": "Valid Item", "description": "All good."},
            "missing_desc": {"name": "No Description"},
            "another_valid": {"name": "Another Valid", "description": "Also good."},
        }
        items_file = tmp_path / "items.json"
        items_file.write_text(json.dumps(data))
        validator = ItemsValidator(items_file, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert result.item_count == 2
        assert "valid_item" in context.get_inventory_items()
        assert "another_valid" in context.get_inventory_items()

    def test_validate_cross_references_returns_empty(self, context: ValidationContext, valid_items_file: Path) -> None:
        """validate_cross_references returns an empty result (items are the authority)."""
        validator = ItemsValidator(valid_items_file, context)
        validator.validate()
        result = validator.validate_cross_references()

        assert result.errors == []
        assert result.item_count == 0

    def test_validate_os_error(self, context: ValidationContext, tmp_path: Path) -> None:
        """OSError while reading the file produces a 'Failed to load' error."""
        items_file = tmp_path / "items.json"
        items_file.write_text(json.dumps({}))
        validator = ItemsValidator(items_file, context)

        with patch("pathlib.Path.open", side_effect=PermissionError("Permission denied")):
            result = validator.validate()

        assert len(result.errors) == 1
        assert "Failed to load" in result.errors[0]
        assert result.item_count == 0

    def test_validate_item_not_dict(self, context: ValidationContext, tmp_path: Path) -> None:
        """Item value that is not a dict produces an error; other valid items are still registered."""
        data = {
            "bad_item": "not_a_dict",
            "valid_item": {"name": "Valid", "description": "Good."},
        }
        items_file = tmp_path / "items.json"
        items_file.write_text(json.dumps(data))
        validator = ItemsValidator(items_file, context)
        result = validator.validate()

        assert any("must be a dictionary" in e for e in result.errors)
        assert result.item_count == 1
        assert "valid_item" in context.get_inventory_items()
