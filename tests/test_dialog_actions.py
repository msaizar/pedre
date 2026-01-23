"""Unit tests for dialog actions."""

import unittest
from unittest.mock import MagicMock

from pedre.systems.dialog.actions import DialogAction, WaitForDialogCloseAction


class TestDialogAction(unittest.TestCase):
    """Test DialogAction."""

    def test_init_defaults(self) -> None:
        """Test DialogAction initialization with defaults."""
        action = DialogAction("TestNPC", ["Hello!"])

        assert action.speaker == "TestNPC"
        assert action.text == ["Hello!"]
        assert action.instant is False
        assert action.auto_close is False
        assert action.started is False

    def test_init_with_instant(self) -> None:
        """Test DialogAction initialization with instant=True."""
        action = DialogAction("TestNPC", ["Hello!"], instant=True)

        assert action.instant is True
        assert action.auto_close is False

    def test_init_with_auto_close(self) -> None:
        """Test DialogAction initialization with auto_close=True."""
        action = DialogAction("TestNPC", ["Hello!"], auto_close=True)

        assert action.instant is False
        assert action.auto_close is True

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
        assert action.instant is False
        assert action.auto_close is False

    def test_from_dict_with_instant(self) -> None:
        """Test creating DialogAction from dict with instant=true."""
        data = {"speaker": "Narrator", "text": ["The story begins..."], "instant": True}
        action = DialogAction.from_dict(data)

        assert action.speaker == "Narrator"
        assert action.instant is True
        assert action.auto_close is False

    def test_from_dict_with_auto_close(self) -> None:
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
        """Test that execute calls show_dialog on DialogManager."""
        action = DialogAction("TestNPC", ["Hello!"])
        context = MagicMock()
        dialog_manager = MagicMock()
        context.get_system.return_value = dialog_manager

        result = action.execute(context)

        assert result is True
        dialog_manager.show_dialog.assert_called_once_with("TestNPC", ["Hello!"], instant=False, auto_close=False)
        assert action.started is True

    def test_execute_passes_instant_flag(self) -> None:
        """Test that execute passes instant flag to DialogManager."""
        action = DialogAction("TestNPC", ["Hello!"], instant=True)
        context = MagicMock()
        dialog_manager = MagicMock()
        context.get_system.return_value = dialog_manager

        action.execute(context)

        dialog_manager.show_dialog.assert_called_once_with("TestNPC", ["Hello!"], instant=True, auto_close=False)

    def test_execute_passes_auto_close_flag(self) -> None:
        """Test that execute passes auto_close flag to DialogManager."""
        action = DialogAction("TestNPC", ["Hello!"], auto_close=True)
        context = MagicMock()
        dialog_manager = MagicMock()
        context.get_system.return_value = dialog_manager

        action.execute(context)

        dialog_manager.show_dialog.assert_called_once_with("TestNPC", ["Hello!"], instant=False, auto_close=True)

    def test_execute_passes_both_flags(self) -> None:
        """Test that execute passes both flags to DialogManager."""
        action = DialogAction("TestNPC", ["Hello!"], instant=True, auto_close=True)
        context = MagicMock()
        dialog_manager = MagicMock()
        context.get_system.return_value = dialog_manager

        action.execute(context)

        dialog_manager.show_dialog.assert_called_once_with("TestNPC", ["Hello!"], instant=True, auto_close=True)

    def test_execute_without_dialog_manager(self) -> None:
        """Test execute handles missing dialog manager gracefully."""
        action = DialogAction("TestNPC", ["Hello!"])
        context = MagicMock()
        context.get_system.return_value = None

        result = action.execute(context)

        assert result is True
        assert action.started is True

    def test_execute_only_once(self) -> None:
        """Test that dialog is only shown once even if execute called multiple times."""
        action = DialogAction("TestNPC", ["Hello!"])
        context = MagicMock()
        dialog_manager = MagicMock()
        context.get_system.return_value = dialog_manager

        action.execute(context)
        action.execute(context)

        dialog_manager.show_dialog.assert_called_once()

    def test_reset(self) -> None:
        """Test reset clears started flag."""
        action = DialogAction("TestNPC", ["Hello!"])
        context = MagicMock()
        dialog_manager = MagicMock()
        context.get_system.return_value = dialog_manager

        action.execute(context)
        assert action.started is True

        action.reset()
        assert action.started is False


class TestWaitForDialogCloseAction(unittest.TestCase):
    """Test WaitForDialogCloseAction."""

    def test_from_dict(self) -> None:
        """Test creating WaitForDialogCloseAction from dictionary."""
        action = WaitForDialogCloseAction.from_dict({})
        assert action is not None


if __name__ == "__main__":
    unittest.main()
