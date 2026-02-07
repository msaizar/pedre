"""Tests for interaction conditions."""

import unittest
from unittest.mock import MagicMock

from pedre.plugins.interaction.conditions import check_object_interacted


class TestCheckObjectInteracted(unittest.TestCase):
    """Test cases for check_object_interacted condition."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_context = MagicMock()
        self.mock_interaction_plugin = MagicMock()
        self.mock_context.interaction_plugin = self.mock_interaction_plugin

    def test_check_object_interacted_returns_true(self) -> None:
        """Test that check_object_interacted returns True when object was interacted with."""
        self.mock_interaction_plugin.has_interacted_with.return_value = True

        condition_data = {"object": "test_object"}
        result = check_object_interacted(condition_data, self.mock_context)

        assert result is True
        self.mock_interaction_plugin.has_interacted_with.assert_called_once_with("test_object")

    def test_check_object_interacted_returns_false(self) -> None:
        """Test that check_object_interacted returns False when object was not interacted with."""
        self.mock_interaction_plugin.has_interacted_with.return_value = False

        condition_data = {"object": "test_object"}
        result = check_object_interacted(condition_data, self.mock_context)

        assert result is False
        self.mock_interaction_plugin.has_interacted_with.assert_called_once_with("test_object")

    def test_check_object_interacted_with_equals_true(self) -> None:
        """Test check_object_interacted with explicit equals=True."""
        self.mock_interaction_plugin.has_interacted_with.return_value = True

        condition_data = {"object": "test_object", "equals": True}
        result = check_object_interacted(condition_data, self.mock_context)

        assert result is True

    def test_check_object_interacted_with_equals_false(self) -> None:
        """Test check_object_interacted with equals=False (negative check)."""
        self.mock_interaction_plugin.has_interacted_with.return_value = False

        condition_data = {"object": "test_object", "equals": False}
        result = check_object_interacted(condition_data, self.mock_context)

        assert result is True  # Object was NOT interacted with, which matches equals=False

    def test_check_object_interacted_equals_false_when_interacted(self) -> None:
        """Test equals=False returns False when object was actually interacted with."""
        self.mock_interaction_plugin.has_interacted_with.return_value = True

        condition_data = {"object": "test_object", "equals": False}
        result = check_object_interacted(condition_data, self.mock_context)

        assert result is False  # Object WAS interacted with, which doesn't match equals=False

    def test_check_object_interacted_missing_object_name(self) -> None:
        """Test that missing object name returns False."""
        condition_data = {}
        result = check_object_interacted(condition_data, self.mock_context)

        assert result is False
        self.mock_interaction_plugin.has_interacted_with.assert_not_called()

    def test_check_object_interacted_empty_object_name(self) -> None:
        """Test that empty object name returns False."""
        condition_data = {"object": ""}
        result = check_object_interacted(condition_data, self.mock_context)

        assert result is False
        self.mock_interaction_plugin.has_interacted_with.assert_not_called()

    def test_check_object_interacted_none_object_name(self) -> None:
        """Test that None object name returns False."""
        condition_data = {"object": None}
        result = check_object_interacted(condition_data, self.mock_context)

        assert result is False
        self.mock_interaction_plugin.has_interacted_with.assert_not_called()


if __name__ == "__main__":
    unittest.main()
