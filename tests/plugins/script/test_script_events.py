"""Unit tests for script events in src/pedre/plugins/script/events.py."""

import unittest

from pedre.plugins.script.events import ScriptCompleteEvent


class TestScriptCompleteEvent(unittest.TestCase):
    """Test suite for ScriptCompleteEvent."""

    def test_initialization(self) -> None:
        """Test event initialization with script_name attribute."""
        event = ScriptCompleteEvent(script_name="intro_cutscene")

        assert event.script_name == "intro_cutscene"

    def test_initialization_different_scripts(self) -> None:
        """Test event initialization with different script names."""
        event1 = ScriptCompleteEvent(script_name="quest_start")
        event2 = ScriptCompleteEvent(script_name="dialog_complete")
        event3 = ScriptCompleteEvent(script_name="cutscene_01")

        assert event1.script_name == "quest_start"
        assert event2.script_name == "dialog_complete"
        assert event3.script_name == "cutscene_01"

    def test_get_script_data(self) -> None:
        """Test get_script_data returns correct data."""
        event = ScriptCompleteEvent(script_name="test_script")

        script_data = event.get_script_data()

        assert "script" in script_data
        assert script_data["script"] == "test_script"

    def test_get_script_data_different_scripts(self) -> None:
        """Test get_script_data with different script names."""
        scripts = ["intro", "quest_1", "boss_fight", "ending_cutscene"]

        for script_name in scripts:
            event = ScriptCompleteEvent(script_name=script_name)
            script_data = event.get_script_data()
            assert script_data["script"] == script_name

    def test_get_script_data_returns_dict(self) -> None:
        """Test that get_script_data returns a dictionary."""
        event = ScriptCompleteEvent(script_name="my_script")

        script_data = event.get_script_data()

        assert isinstance(script_data, dict)
        assert len(script_data) == 1

    def test_event_is_dataclass(self) -> None:
        """Test that ScriptCompleteEvent is properly defined as a dataclass."""
        assert hasattr(ScriptCompleteEvent, "__dataclass_fields__")

    def test_script_name_with_underscores(self) -> None:
        """Test event with script names containing underscores."""
        names = ["script_1", "quest_start_01", "cutscene_intro_test"]

        for name in names:
            event = ScriptCompleteEvent(script_name=name)
            assert event.script_name == name
            assert event.get_script_data()["script"] == name

    def test_script_name_empty_string(self) -> None:
        """Test event with empty string script name."""
        event = ScriptCompleteEvent(script_name="")

        assert event.script_name == ""
        assert event.get_script_data()["script"] == ""

    def test_multiple_events_independence(self) -> None:
        """Test that multiple event instances are independent."""
        event1 = ScriptCompleteEvent(script_name="script1")
        event2 = ScriptCompleteEvent(script_name="script2")

        # Changing one should not affect the other
        assert event1.script_name == "script1"
        assert event2.script_name == "script2"
        assert event1.get_script_data()["script"] != event2.get_script_data()["script"]


if __name__ == "__main__":
    unittest.main()
