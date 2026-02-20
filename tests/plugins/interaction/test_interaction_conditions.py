"""Tests for interaction conditions."""

from unittest.mock import MagicMock

import pytest

from pedre.conditions.registry import ConditionParseError
from pedre.plugins.interaction.conditions import ObjectInteractedCondition


class TestObjectInteractedCondition:
    """Test cases for ObjectInteractedCondition."""

    @pytest.fixture
    def mock_context(self) -> MagicMock:
        """Fixture for mock context with interaction plugin."""
        ctx = MagicMock()
        ctx.interaction_plugin = MagicMock()
        return ctx

    def test_check_returns_true(self, mock_context: MagicMock) -> None:
        """Test that check returns True when object was interacted with."""
        mock_context.interaction_plugin.has_interacted_with.return_value = True

        condition = ObjectInteractedCondition(object_name="test_object")
        result = condition.check(mock_context)

        assert result is True
        mock_context.interaction_plugin.has_interacted_with.assert_called_once_with("test_object")

    def test_check_returns_false(self, mock_context: MagicMock) -> None:
        """Test that check returns False when object was not interacted with."""
        mock_context.interaction_plugin.has_interacted_with.return_value = False

        condition = ObjectInteractedCondition(object_name="test_object")
        result = condition.check(mock_context)

        assert result is False
        mock_context.interaction_plugin.has_interacted_with.assert_called_once_with("test_object")

    def test_check_with_equals_true(self, mock_context: MagicMock) -> None:
        """Test check with explicit equals=True."""
        mock_context.interaction_plugin.has_interacted_with.return_value = True

        condition = ObjectInteractedCondition(object_name="test_object", expected=True)
        result = condition.check(mock_context)

        assert result is True

    def test_check_with_equals_false(self, mock_context: MagicMock) -> None:
        """Test check with equals=False (negative check)."""
        mock_context.interaction_plugin.has_interacted_with.return_value = False

        condition = ObjectInteractedCondition(object_name="test_object", expected=False)
        result = condition.check(mock_context)

        assert result is True  # Object was NOT interacted with, which matches equals=False

    def test_check_equals_false_when_interacted(self, mock_context: MagicMock) -> None:
        """Test equals=False returns False when object was actually interacted with."""
        mock_context.interaction_plugin.has_interacted_with.return_value = True

        condition = ObjectInteractedCondition(object_name="test_object", expected=False)
        result = condition.check(mock_context)

        assert result is False  # Object WAS interacted with, which doesn't match equals=False

    def test_check_missing_object_name(self, mock_context: MagicMock) -> None:
        """Test that missing object name returns False."""
        condition = ObjectInteractedCondition(object_name="")
        result = condition.check(mock_context)

        assert result is False
        mock_context.interaction_plugin.has_interacted_with.assert_not_called()

    def test_validate_success(self) -> None:
        """Test validator passes with valid data."""
        data = {"object": "test_object"}
        ObjectInteractedCondition.from_dict(data)

    def test_validate_missing_object(self) -> None:
        """Test validator detects missing object field."""
        data = {}
        with pytest.raises(ConditionParseError):
            ObjectInteractedCondition.from_dict(data)

    def test_validate_empty_object(self) -> None:
        """Test validator detects empty object field."""
        data = {"object": ""}
        with pytest.raises(ConditionParseError):
            ObjectInteractedCondition.from_dict(data)

    def test_validate_object_not_string(self) -> None:
        """Test validator detects non-string object field."""
        data = {"object": 123}
        with pytest.raises(ConditionParseError):
            ObjectInteractedCondition.from_dict(data)

    def test_validate_equals_not_bool(self) -> None:
        """Test validator detects non-bool equals field."""
        data = {"object": "test_object", "equals": "yes"}
        with pytest.raises(ConditionParseError):
            ObjectInteractedCondition.from_dict(data)
