"""Tests for inventory conditions."""

import unittest
from unittest.mock import MagicMock

from pedre.plugins.inventory.conditions import (
    _validate_item_acquired,
    check_inventory_accessed,
    check_item_acquired,
)


class TestCheckInventoryAccessed(unittest.TestCase):
    """Test cases for check_inventory_accessed condition."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_context = MagicMock()
        self.mock_inventory_plugin = MagicMock()
        self.mock_context.inventory_plugin = self.mock_inventory_plugin

    def test_check_inventory_accessed_returns_true(self) -> None:
        """Test that check_inventory_accessed returns True when inventory has been accessed."""
        self.mock_inventory_plugin.has_been_accessed.return_value = True

        condition_data = {}
        result = check_inventory_accessed(condition_data, self.mock_context)

        assert result is True
        self.mock_inventory_plugin.has_been_accessed.assert_called_once()

    def test_check_inventory_accessed_returns_false(self) -> None:
        """Test that check_inventory_accessed returns False when inventory has not been accessed."""
        self.mock_inventory_plugin.has_been_accessed.return_value = False

        condition_data = {}
        result = check_inventory_accessed(condition_data, self.mock_context)

        assert result is False
        self.mock_inventory_plugin.has_been_accessed.assert_called_once()

    def test_check_inventory_accessed_ignores_condition_data(self) -> None:
        """Test that condition_data content is ignored (only context matters)."""
        self.mock_inventory_plugin.has_been_accessed.return_value = True

        # Pass various condition data - should all be ignored
        condition_data = {"random_key": "random_value", "another": 123}
        result = check_inventory_accessed(condition_data, self.mock_context)

        assert result is True
        self.mock_inventory_plugin.has_been_accessed.assert_called_once()


class TestValidateItemAcquired(unittest.TestCase):
    """Test cases for _validate_item_acquired validator."""

    def test_validate_item_acquired_success(self) -> None:
        """Test validator passes with valid data."""
        data = {"item_id": "test_item"}
        errors = _validate_item_acquired(data)
        assert errors == []

    def test_validate_item_acquired_missing_item_id(self) -> None:
        """Test validator detects missing item_id field."""
        data = {}
        errors = _validate_item_acquired(data)
        assert len(errors) == 1
        assert "missing required 'item_id' field" in errors[0]

    def test_validate_item_acquired_empty_item_id(self) -> None:
        """Test validator detects empty item_id field."""
        data = {"item_id": ""}
        errors = _validate_item_acquired(data)
        assert len(errors) == 1
        assert "missing required 'item_id' field" in errors[0]


class TestCheckItemAcquired(unittest.TestCase):
    """Test cases for check_item_acquired condition."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_context = MagicMock()
        self.mock_inventory_plugin = MagicMock()
        self.mock_context.inventory_plugin = self.mock_inventory_plugin

    def test_check_item_acquired_returns_true(self) -> None:
        """Test that check_item_acquired returns True when item is in inventory."""
        self.mock_inventory_plugin.has_item.return_value = True

        condition_data = {"item_id": "test_item"}
        result = check_item_acquired(condition_data, self.mock_context)

        assert result is True
        self.mock_inventory_plugin.has_item.assert_called_once_with("test_item")

    def test_check_item_acquired_returns_false(self) -> None:
        """Test that check_item_acquired returns False when item is not in inventory."""
        self.mock_inventory_plugin.has_item.return_value = False

        condition_data = {"item_id": "test_item"}
        result = check_item_acquired(condition_data, self.mock_context)

        assert result is False
        self.mock_inventory_plugin.has_item.assert_called_once_with("test_item")

    def test_check_item_acquired_missing_item_id(self) -> None:
        """Test that missing item_id returns False."""
        condition_data = {}
        result = check_item_acquired(condition_data, self.mock_context)

        assert result is False
        self.mock_inventory_plugin.has_item.assert_not_called()

    def test_check_item_acquired_empty_item_id(self) -> None:
        """Test that empty item_id returns False."""
        condition_data = {"item_id": ""}
        result = check_item_acquired(condition_data, self.mock_context)

        assert result is False
        self.mock_inventory_plugin.has_item.assert_not_called()

    def test_check_item_acquired_none_item_id(self) -> None:
        """Test that None item_id returns False."""
        condition_data = {"item_id": None}
        result = check_item_acquired(condition_data, self.mock_context)

        assert result is False
        self.mock_inventory_plugin.has_item.assert_not_called()

    def test_check_item_acquired_with_different_items(self) -> None:
        """Test checking for different item IDs."""

        # Setup mock to return different values based on item_id
        def has_item_side_effect(item_id: str) -> bool:
            return item_id == "found_item"

        self.mock_inventory_plugin.has_item.side_effect = has_item_side_effect

        # Test with item that exists
        condition_data = {"item_id": "found_item"}
        result = check_item_acquired(condition_data, self.mock_context)
        assert result is True

        # Test with item that doesn't exist
        condition_data = {"item_id": "missing_item"}
        result = check_item_acquired(condition_data, self.mock_context)
        assert result is False


if __name__ == "__main__":
    unittest.main()
