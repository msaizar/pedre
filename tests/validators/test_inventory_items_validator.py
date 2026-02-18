"""Tests for InventoryItemsValidator."""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
import pytest

from pedre.validators.context import ValidationContext
from pedre.validators.inventory_items_validator import InventoryItemsValidator


class TestInventoryItemsValidator:
    """Test InventoryItemsValidator."""

    @pytest.fixture
    def context(self) -> ValidationContext:
        """Create a fresh ValidationContext for each test."""
        return ValidationContext()

    @pytest.fixture
    def valid_items_file(self, tmp_path: Path) -> Path:
        """Create a valid inventory_items.json file."""
        data = {
            "items": [
                {"id": "rusty_key", "name": "Rusty Key"},
                {"id": "health_potion", "name": "Health Potion"},
            ]
        }
        items_file = tmp_path / "inventory_items.json"
        items_file.write_text(json.dumps(data))
        return items_file

    def test_name_property(self, context: ValidationContext, valid_items_file: Path) -> None:
        """Test validator name."""
        validator = InventoryItemsValidator(valid_items_file, context)
        assert validator.name == "Inventory Items"

    def test_validate_valid_file_registers_items(self, context: ValidationContext, valid_items_file: Path) -> None:
        """Test that valid items are registered in context."""
        validator = InventoryItemsValidator(valid_items_file, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 2
        assert "rusty_key" in context.get_inventory_items()
        assert "health_potion" in context.get_inventory_items()

    def test_validate_file_not_found(self, context: ValidationContext, tmp_path: Path) -> None:
        """Test error when file does not exist."""
        validator = InventoryItemsValidator(tmp_path / "nonexistent.json", context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "not found" in result.errors[0]
        assert result.item_count == 0

    def test_validate_invalid_json(self, context: ValidationContext, tmp_path: Path) -> None:
        """Test error on invalid JSON."""
        items_file = tmp_path / "inventory_items.json"
        items_file.write_text("not valid json{")
        validator = InventoryItemsValidator(items_file, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert "Failed to parse" in result.errors[0]

    def test_validate_root_not_dict(self, context: ValidationContext, tmp_path: Path) -> None:
        """Test error when root is not a dictionary."""
        items_file = tmp_path / "inventory_items.json"
        items_file.write_text(json.dumps([{"id": "key"}]))
        validator = InventoryItemsValidator(items_file, context)
        result = validator.validate()

        assert any("root must be a dictionary" in e for e in result.errors)

    def test_validate_missing_items_key(self, context: ValidationContext, tmp_path: Path) -> None:
        """Test error when 'items' key is missing."""
        items_file = tmp_path / "inventory_items.json"
        items_file.write_text(json.dumps({"other_key": []}))
        validator = InventoryItemsValidator(items_file, context)
        result = validator.validate()

        assert any("missing required 'items' key" in e for e in result.errors)

    def test_validate_items_not_list(self, context: ValidationContext, tmp_path: Path) -> None:
        """Test error when 'items' is not a list."""
        items_file = tmp_path / "inventory_items.json"
        items_file.write_text(json.dumps({"items": "not a list"}))
        validator = InventoryItemsValidator(items_file, context)
        result = validator.validate()

        assert any("'items' must be a list" in e for e in result.errors)

    def test_validate_item_missing_id(self, context: ValidationContext, tmp_path: Path) -> None:
        """Test error when item is missing 'id' field."""
        data = {"items": [{"name": "Key"}]}
        items_file = tmp_path / "inventory_items.json"
        items_file.write_text(json.dumps(data))
        validator = InventoryItemsValidator(items_file, context)
        result = validator.validate()

        assert any("missing required 'id' field" in e for e in result.errors)
        assert result.item_count == 0

    def test_validate_item_missing_name(self, context: ValidationContext, tmp_path: Path) -> None:
        """Test error when item is missing 'name' field."""
        data = {"items": [{"id": "key"}]}
        items_file = tmp_path / "inventory_items.json"
        items_file.write_text(json.dumps(data))
        validator = InventoryItemsValidator(items_file, context)
        result = validator.validate()

        assert any("missing required 'name' field" in e for e in result.errors)

    def test_validate_empty_items_list(self, context: ValidationContext, tmp_path: Path) -> None:
        """Test validation with empty items list is valid."""
        items_file = tmp_path / "inventory_items.json"
        items_file.write_text(json.dumps({"items": []}))
        validator = InventoryItemsValidator(items_file, context)
        result = validator.validate()

        assert result.errors == []
        assert result.item_count == 0
        assert context.get_inventory_items() == set()

    def test_validate_partial_errors_still_registers_valid_items(
        self, context: ValidationContext, tmp_path: Path
    ) -> None:
        """Test that valid items are still registered even when some items have errors."""
        data = {
            "items": [
                {"id": "valid_item", "name": "Valid Item"},
                {"name": "Missing ID"},
                {"id": "another_valid", "name": "Another Valid"},
            ]
        }
        items_file = tmp_path / "inventory_items.json"
        items_file.write_text(json.dumps(data))
        validator = InventoryItemsValidator(items_file, context)
        result = validator.validate()

        assert len(result.errors) == 1
        assert result.item_count == 2
        assert "valid_item" in context.get_inventory_items()
        assert "another_valid" in context.get_inventory_items()

    def test_validate_cross_references_returns_empty(self, context: ValidationContext, valid_items_file: Path) -> None:
        """Test that validate_cross_references returns empty result (items are the authority)."""
        validator = InventoryItemsValidator(valid_items_file, context)
        validator.validate()
        result = validator.validate_cross_references()

        assert result.errors == []
        assert result.item_count == 0
