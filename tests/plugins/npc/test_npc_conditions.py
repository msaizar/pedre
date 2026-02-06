"""Tests for NPC conditions."""

import unittest
from unittest.mock import MagicMock

from pedre.plugins.npc.base import NPCState
from pedre.plugins.npc.conditions import check_npc_dialog_level, check_npc_interacted


class TestCheckNpcInteracted(unittest.TestCase):
    """Test cases for check_npc_interacted condition."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_context = MagicMock()
        self.mock_npc_plugin = MagicMock()
        self.mock_context.npc_plugin = self.mock_npc_plugin

    def test_check_npc_interacted_returns_true(self) -> None:
        """Test that check_npc_interacted returns True when NPC was interacted with."""
        self.mock_npc_plugin.has_npc_been_interacted_with.return_value = True

        condition_data = {"npc": "test_npc"}
        result = check_npc_interacted(condition_data, self.mock_context)

        assert result is True
        self.mock_npc_plugin.has_npc_been_interacted_with.assert_called_once_with("test_npc", None)

    def test_check_npc_interacted_returns_false(self) -> None:
        """Test that check_npc_interacted returns False when NPC was not interacted with."""
        self.mock_npc_plugin.has_npc_been_interacted_with.return_value = False

        condition_data = {"npc": "test_npc"}
        result = check_npc_interacted(condition_data, self.mock_context)

        assert result is False
        self.mock_npc_plugin.has_npc_been_interacted_with.assert_called_once_with("test_npc", None)

    def test_check_npc_interacted_with_scene_name(self) -> None:
        """Test check_npc_interacted with specific scene name."""
        self.mock_npc_plugin.has_npc_been_interacted_with.return_value = True

        condition_data = {"npc": "test_npc", "scene": "village"}
        result = check_npc_interacted(condition_data, self.mock_context)

        assert result is True
        self.mock_npc_plugin.has_npc_been_interacted_with.assert_called_once_with("test_npc", "village")

    def test_check_npc_interacted_with_equals_true(self) -> None:
        """Test check_npc_interacted with explicit equals=True."""
        self.mock_npc_plugin.has_npc_been_interacted_with.return_value = True

        condition_data = {"npc": "test_npc", "equals": True}
        result = check_npc_interacted(condition_data, self.mock_context)

        assert result is True

    def test_check_npc_interacted_with_equals_false(self) -> None:
        """Test check_npc_interacted with equals=False (negative check)."""
        self.mock_npc_plugin.has_npc_been_interacted_with.return_value = False

        condition_data = {"npc": "test_npc", "equals": False}
        result = check_npc_interacted(condition_data, self.mock_context)

        assert result is True  # NPC was NOT interacted with, which matches equals=False

    def test_check_npc_interacted_equals_false_when_interacted(self) -> None:
        """Test equals=False returns False when NPC was actually interacted with."""
        self.mock_npc_plugin.has_npc_been_interacted_with.return_value = True

        condition_data = {"npc": "test_npc", "equals": False}
        result = check_npc_interacted(condition_data, self.mock_context)

        assert result is False  # NPC WAS interacted with, which doesn't match equals=False

    def test_check_npc_interacted_missing_npc_name(self) -> None:
        """Test that missing NPC name returns False."""
        condition_data = {}
        result = check_npc_interacted(condition_data, self.mock_context)

        assert result is False
        self.mock_npc_plugin.has_npc_been_interacted_with.assert_not_called()

    def test_check_npc_interacted_empty_npc_name(self) -> None:
        """Test that empty NPC name returns False."""
        condition_data = {"npc": ""}
        result = check_npc_interacted(condition_data, self.mock_context)

        assert result is False
        self.mock_npc_plugin.has_npc_been_interacted_with.assert_not_called()

    def test_check_npc_interacted_none_npc_name(self) -> None:
        """Test that None NPC name returns False."""
        condition_data = {"npc": None}
        result = check_npc_interacted(condition_data, self.mock_context)

        assert result is False
        self.mock_npc_plugin.has_npc_been_interacted_with.assert_not_called()

    def test_check_npc_interacted_with_scene_and_equals(self) -> None:
        """Test check_npc_interacted with both scene and equals parameters."""
        self.mock_npc_plugin.has_npc_been_interacted_with.return_value = True

        condition_data = {"npc": "guard", "scene": "castle", "equals": True}
        result = check_npc_interacted(condition_data, self.mock_context)

        assert result is True
        self.mock_npc_plugin.has_npc_been_interacted_with.assert_called_once_with("guard", "castle")


class TestCheckNpcDialogLevel(unittest.TestCase):
    """Test cases for check_npc_dialog_level condition."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_context = MagicMock()
        self.mock_npc_plugin = MagicMock()
        self.mock_context.npc_plugin = self.mock_npc_plugin

    def test_check_npc_dialog_level_returns_true(self) -> None:
        """Test that check_npc_dialog_level returns True when dialog level matches."""
        mock_npc_state = MagicMock(spec=NPCState)
        mock_npc_state.dialog_level = 3
        self.mock_npc_plugin.get_npc_by_name.return_value = mock_npc_state

        condition_data = {"npc": "test_npc", "equals": 3}
        result = check_npc_dialog_level(condition_data, self.mock_context)

        assert result is True
        self.mock_npc_plugin.get_npc_by_name.assert_called_once_with("test_npc")

    def test_check_npc_dialog_level_returns_false_wrong_level(self) -> None:
        """Test that check_npc_dialog_level returns False when dialog level doesn't match."""
        mock_npc_state = MagicMock(spec=NPCState)
        mock_npc_state.dialog_level = 2
        self.mock_npc_plugin.get_npc_by_name.return_value = mock_npc_state

        condition_data = {"npc": "test_npc", "equals": 3}
        result = check_npc_dialog_level(condition_data, self.mock_context)

        assert result is False

    def test_check_npc_dialog_level_zero_level(self) -> None:
        """Test check_npc_dialog_level with dialog level 0."""
        mock_npc_state = MagicMock(spec=NPCState)
        mock_npc_state.dialog_level = 0
        self.mock_npc_plugin.get_npc_by_name.return_value = mock_npc_state

        condition_data = {"npc": "test_npc", "equals": 0}
        result = check_npc_dialog_level(condition_data, self.mock_context)

        assert result is True

    def test_check_npc_dialog_level_npc_not_found(self) -> None:
        """Test that check_npc_dialog_level returns False when NPC is not found."""
        self.mock_npc_plugin.get_npc_by_name.return_value = None

        condition_data = {"npc": "nonexistent_npc", "equals": 3}
        result = check_npc_dialog_level(condition_data, self.mock_context)

        assert result is False
        self.mock_npc_plugin.get_npc_by_name.assert_called_once_with("nonexistent_npc")

    def test_check_npc_dialog_level_missing_npc_name(self) -> None:
        """Test that missing NPC name returns False."""
        condition_data = {"equals": 3}
        result = check_npc_dialog_level(condition_data, self.mock_context)

        assert result is False
        self.mock_npc_plugin.get_npc_by_name.assert_not_called()

    def test_check_npc_dialog_level_empty_npc_name(self) -> None:
        """Test that empty NPC name returns False."""
        condition_data = {"npc": "", "equals": 3}
        result = check_npc_dialog_level(condition_data, self.mock_context)

        assert result is False
        self.mock_npc_plugin.get_npc_by_name.assert_not_called()

    def test_check_npc_dialog_level_none_npc_name(self) -> None:
        """Test that None NPC name returns False."""
        condition_data = {"npc": None, "equals": 3}
        result = check_npc_dialog_level(condition_data, self.mock_context)

        assert result is False
        self.mock_npc_plugin.get_npc_by_name.assert_not_called()

    def test_check_npc_dialog_level_missing_equals(self) -> None:
        """Test that missing equals parameter returns False."""
        mock_npc_state = MagicMock(spec=NPCState)
        mock_npc_state.dialog_level = 3
        self.mock_npc_plugin.get_npc_by_name.return_value = mock_npc_state

        condition_data = {"npc": "test_npc"}
        result = check_npc_dialog_level(condition_data, self.mock_context)

        assert result is False
        self.mock_npc_plugin.get_npc_by_name.assert_not_called()

    def test_check_npc_dialog_level_none_equals(self) -> None:
        """Test that None equals parameter returns False."""
        condition_data = {"npc": "test_npc", "equals": None}
        result = check_npc_dialog_level(condition_data, self.mock_context)

        assert result is False
        self.mock_npc_plugin.get_npc_by_name.assert_not_called()

    def test_check_npc_dialog_level_with_negative_level(self) -> None:
        """Test check_npc_dialog_level with negative dialog level (edge case)."""
        mock_npc_state = MagicMock(spec=NPCState)
        mock_npc_state.dialog_level = -1
        self.mock_npc_plugin.get_npc_by_name.return_value = mock_npc_state

        condition_data = {"npc": "test_npc", "equals": -1}
        result = check_npc_dialog_level(condition_data, self.mock_context)

        assert result is True

    def test_check_npc_dialog_level_with_high_level(self) -> None:
        """Test check_npc_dialog_level with high dialog level."""
        mock_npc_state = MagicMock(spec=NPCState)
        mock_npc_state.dialog_level = 100
        self.mock_npc_plugin.get_npc_by_name.return_value = mock_npc_state

        condition_data = {"npc": "test_npc", "equals": 100}
        result = check_npc_dialog_level(condition_data, self.mock_context)

        assert result is True


if __name__ == "__main__":
    unittest.main()
