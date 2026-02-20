"""Tests for inventory conditions."""

import unittest
from unittest.mock import MagicMock

import pytest

from pedre.conditions.registry import ConditionParseError
from pedre.plugins.inventory.conditions import (
    InventoryAccessedCondition,
    ItemAcquiredCondition,
)
from pedre.types import EntityReference


class TestInventoryAccessedCondition(unittest.TestCase):
    """Test cases for InventoryAccessedCondition."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_context = MagicMock()
        self.mock_inventory_plugin = MagicMock()
        self.mock_context.inventory_plugin = self.mock_inventory_plugin

    def test_check_returns_true(self) -> None:
        """Test that check returns True when inventory has been accessed."""
        self.mock_inventory_plugin.has_been_accessed.return_value = True

        condition = InventoryAccessedCondition()
        result = condition.check(self.mock_context)

        assert result is True
        self.mock_inventory_plugin.has_been_accessed.assert_called_once()

    def test_check_returns_false(self) -> None:
        """Test that check returns False when inventory has not been accessed."""
        self.mock_inventory_plugin.has_been_accessed.return_value = False

        condition = InventoryAccessedCondition()
        result = condition.check(self.mock_context)

        assert result is False
        self.mock_inventory_plugin.has_been_accessed.assert_called_once()

    def test_validate_success(self) -> None:
        """Test validator always passes (no params)."""
        data = {"random_key": "val"}
        InventoryAccessedCondition.from_dict(data)


class TestItemAcquiredCondition(unittest.TestCase):
    """Test cases for ItemAcquiredCondition."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_context = MagicMock()
        self.mock_inventory_plugin = MagicMock()
        self.mock_context.inventory_plugin = self.mock_inventory_plugin

    def test_check_returns_true(self) -> None:
        """Test that check returns True when item is in inventory."""
        self.mock_inventory_plugin.has_item.return_value = True

        condition = ItemAcquiredCondition(item_id="test_item")
        result = condition.check(self.mock_context)

        assert result is True
        self.mock_inventory_plugin.has_item.assert_called_once_with("test_item")

    def test_check_returns_false(self) -> None:
        """Test that check returns False when item is not in inventory."""
        self.mock_inventory_plugin.has_item.return_value = False

        condition = ItemAcquiredCondition(item_id="test_item")
        result = condition.check(self.mock_context)

        assert result is False
        self.mock_inventory_plugin.has_item.assert_called_once_with("test_item")

    def test_check_missing_item_id(self) -> None:
        """Test that missing item_id returns False."""
        condition = ItemAcquiredCondition(item_id="")
        result = condition.check(self.mock_context)

        assert result is False
        self.mock_inventory_plugin.has_item.assert_not_called()

    def test_validate_success(self) -> None:
        """Test validator passes with valid data."""
        data = {"item_id": "test_item"}
        ItemAcquiredCondition.from_dict(data)

    def test_validate_missing_item_id(self) -> None:
        """Test validator detects missing item_id field."""
        data = {}
        with pytest.raises(ConditionParseError):
            ItemAcquiredCondition.from_dict(data)

    def test_validate_empty_item_id(self) -> None:
        """Test validator detects empty item_id field."""
        data = {"item_id": ""}
        with pytest.raises(ConditionParseError):
            ItemAcquiredCondition.from_dict(data)

    def test_validate_item_id_not_string(self) -> None:
        """Test validator detects non-string item_id field."""
        data = {"item_id": 123}
        with pytest.raises(ConditionParseError):
            ItemAcquiredCondition.from_dict(data)


class TestGetReferences:
    """Test get_references() on inventory conditions."""

    def test_item_acquired_condition_returns_inventory_item_reference(self) -> None:
        """Test that ItemAcquiredCondition.get_references returns an inventory_item reference."""
        condition = ItemAcquiredCondition(item_id="test_item")
        refs = condition.get_references()
        assert refs == {EntityReference(type="inventory_item", name="test_item")}

    def test_inventory_accessed_condition_returns_empty_set(self) -> None:
        """Test that InventoryAccessedCondition.get_references returns empty set."""
        condition = InventoryAccessedCondition()
        refs = condition.get_references()
        assert refs == set()
