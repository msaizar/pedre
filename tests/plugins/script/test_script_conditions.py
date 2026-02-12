"""Tests for script conditions."""

import unittest
from unittest.mock import MagicMock

from pedre.plugins.script.base import Script
from pedre.plugins.script.conditions import ScriptCompletedCondition


class TestScriptCompletedCondition(unittest.TestCase):
    """Test cases for ScriptCompletedCondition."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_context = MagicMock()
        self.mock_script_plugin = MagicMock()
        self.mock_context.script_plugin = self.mock_script_plugin

    def test_check_returns_true(self) -> None:
        """Test that check returns True when script is completed."""
        mock_script = MagicMock()
        mock_script.completed = True
        self.mock_script_plugin.get_scripts.return_value = {"test_script": mock_script}

        condition = ScriptCompletedCondition(script_name="test_script")
        result = condition.check(self.mock_context)

        assert result is True
        self.mock_script_plugin.get_scripts.assert_called_once()

    def test_check_returns_false_not_completed(self) -> None:
        """Test that check returns False when script is not completed."""
        mock_script = MagicMock()
        mock_script.completed = False
        self.mock_script_plugin.get_scripts.return_value = {"test_script": mock_script}

        condition = ScriptCompletedCondition(script_name="test_script")
        result = condition.check(self.mock_context)

        assert result is False

    def test_check_script_not_found(self) -> None:
        """Test that check returns False when script is not found."""
        self.mock_script_plugin.get_scripts.return_value = {}

        condition = ScriptCompletedCondition(script_name="nonexistent_script")
        result = condition.check(self.mock_context)

        assert result is False
        self.mock_script_plugin.get_scripts.assert_called_once()

    def test_check_missing_script_name(self) -> None:
        """Test that missing script name returns False."""
        condition = ScriptCompletedCondition(script_name="")
        result = condition.check(self.mock_context)

        assert result is False
        self.mock_script_plugin.get_scripts.assert_not_called()

    def test_check_with_multiple_scripts(self) -> None:
        """Test checking a specific script when multiple scripts exist."""
        mock_script_completed = MagicMock()
        mock_script_completed.completed = True

        mock_script_not_completed = MagicMock()
        mock_script_not_completed.completed = False

        self.mock_script_plugin.get_scripts.return_value = {
            "completed_script": mock_script_completed,
            "running_script": mock_script_not_completed,
        }

        # Check the completed script
        condition = ScriptCompletedCondition(script_name="completed_script")
        result = condition.check(self.mock_context)
        assert result is True

        # Check the not completed script
        condition = ScriptCompletedCondition(script_name="running_script")
        result = condition.check(self.mock_context)
        assert result is False

    def test_check_with_real_script_object(self) -> None:
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
        condition = ScriptCompletedCondition(script_name="script1")
        result = condition.check(self.mock_context)
        assert result is True

        # Test not completed script
        condition = ScriptCompletedCondition(script_name="script2")
        result = condition.check(self.mock_context)
        assert result is False

    def test_validate_success(self) -> None:
        """Test validator passes with valid data."""
        data = {"script": "test_script"}
        errors = ScriptCompletedCondition.validate_params(data)
        assert errors == []

    def test_validate_missing_script(self) -> None:
        """Test validator detects missing script field."""
        data = {}
        errors = ScriptCompletedCondition.validate_params(data)
        assert len(errors) == 1
        assert "missing required 'script' field" in errors[0]

    def test_validate_empty_script(self) -> None:
        """Test validator detects empty script field."""
        data = {"script": ""}
        errors = ScriptCompletedCondition.validate_params(data)
        assert len(errors) == 1
        assert "missing required 'script' field" in errors[0]

    def test_validate_script_not_string(self) -> None:
        """Test validator detects non-string script field."""
        data = {"script": 123}
        errors = ScriptCompletedCondition.validate_params(data)
        assert len(errors) == 1
        assert "'script' must be a string" in errors[0]


if __name__ == "__main__":
    unittest.main()
