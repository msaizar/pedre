"""Tests for interaction conditions."""

import unittest
from unittest.mock import MagicMock

from pedre.plugins.interaction.conditions import ObjectInteractedCondition


class TestObjectInteractedCondition(unittest.TestCase):
    """Test cases for ObjectInteractedCondition."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_context = MagicMock()
        self.mock_interaction_plugin = MagicMock()
        self.mock_context.interaction_plugin = self.mock_interaction_plugin

    def test_check_returns_true(self) -> None:
        """Test that check returns True when object was interacted with."""
        self.mock_interaction_plugin.has_interacted_with.return_value = True

        condition = ObjectInteractedCondition(object_name="test_object")
        result = condition.check(self.mock_context)

        assert result is True
        self.mock_interaction_plugin.has_interacted_with.assert_called_once_with("test_object")

    def test_check_returns_false(self) -> None:
        """Test that check returns False when object was not interacted with."""
        self.mock_interaction_plugin.has_interacted_with.return_value = False

        condition = ObjectInteractedCondition(object_name="test_object")
        result = condition.check(self.mock_context)

        assert result is False
        self.mock_interaction_plugin.has_interacted_with.assert_called_once_with("test_object")

    def test_check_with_equals_true(self) -> None:
        """Test check with explicit equals=True."""
        self.mock_interaction_plugin.has_interacted_with.return_value = True

        condition = ObjectInteractedCondition(object_name="test_object", expected=True)
        result = condition.check(self.mock_context)

        assert result is True

    def test_check_with_equals_false(self) -> None:
        """Test check with equals=False (negative check)."""
        self.mock_interaction_plugin.has_interacted_with.return_value = False

        condition = ObjectInteractedCondition(object_name="test_object", expected=False)
        result = condition.check(self.mock_context)

        assert result is True  # Object was NOT interacted with, which matches equals=False

    def test_check_equals_false_when_interacted(self) -> None:
        """Test equals=False returns False when object was actually interacted with."""
        self.mock_interaction_plugin.has_interacted_with.return_value = True

        condition = ObjectInteractedCondition(object_name="test_object", expected=False)
        result = condition.check(self.mock_context)

        assert result is False  # Object WAS interacted with, which doesn't match equals=False

    def test_check_missing_object_name(self) -> None:
        """Test that missing object name returns False."""
        condition = ObjectInteractedCondition(object_name="")
        result = condition.check(self.mock_context)

        assert result is False
        self.mock_interaction_plugin.has_interacted_with.assert_not_called()

    def test_validate_success(self) -> None:
        """Test validator passes with valid data."""
        data = {"object": "test_object"}
        errors = ObjectInteractedCondition.validate_params(data)
        assert errors == []

    def test_validate_missing_object(self) -> None:
        """Test validator detects missing object field."""
        data = {}
        errors = ObjectInteractedCondition.validate_params(data)
        assert len(errors) == 1
        assert "missing required 'object' field" in errors[0]

    def test_validate_empty_object(self) -> None:
        """Test validator detects empty object field."""
        data = {"object": ""}
        errors = ObjectInteractedCondition.validate_params(data)
        assert len(errors) == 1
        assert "missing required 'object' field" in errors[0]

    def test_validate_object_not_string(self) -> None:
        """Test validator detects non-string object field."""
        data = {"object": 123}
        errors = ObjectInteractedCondition.validate_params(data)
        assert len(errors) == 1
        assert "'object' must be a string" in errors[0]

    def test_validate_equals_not_bool(self) -> None:
        """Test validator detects non-bool equals field."""
        data = {"object": "test_object", "equals": "yes"}
        errors = ObjectInteractedCondition.validate_params(data)
        assert len(errors) == 1
        assert "'equals' must be a bool" in errors[0]


if __name__ == "__main__":
    unittest.main()
