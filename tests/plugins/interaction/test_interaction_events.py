"""Unit tests for interaction events in src/pedre/plugins/interaction/events.py."""

from pedre.plugins.interaction.events import ObjectInteractedEvent


class TestObjectInteractedEvent:
    """Test suite for ObjectInteractedEvent."""

    def test_initialization(self) -> None:
        """Test event initialization with attributes."""
        event = ObjectInteractedEvent(object_name="treasure_chest")

        assert event.object_name == "treasure_chest"

    def test_initialization_different_objects(self) -> None:
        """Test event initialization with different object names."""
        event1 = ObjectInteractedEvent(object_name="door")
        event2 = ObjectInteractedEvent(object_name="lever")
        event3 = ObjectInteractedEvent(object_name="sign_01")

        assert event1.object_name == "door"
        assert event2.object_name == "lever"
        assert event3.object_name == "sign_01"

    def test_get_script_data(self) -> None:
        """Test get_script_data returns correct data."""
        event = ObjectInteractedEvent(object_name="switch")

        script_data = event.get_script_data()

        assert "object_name" in script_data
        assert script_data["object_name"] == "switch"

    def test_get_script_data_different_objects(self) -> None:
        """Test get_script_data with different object names."""
        objects = ["chest_1", "lever_a", "button_red", "door_main"]

        for obj_name in objects:
            event = ObjectInteractedEvent(object_name=obj_name)
            script_data = event.get_script_data()
            assert script_data["object_name"] == obj_name

    def test_get_script_data_returns_dict(self) -> None:
        """Test that get_script_data returns a dictionary."""
        event = ObjectInteractedEvent(object_name="test_object")

        script_data = event.get_script_data()

        assert isinstance(script_data, dict)
        assert len(script_data) == 1

    def test_event_is_dataclass(self) -> None:
        """Test that ObjectInteractedEvent is properly defined as a dataclass."""
        assert hasattr(ObjectInteractedEvent, "__dataclass_fields__")

    def test_object_name_with_special_characters(self) -> None:
        """Test event with object names containing special characters."""
        special_names = ["door_2", "lever-left", "switch.main", "sign_01_test"]

        for name in special_names:
            event = ObjectInteractedEvent(object_name=name)
            assert event.object_name == name
            assert event.get_script_data()["object_name"] == name

    def test_object_name_empty_string(self) -> None:
        """Test event with empty string object name."""
        event = ObjectInteractedEvent(object_name="")

        assert event.object_name == ""
        assert event.get_script_data()["object_name"] == ""

    def test_multiple_events_independence(self) -> None:
        """Test that multiple event instances are independent."""
        event1 = ObjectInteractedEvent(object_name="object1")
        event2 = ObjectInteractedEvent(object_name="object2")

        # Changing one should not affect the other
        assert event1.object_name == "object1"
        assert event2.object_name == "object2"
        assert event1.get_script_data()["object_name"] != event2.get_script_data()["object_name"]
