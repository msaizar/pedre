"""Tests for script conditions."""

import unittest
from unittest.mock import MagicMock

from pedre.plugins.script.base import Script
from pedre.plugins.script.conditions import check_script_completed


class TestCheckScriptCompleted(unittest.TestCase):
    """Test cases for check_script_completed condition."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_context = MagicMock()
        self.mock_script_plugin = MagicMock()
        self.mock_context.script_plugin = self.mock_script_plugin

    def test_check_script_completed_returns_true(self) -> None:
        """Test that check_script_completed returns True when script is completed."""
        mock_script = MagicMock(spec=Script)
        mock_script.completed = True
        self.mock_script_plugin.get_scripts.return_value = {"test_script": mock_script}

        condition_data = {"script": "test_script"}
        result = check_script_completed(condition_data, self.mock_context)

        assert result is True
        self.mock_script_plugin.get_scripts.assert_called_once()

    def test_check_script_completed_returns_false_not_completed(self) -> None:
        """Test that check_script_completed returns False when script is not completed."""
        mock_script = MagicMock(spec=Script)
        mock_script.completed = False
        self.mock_script_plugin.get_scripts.return_value = {"test_script": mock_script}

        condition_data = {"script": "test_script"}
        result = check_script_completed(condition_data, self.mock_context)

        assert result is False

    def test_check_script_completed_script_not_found(self) -> None:
        """Test that check_script_completed returns False when script is not found."""
        self.mock_script_plugin.get_scripts.return_value = {}

        condition_data = {"script": "nonexistent_script"}
        result = check_script_completed(condition_data, self.mock_context)

        assert result is False
        self.mock_script_plugin.get_scripts.assert_called_once()

    def test_check_script_completed_missing_script_name(self) -> None:
        """Test that missing script name returns False."""
        condition_data = {}
        result = check_script_completed(condition_data, self.mock_context)

        assert result is False
        self.mock_script_plugin.get_scripts.assert_not_called()

    def test_check_script_completed_empty_script_name(self) -> None:
        """Test that empty script name returns False."""
        condition_data = {"script": ""}
        result = check_script_completed(condition_data, self.mock_context)

        assert result is False
        self.mock_script_plugin.get_scripts.assert_not_called()

    def test_check_script_completed_default_empty_string(self) -> None:
        """Test that script defaults to empty string when not provided."""
        condition_data = {"other_key": "value"}
        result = check_script_completed(condition_data, self.mock_context)

        assert result is False

    def test_check_script_completed_with_multiple_scripts(self) -> None:
        """Test checking a specific script when multiple scripts exist."""
        mock_script_completed = MagicMock(spec=Script)
        mock_script_completed.completed = True

        mock_script_not_completed = MagicMock(spec=Script)
        mock_script_not_completed.completed = False

        self.mock_script_plugin.get_scripts.return_value = {
            "completed_script": mock_script_completed,
            "running_script": mock_script_not_completed,
        }

        # Check the completed script
        condition_data = {"script": "completed_script"}
        result = check_script_completed(condition_data, self.mock_context)
        assert result is True

        # Check the not completed script
        condition_data = {"script": "running_script"}
        result = check_script_completed(condition_data, self.mock_context)
        assert result is False

    def test_check_script_completed_with_real_script_object(self) -> None:
        """Test with actual Script dataclass instance."""
        # Create a real Script instance
        completed_script = Script(
            actions=[{"type": "wait", "duration": 1.0}],
            completed=True,
        )

        not_completed_script = Script(
            actions=[{"type": "wait", "duration": 1.0}],
            completed=False,
        )

        self.mock_script_plugin.get_scripts.return_value = {
            "script1": completed_script,
            "script2": not_completed_script,
        }

        # Test completed script
        condition_data = {"script": "script1"}
        result = check_script_completed(condition_data, self.mock_context)
        assert result is True

        # Test not completed script
        condition_data = {"script": "script2"}
        result = check_script_completed(condition_data, self.mock_context)
        assert result is False

    def test_check_script_completed_none_script_name(self) -> None:
        """Test that None script name is handled correctly."""
        # When using .get() with default "", None as a value still returns None
        # The code will evaluate `if not script_name:` which catches None
        mock_script = MagicMock(spec=Script)
        mock_script.completed = True
        self.mock_script_plugin.get_scripts.return_value = {"some_script": mock_script}

        condition_data = {"script": None}
        result = check_script_completed(condition_data, self.mock_context)

        assert result is False


if __name__ == "__main__":
    unittest.main()
