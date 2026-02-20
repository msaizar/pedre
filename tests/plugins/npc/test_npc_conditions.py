"""Tests for NPC conditions."""

import unittest
from unittest.mock import MagicMock

import pytest

from pedre.conditions.registry import ConditionParseError
from pedre.plugins.npc.conditions import (
    NPCDialogLevelCondition,
    NPCInteractedCondition,
)


class TestNPCInteractedCondition(unittest.TestCase):
    """Test cases for NPCInteractedCondition."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_context = MagicMock()
        self.mock_npc_plugin = MagicMock()
        self.mock_context.npc_plugin = self.mock_npc_plugin

    def test_check_returns_true(self) -> None:
        """Test that check returns True when NPC was interacted with."""
        self.mock_npc_plugin.has_npc_been_interacted_with.return_value = True

        condition = NPCInteractedCondition(npc_name="test_npc")
        result = condition.check(self.mock_context)

        assert result is True
        self.mock_npc_plugin.has_npc_been_interacted_with.assert_called_once_with("test_npc", None)

    def test_check_returns_false(self) -> None:
        """Test that check returns False when NPC was not interacted with."""
        self.mock_npc_plugin.has_npc_been_interacted_with.return_value = False

        condition = NPCInteractedCondition(npc_name="test_npc")
        result = condition.check(self.mock_context)

        assert result is False
        self.mock_npc_plugin.has_npc_been_interacted_with.assert_called_once_with("test_npc", None)

    def test_check_with_scene_name(self) -> None:
        """Test check with specific scene name."""
        self.mock_npc_plugin.has_npc_been_interacted_with.return_value = True

        condition = NPCInteractedCondition(npc_name="test_npc", scene_name="village")
        result = condition.check(self.mock_context)

        assert result is True
        self.mock_npc_plugin.has_npc_been_interacted_with.assert_called_once_with("test_npc", "village")

    def test_check_with_equals_true(self) -> None:
        """Test check with explicit equals=True."""
        self.mock_npc_plugin.has_npc_been_interacted_with.return_value = True

        condition = NPCInteractedCondition(npc_name="test_npc", expected=True)
        result = condition.check(self.mock_context)

        assert result is True

    def test_check_with_equals_false(self) -> None:
        """Test check with equals=False (negative check)."""
        self.mock_npc_plugin.has_npc_been_interacted_with.return_value = False

        condition = NPCInteractedCondition(npc_name="test_npc", expected=False)
        result = condition.check(self.mock_context)

        assert result is True  # NPC was NOT interacted with, which matches equals=False

    def test_check_equals_false_when_interacted(self) -> None:
        """Test equals=False returns False when NPC was actually interacted with."""
        self.mock_npc_plugin.has_npc_been_interacted_with.return_value = True

        condition = NPCInteractedCondition(npc_name="test_npc", expected=False)
        result = condition.check(self.mock_context)

        assert result is False  # NPC WAS interacted with, which doesn't match equals=False

    def test_check_missing_npc_name(self) -> None:
        """Test that missing NPC name returns False."""
        condition = NPCInteractedCondition(npc_name="")
        result = condition.check(self.mock_context)

        assert result is False
        self.mock_npc_plugin.has_npc_been_interacted_with.assert_not_called()

    def test_validate_success(self) -> None:
        """Test validator passes with valid data."""
        data = {"npc": "test_npc"}
        NPCInteractedCondition.from_dict(data)

    def test_validate_missing_npc(self) -> None:
        """Test validator detects missing npc field."""
        data = {}
        with pytest.raises(ConditionParseError, match="missing required 'npc' field"):
            NPCInteractedCondition.from_dict(data)

    def test_validate_empty_npc(self) -> None:
        """Test validator detects empty npc field."""
        data = {"npc": ""}
        with pytest.raises(ConditionParseError, match="missing required 'npc' field"):
            NPCInteractedCondition.from_dict(data)

    def test_validate_npc_not_string(self) -> None:
        """Test validator detects non-string npc field."""
        data = {"npc": 123}
        with pytest.raises(ConditionParseError, match="'npc' must be a string"):
            NPCInteractedCondition.from_dict(data)

    def test_validate_scene_not_string(self) -> None:
        """Test validator detects non-string scene field."""
        data = {"npc": "test_npc", "scene": 123}
        with pytest.raises(ConditionParseError, match="'scene' must be a string"):
            NPCInteractedCondition.from_dict(data)

    def test_validate_equals_not_bool(self) -> None:
        """Test validator detects non-bool equals field."""
        data = {"npc": "test_npc", "equals": "yes"}
        with pytest.raises(ConditionParseError, match="'equals' must be a bool"):
            NPCInteractedCondition.from_dict(data)


class TestNPCDialogLevelCondition(unittest.TestCase):
    """Test cases for NPCDialogLevelCondition."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_context = MagicMock()
        self.mock_npc_plugin = MagicMock()
        self.mock_context.npc_plugin = self.mock_npc_plugin

    def test_check_returns_true(self) -> None:
        """Test that check returns True when dialog level matches."""
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 3
        self.mock_npc_plugin.get_npc_by_name.return_value = mock_npc_state

        condition = NPCDialogLevelCondition(npc_name="test_npc", expected_level=3)
        result = condition.check(self.mock_context)

        assert result is True
        self.mock_npc_plugin.get_npc_by_name.assert_called_once_with("test_npc")

    def test_check_returns_false_wrong_level(self) -> None:
        """Test that check returns False when dialog level doesn't match."""
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 2
        self.mock_npc_plugin.get_npc_by_name.return_value = mock_npc_state

        condition = NPCDialogLevelCondition(npc_name="test_npc", expected_level=3)
        result = condition.check(self.mock_context)

        assert result is False

    def test_check_zero_level(self) -> None:
        """Test check with dialog level 0."""
        mock_npc_state = MagicMock()
        mock_npc_state.dialog_level = 0
        self.mock_npc_plugin.get_npc_by_name.return_value = mock_npc_state

        condition = NPCDialogLevelCondition(npc_name="test_npc", expected_level=0)
        result = condition.check(self.mock_context)

        assert result is True

    def test_check_npc_not_found(self) -> None:
        """Test that check returns False when NPC is not found."""
        self.mock_npc_plugin.get_npc_by_name.return_value = None

        condition = NPCDialogLevelCondition(npc_name="nonexistent_npc", expected_level=3)
        result = condition.check(self.mock_context)

        assert result is False
        self.mock_npc_plugin.get_npc_by_name.assert_called_once_with("nonexistent_npc")

    def test_check_missing_npc_name(self) -> None:
        """Test that missing NPC name returns False."""
        condition = NPCDialogLevelCondition(npc_name="", expected_level=3)
        result = condition.check(self.mock_context)

        assert result is False
        self.mock_npc_plugin.get_npc_by_name.assert_not_called()

    def test_validate_success(self) -> None:
        """Test validator passes with valid data."""
        data = {"npc": "test_npc", "equals": 2}
        NPCDialogLevelCondition.from_dict(data)

    def test_validate_missing_npc(self) -> None:
        """Test validator detects missing npc field."""
        data = {"equals": 2}
        with pytest.raises(ConditionParseError, match="missing required 'npc' field"):
            NPCDialogLevelCondition.from_dict(data)

    def test_validate_empty_npc(self) -> None:
        """Test validator detects empty npc field."""
        data = {"npc": "", "equals": 2}
        with pytest.raises(ConditionParseError, match="missing required 'npc' field"):
            NPCDialogLevelCondition.from_dict(data)

    def test_validate_missing_equals(self) -> None:
        """Test validator detects missing equals field."""
        data = {"npc": "test_npc"}
        with pytest.raises(ConditionParseError, match="missing required 'equals' field"):
            NPCDialogLevelCondition.from_dict(data)

    def test_validate_equals_zero(self) -> None:
        """Test validator accepts equals=0."""
        data = {"npc": "test_npc", "equals": 0}
        NPCDialogLevelCondition.from_dict(data)

    def test_validate_npc_not_string(self) -> None:
        """Test validator detects non-string npc field."""
        data = {"npc": 123, "equals": 2}
        with pytest.raises(ConditionParseError, match="'npc' must be a string"):
            NPCDialogLevelCondition.from_dict(data)

    def test_validate_equals_not_int(self) -> None:
        """Test validator detects non-int equals field."""
        data = {"npc": "test_npc", "equals": "2"}
        with pytest.raises(ConditionParseError, match="'equals' must be an int"):
            NPCDialogLevelCondition.from_dict(data)

    def test_validate_equals_bool(self) -> None:
        """Test validator detects bool equals field."""
        data = {"npc": "test_npc", "equals": True}
        with pytest.raises(ConditionParseError, match="'equals' must be an int"):
            NPCDialogLevelCondition.from_dict(data)
