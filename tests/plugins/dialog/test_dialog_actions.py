"""Unit tests for dialog actions."""

import unittest
from unittest.mock import MagicMock

from pedre.plugins.dialog.actions import DialogAction, WaitForDialogCloseAction


class TestDialogAction(unittest.TestCase):
    """Test DialogAction."""

    def test_init_defaults(self) -> None:
        """Test DialogAction initialization with defaults."""
        action = DialogAction("TestNPC", ["Hello!"])

        assert action.speaker == "TestNPC"
        assert action.text == ["Hello!"]
        assert action.instant is False  # Default from settings.DIALOG_INSTANT_TEXT_DEFAULT
        assert action.auto_close is False  # Default from settings.DIALOG_AUTO_CLOSE_DEFAULT
        assert action.started is False

    def test_init_with_instant(self) -> None:
        """Test DialogAction initialization with instant=True."""
        action = DialogAction("TestNPC", ["Hello!"], instant=True)

        assert action.instant is True
        assert action.auto_close is False  # Default from settings

    def test_init_with_auto_close_true(self) -> None:
        """Test DialogAction initialization with auto_close=True."""
        action = DialogAction("TestNPC", ["Hello!"], auto_close=True)

        assert action.instant is False
        assert action.auto_close is True

    def test_init_with_auto_close_false(self) -> None:
        """Test DialogAction initialization with auto_close=False."""
        action = DialogAction("TestNPC", ["Hello!"], auto_close=False)

        assert action.instant is False
        assert action.auto_close is False

    def test_init_with_both_flags(self) -> None:
        """Test DialogAction initialization with both instant and auto_close."""
        action = DialogAction("TestNPC", ["Hello!"], instant=True, auto_close=True)

        assert action.instant is True
        assert action.auto_close is True

    def test_from_dict_defaults(self) -> None:
        """Test creating DialogAction from dict with defaults."""
        data = {"speaker": "Merchant", "text": ["Welcome!"]}
        action = DialogAction.from_dict(data)

        assert action.speaker == "Merchant"
        assert action.text == ["Welcome!"]
        assert action.instant is False  # Default from settings
        assert action.auto_close is False  # Default from settings

    def test_from_dict_with_instant(self) -> None:
        """Test creating DialogAction from dict with instant=true."""
        data = {"speaker": "Narrator", "text": ["The story begins..."], "instant": True}
        action = DialogAction.from_dict(data)

        assert action.speaker == "Narrator"
        assert action.instant is True
        assert action.auto_close is False  # Default from settings

    def test_from_dict_with_auto_close_true(self) -> None:
        """Test creating DialogAction from dict with auto_close=true."""
        data = {
            "speaker": "Narrator",
            "text": ["This will auto-close..."],
            "auto_close": True,
        }
        action = DialogAction.from_dict(data)

        assert action.speaker == "Narrator"
        assert action.auto_close is True
        assert action.instant is False

    def test_from_dict_with_auto_close_false(self) -> None:
        """Test creating DialogAction from dict with auto_close=false."""
        data = {
            "speaker": "Narrator",
            "text": ["This will not auto-close..."],
            "auto_close": False,
        }
        action = DialogAction.from_dict(data)

        assert action.speaker == "Narrator"
        assert action.auto_close is False
        assert action.instant is False

    def test_from_dict_with_both_flags(self) -> None:
        """Test creating DialogAction from dict with both flags."""
        data = {
            "speaker": "Narrator",
            "text": ["Instant and auto-close"],
            "instant": True,
            "auto_close": True,
        }
        action = DialogAction.from_dict(data)

        assert action.instant is True
        assert action.auto_close is True

    def test_execute_calls_show_dialog(self) -> None:
        """Test that execute calls show_dialog on DialogPlugin."""
        action = DialogAction("TestNPC", ["Hello!"])
        context = MagicMock()
        dialog_plugin = MagicMock()
        context.dialog_plugin = dialog_plugin

        result = action.execute(context)

        assert result is True
        dialog_plugin.show_dialog.assert_called_once_with("TestNPC", ["Hello!"], instant=False, auto_close=False)
        assert action.started is True

    def test_execute_passes_instant_flag(self) -> None:
        """Test that execute passes instant flag to DialogPlugin."""
        action = DialogAction("TestNPC", ["Hello!"], instant=True)
        context = MagicMock()
        dialog_plugin = MagicMock()
        context.dialog_plugin = dialog_plugin

        action.execute(context)

        dialog_plugin.show_dialog.assert_called_once_with("TestNPC", ["Hello!"], instant=True, auto_close=False)

    def test_execute_passes_auto_close_flag(self) -> None:
        """Test that execute passes auto_close flag to DialogPlugin."""
        action = DialogAction("TestNPC", ["Hello!"], auto_close=True)
        context = MagicMock()
        dialog_plugin = MagicMock()
        context.dialog_plugin = dialog_plugin

        action.execute(context)

        dialog_plugin.show_dialog.assert_called_once_with("TestNPC", ["Hello!"], instant=False, auto_close=True)

    def test_execute_passes_both_flags(self) -> None:
        """Test that execute passes both flags to DialogPlugin."""
        action = DialogAction("TestNPC", ["Hello!"], instant=True, auto_close=True)
        context = MagicMock()
        dialog_plugin = MagicMock()
        context.dialog_plugin = dialog_plugin

        action.execute(context)

        dialog_plugin.show_dialog.assert_called_once_with("TestNPC", ["Hello!"], instant=True, auto_close=True)

    def test_execute_only_once(self) -> None:
        """Test that dialog is only shown once even if execute called multiple times."""
        action = DialogAction("TestNPC", ["Hello!"])
        context = MagicMock()
        dialog_plugin = MagicMock()
        context.dialog_plugin = dialog_plugin

        action.execute(context)
        action.execute(context)

        dialog_plugin.show_dialog.assert_called_once()

    def test_reset(self) -> None:
        """Test reset clears started flag."""
        action = DialogAction("TestNPC", ["Hello!"])
        context = MagicMock()
        dialog_plugin = MagicMock()
        context.dialog_plugin = dialog_plugin

        action.execute(context)
        assert action.started is True

        action.reset()
        assert action.started is False


class TestDialogActionValidation(unittest.TestCase):
    """Test DialogAction validation."""

    def test_validate_params_success(self) -> None:
        """Test validate_params with valid data."""
        data = {"text": ["Hello!"], "speaker": "TestNPC"}
        errors = DialogAction.validate_params(data)
        assert errors == []

    def test_validate_params_missing_text(self) -> None:
        """Test validate_params detects missing text field."""
        data = {"speaker": "TestNPC"}
        errors = DialogAction.validate_params(data)
        assert len(errors) == 1
        assert "missing required 'text' field" in errors[0]

    def test_validate_params_empty_text(self) -> None:
        """Test validate_params detects empty text field."""
        data = {"text": "", "speaker": "TestNPC"}
        errors = DialogAction.validate_params(data)
        assert len(errors) == 1
        assert "missing required 'text' field" in errors[0]

    def test_validate_params_missing_speaker(self) -> None:
        """Test validate_params detects missing speaker field."""
        data = {"text": ["Hello!"]}
        errors = DialogAction.validate_params(data)
        assert len(errors) == 1
        assert "missing required 'speaker' field" in errors[0]

    def test_validate_params_empty_speaker(self) -> None:
        """Test validate_params detects empty speaker field."""
        data = {"text": ["Hello!"], "speaker": ""}
        errors = DialogAction.validate_params(data)
        assert len(errors) == 1
        assert "missing required 'speaker' field" in errors[0]

    def test_validate_params_missing_both_fields(self) -> None:
        """Test validate_params detects both missing fields."""
        data = {}
        errors = DialogAction.validate_params(data)
        assert len(errors) == 2
        assert any("'text'" in e for e in errors)
        assert any("'speaker'" in e for e in errors)

    def test_validate_params_text_wrong_type_not_list(self) -> None:
        """Test validate_params detects text field that is not a list."""
        data = {"text": "not a list", "speaker": "TestNPC"}
        errors = DialogAction.validate_params(data)
        assert len(errors) == 1
        assert "'text' must be a list" in errors[0]

    def test_validate_params_text_items_not_strings(self) -> None:
        """Test validate_params detects non-string items in text list."""
        data = {"text": [123, 456], "speaker": "TestNPC"}
        errors = DialogAction.validate_params(data)
        assert len(errors) == 1
        assert "'text' items must be strings" in errors[0]

    def test_validate_params_speaker_wrong_type(self) -> None:
        """Test validate_params detects speaker field that is not a string."""
        data = {"text": ["Hello!"], "speaker": 123}
        errors = DialogAction.validate_params(data)
        assert len(errors) == 1
        assert "'speaker' must be a string" in errors[0]

    def test_validate_params_instant_wrong_type(self) -> None:
        """Test validate_params detects instant field that is not a bool."""
        data = {"text": ["Hello!"], "speaker": "TestNPC", "instant": "yes"}
        errors = DialogAction.validate_params(data)
        assert len(errors) == 1
        assert "'instant' must be a bool" in errors[0]

    def test_validate_params_auto_close_wrong_type(self) -> None:
        """Test validate_params detects auto_close field that is not a bool."""
        data = {"text": ["Hello!"], "speaker": "TestNPC", "auto_close": 1}
        errors = DialogAction.validate_params(data)
        assert len(errors) == 1
        assert "'auto_close' must be a bool" in errors[0]

    def test_validate_params_valid_with_optional_bools(self) -> None:
        """Test validate_params passes with valid optional bool fields."""
        data = {"text": ["Hello!"], "speaker": "TestNPC", "instant": True, "auto_close": False}
        errors = DialogAction.validate_params(data)
        assert errors == []


class TestWaitForDialogCloseAction(unittest.TestCase):
    """Test WaitForDialogCloseAction."""

    def test_from_dict(self) -> None:
        """Test creating WaitForDialogCloseAction from dictionary."""
        action = WaitForDialogCloseAction.from_dict({})
        assert action is not None

    def test_execute_returns_false_when_dialog_showing(self) -> None:
        """Test execute returns False when dialog is still showing."""
        action = WaitForDialogCloseAction()
        context = MagicMock()
        dialog_plugin = MagicMock()
        dialog_plugin.is_showing.return_value = True
        context.dialog_plugin = dialog_plugin

        result = action.execute(context)

        assert result is False

    def test_execute_returns_true_when_dialog_closed(self) -> None:
        """Test execute returns True when dialog is closed."""
        action = WaitForDialogCloseAction()
        context = MagicMock()
        dialog_plugin = MagicMock()
        dialog_plugin.is_showing.return_value = False
        context.dialog_plugin = dialog_plugin

        result = action.execute(context)

        assert result is True

    def test_execute_returns_true_when_dialog_plugin_is_none(self) -> None:
        """Test execute returns True when dialog_plugin is None."""
        action = WaitForDialogCloseAction()
        context = MagicMock()
        context.dialog_plugin = None

        result = action.execute(context)

        assert result is True


if __name__ == "__main__":
    unittest.main()
