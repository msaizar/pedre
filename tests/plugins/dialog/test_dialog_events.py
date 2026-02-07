"""Unit tests for dialog events."""

import unittest

from pedre.plugins.dialog.events import DialogClosedEvent, DialogOpenedEvent


class TestDialogClosedEvent(unittest.TestCase):
    """Test DialogClosedEvent."""

    def test_init(self) -> None:
        """Test DialogClosedEvent initialization."""
        event = DialogClosedEvent(npc_name="merchant", dialog_level=2)

        assert event.npc_name == "merchant"
        assert event.dialog_level == 2

    def test_get_script_data(self) -> None:
        """Test get_script_data returns correct dictionary."""
        event = DialogClosedEvent(npc_name="guard", dialog_level=3)

        data = event.get_script_data()

        assert data == {"npc": "guard", "dialog_level": 3}

    def test_get_script_data_with_different_values(self) -> None:
        """Test get_script_data with different values."""
        event = DialogClosedEvent(npc_name="elder", dialog_level=0)

        data = event.get_script_data()

        assert data == {"npc": "elder", "dialog_level": 0}


class TestDialogOpenedEvent(unittest.TestCase):
    """Test DialogOpenedEvent."""

    def test_init(self) -> None:
        """Test DialogOpenedEvent initialization."""
        event = DialogOpenedEvent(npc_name="shopkeeper", dialog_level=1)

        assert event.npc_name == "shopkeeper"
        assert event.dialog_level == 1

    def test_get_script_data(self) -> None:
        """Test get_script_data returns correct dictionary."""
        event = DialogOpenedEvent(npc_name="wizard", dialog_level=5)

        data = event.get_script_data()

        assert data == {"npc": "wizard", "dialog_level": 5}

    def test_get_script_data_with_different_values(self) -> None:
        """Test get_script_data with different values."""
        event = DialogOpenedEvent(npc_name="hero", dialog_level=0)

        data = event.get_script_data()

        assert data == {"npc": "hero", "dialog_level": 0}


if __name__ == "__main__":
    unittest.main()
