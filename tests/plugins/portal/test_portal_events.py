"""Unit tests for portal events."""

from pedre.plugins.portal.events import PortalEnteredEvent


class TestPortalEnteredEvent:
    """Test PortalEnteredEvent."""

    def test_init(self) -> None:
        """Test PortalEnteredEvent initialization."""
        event = PortalEnteredEvent(portal_name="forest_gate")

        assert event.portal_name == "forest_gate"

    def test_get_script_data(self) -> None:
        """Test get_script_data returns correct dictionary."""
        event = PortalEnteredEvent(portal_name="dungeon_entrance")

        data = event.get_script_data()

        assert data == {"portal": "dungeon_entrance"}

    def test_get_script_data_with_different_values(self) -> None:
        """Test get_script_data with different values."""
        event = PortalEnteredEvent(portal_name="town_exit")

        data = event.get_script_data()

        assert data == {"portal": "town_exit"}
