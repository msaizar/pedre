"""Tests for script conditions."""

from unittest.mock import MagicMock

import pytest

from pedre.conditions.registry import ConditionParseError
from pedre.plugins.script.base import Script
from pedre.plugins.script.conditions import ScriptCompletedCondition


@pytest.fixture
def mock_context() -> MagicMock:
    """Create a mock context with a script plugin."""
    context = MagicMock()
    context.script_plugin = MagicMock()
    return context


class TestScriptCompletedCondition:
    """Test cases for ScriptCompletedCondition."""

    def test_check_returns_true(self, mock_context: MagicMock) -> None:
        """Test that check returns True when script is completed."""
        mock_script = MagicMock()
        mock_script.completed = True
        mock_context.script_plugin.get_scripts.return_value = {"test_script": mock_script}

        condition = ScriptCompletedCondition(script_name="test_script")
        result = condition.check(mock_context)

        assert result is True
        mock_context.script_plugin.get_scripts.assert_called_once()

    def test_check_returns_false_not_completed(self, mock_context: MagicMock) -> None:
        """Test that check returns False when script is not completed."""
        mock_script = MagicMock()
        mock_script.completed = False
        mock_context.script_plugin.get_scripts.return_value = {"test_script": mock_script}

        condition = ScriptCompletedCondition(script_name="test_script")
        result = condition.check(mock_context)

        assert result is False

    def test_check_script_not_found(self, mock_context: MagicMock) -> None:
        """Test that check returns False when script is not found."""
        mock_context.script_plugin.get_scripts.return_value = {}

        condition = ScriptCompletedCondition(script_name="nonexistent_script")
        result = condition.check(mock_context)

        assert result is False
        mock_context.script_plugin.get_scripts.assert_called_once()

    def test_check_missing_script_name(self, mock_context: MagicMock) -> None:
        """Test that missing script name returns False."""
        condition = ScriptCompletedCondition(script_name="")
        result = condition.check(mock_context)

        assert result is False
        mock_context.script_plugin.get_scripts.assert_not_called()

    def test_check_with_multiple_scripts(self, mock_context: MagicMock) -> None:
        """Test checking a specific script when multiple scripts exist."""
        mock_script_completed = MagicMock()
        mock_script_completed.completed = True

        mock_script_not_completed = MagicMock()
        mock_script_not_completed.completed = False

        mock_context.script_plugin.get_scripts.return_value = {
            "completed_script": mock_script_completed,
            "running_script": mock_script_not_completed,
        }

        # Check the completed script
        condition = ScriptCompletedCondition(script_name="completed_script")
        result = condition.check(mock_context)
        assert result is True

        # Check the not completed script
        condition = ScriptCompletedCondition(script_name="running_script")
        result = condition.check(mock_context)
        assert result is False

    def test_check_with_real_script_object(self, mock_context: MagicMock) -> None:
        """Test with actual Script dataclass instance."""
        # Create a real Script instance
        mock_action = MagicMock()
        completed_script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[mock_action],
            on_condition_fail=[],
            completed=True,
        )

        not_completed_script = Script(
            trigger=None,
            conditions=[],
            scene=None,
            run_once=False,
            actions=[mock_action],
            on_condition_fail=[],
            completed=False,
        )

        mock_context.script_plugin.get_scripts.return_value = {
            "script1": completed_script,
            "script2": not_completed_script,
        }

        # Test completed script
        condition = ScriptCompletedCondition(script_name="script1")
        result = condition.check(mock_context)
        assert result is True

        # Test not completed script
        condition = ScriptCompletedCondition(script_name="script2")
        result = condition.check(mock_context)
        assert result is False

    def test_validate_success(self) -> None:
        """Test validator passes with valid data."""
        data = {"script": "test_script"}
        ScriptCompletedCondition.from_dict(data)

    def test_validate_missing_script(self) -> None:
        """Test validator detects missing script field."""
        data = {}
        with pytest.raises(ConditionParseError, match="missing required 'script' field"):
            ScriptCompletedCondition.from_dict(data)

    def test_validate_empty_script(self) -> None:
        """Test validator detects empty script field."""
        data = {"script": ""}
        with pytest.raises(ConditionParseError, match="missing required 'script' field"):
            ScriptCompletedCondition.from_dict(data)

    def test_validate_script_not_string(self) -> None:
        """Test validator detects non-string script field."""
        data = {"script": 123}
        with pytest.raises(ConditionParseError, match="'script' must be a string"):
            ScriptCompletedCondition.from_dict(data)
