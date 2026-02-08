"""Unit tests for PortalPlugin in src/pedre/plugins/portal/plugin.py."""

import unittest
from unittest.mock import MagicMock, patch

from pedre.plugins.portal.events import PortalEnteredEvent
from pedre.plugins.portal.plugin import PortalPlugin


class TestPortalPlugin(unittest.TestCase):
    """Test Suite for PortalPlugin."""

    def setUp(self) -> None:
        """Set up the PortalPlugin and mock context."""
        self.plugin = PortalPlugin()
        self.mock_context = MagicMock()
        self.mock_event_bus = MagicMock()
        self.mock_player_plugin = MagicMock()

        self.mock_context.event_bus = self.mock_event_bus
        self.mock_context.player_plugin = self.mock_player_plugin

        self.plugin.setup(self.mock_context)

    def test_initialization(self) -> None:
        """Test proper initialization of the plugin."""
        plugin = PortalPlugin()
        assert plugin.name == "portal"
        assert plugin.dependencies == []
        assert plugin.portals == []
        assert plugin.interaction_distance > 0
        assert plugin._portals_player_inside == set()

    def test_setup(self) -> None:
        """Test setup configures context."""
        plugin = PortalPlugin()
        plugin.setup(self.mock_context)
        assert plugin.context == self.mock_context

    def test_register_portal(self) -> None:
        """Test registering a portal."""
        mock_sprite = MagicMock()

        self.plugin.register_portal(mock_sprite, "test_portal")

        assert len(self.plugin.portals) == 1
        assert self.plugin.portals[0].name == "test_portal"
        assert self.plugin.portals[0].sprite == mock_sprite

    @patch("pedre.plugins.portal.plugin.arcade.Sprite")
    def test_load_from_tiled_basic(self, mock_sprite_cls: MagicMock) -> None:
        """Test loading portals from Tiled map."""
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()

        # Mock portal object with point shape
        mock_portal = MagicMock()
        mock_portal.name = "entrance"
        mock_portal.properties = {"some_prop": "value"}
        mock_portal.shape = [100.0, 200.0]

        mock_tile_map.object_lists.get.return_value = [mock_portal]

        # Mock sprite creation
        mock_sprite = MagicMock()
        mock_sprite_cls.return_value = mock_sprite

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Verify portal registered
        assert len(self.plugin.portals) == 1
        assert self.plugin.portals[0].name == "entrance"

        # Verify sprite configured
        assert mock_sprite.center_x == 100.0
        assert mock_sprite.center_y == 200.0

    @patch("pedre.plugins.portal.plugin.arcade.Sprite")
    def test_load_from_tiled_polygon_shape(self, mock_sprite_cls: MagicMock) -> None:
        """Test loading portal with polygon shape."""
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()

        # Mock portal object with polygon shape
        mock_portal = MagicMock()
        mock_portal.name = "gate"
        mock_portal.properties = {"some_prop": "value"}
        mock_portal.shape = [(50.0, 100.0), (150.0, 100.0), (150.0, 200.0), (50.0, 200.0)]

        mock_tile_map.object_lists.get.return_value = [mock_portal]

        # Mock sprite creation
        mock_sprite = MagicMock()
        mock_sprite_cls.return_value = mock_sprite

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Verify portal registered
        assert len(self.plugin.portals) == 1

        # Verify sprite configured with bounding box
        # Center should be at (100, 150) - midpoint of (50-150, 100-200)
        assert mock_sprite.center_x == 100.0
        assert mock_sprite.center_y == 150.0
        assert mock_sprite.width == 100.0  # 150 - 50
        assert mock_sprite.height == 100.0  # 200 - 100

    def test_load_from_tiled_no_layer(self) -> None:
        """Test loading when no Portals layer exists."""
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_tile_map.object_lists.get.return_value = None

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert len(self.plugin.portals) == 0

    def test_load_from_tiled_invalid_portal(self) -> None:
        """Test loading skips portals with missing data."""
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()

        # Mock portal without name
        mock_portal = MagicMock()
        mock_portal.name = None
        mock_portal.properties = {}
        mock_portal.shape = [100.0, 200.0]

        mock_tile_map.object_lists.get.return_value = [mock_portal]

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Should skip invalid portal
        assert len(self.plugin.portals) == 0

    @patch("pedre.plugins.portal.plugin.logger")
    def test_load_from_tiled_shape_wrong_type(self, mock_logger: MagicMock) -> None:
        """Test loading skips portals with shape that is wrong type (not list/tuple)."""
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()

        # Mock portal with shape as string (truthy but wrong type)
        mock_portal = MagicMock()
        mock_portal.name = "broken_portal"
        mock_portal.properties = {"some": "prop"}
        mock_portal.shape = "invalid"  # Truthy but not list/tuple

        mock_tile_map.object_lists.get.return_value = [mock_portal]

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Should skip portal with invalid shape type
        assert len(self.plugin.portals) == 0
        # Should log warning about invalid shape
        assert mock_logger.warning.call_count == 1
        assert "invalid shape" in str(mock_logger.warning.call_args)

    @patch("pedre.plugins.portal.plugin.arcade.Sprite")
    def test_load_from_tiled_polygon_with_invalid_point(self, mock_sprite_cls: MagicMock) -> None:
        """Test loading polygon portal with invalid point in shape."""
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()

        # Mock portal with polygon shape containing invalid point (too short)
        mock_portal = MagicMock()
        mock_portal.name = "gate"
        mock_portal.properties = {"some_prop": "value"}
        # First point is valid tuple, second is too short (should be skipped)
        mock_portal.shape = [(50.0, 100.0), (150.0,), (150.0, 200.0), (50.0, 200.0)]

        mock_tile_map.object_lists.get.return_value = [mock_portal]

        # Mock sprite creation
        mock_sprite = MagicMock()
        mock_sprite_cls.return_value = mock_sprite

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Portal should still be registered (valid points are used)
        assert len(self.plugin.portals) == 1

    def test_check_portals_no_player(self) -> None:
        """Test check_portals handles missing player."""
        self.plugin.check_portals(None)
        # Should not crash

    def test_check_portals_player_enters_portal(self) -> None:
        """Test event published when player enters portal."""
        # Create portal
        mock_portal_sprite = MagicMock()
        mock_portal_sprite.center_x = 100.0
        mock_portal_sprite.center_y = 100.0
        self.plugin.register_portal(mock_portal_sprite, "test_portal")

        # Create player near portal
        mock_player = MagicMock()
        mock_player.center_x = 105.0
        mock_player.center_y = 105.0

        self.plugin.check_portals(mock_player)

        # Verify event published
        self.mock_event_bus.publish.assert_called_once()
        event = self.mock_event_bus.publish.call_args[0][0]
        assert isinstance(event, PortalEnteredEvent)
        assert event.portal_name == "test_portal"

    def test_check_portals_player_stays_in_portal(self) -> None:
        """Test event not re-published when player stays in portal."""
        # Create portal
        mock_portal_sprite = MagicMock()
        mock_portal_sprite.center_x = 100.0
        mock_portal_sprite.center_y = 100.0
        self.plugin.register_portal(mock_portal_sprite, "test_portal")

        # Create player near portal
        mock_player = MagicMock()
        mock_player.center_x = 105.0
        mock_player.center_y = 105.0

        # First check - should publish
        self.plugin.check_portals(mock_player)
        assert self.mock_event_bus.publish.call_count == 1

        # Second check - should not publish again
        self.plugin.check_portals(mock_player)
        assert self.mock_event_bus.publish.call_count == 1

    def test_check_portals_player_exits_and_reenters(self) -> None:
        """Test event published again when player exits and re-enters."""
        # Create portal
        mock_portal_sprite = MagicMock()
        mock_portal_sprite.center_x = 100.0
        mock_portal_sprite.center_y = 100.0
        self.plugin.register_portal(mock_portal_sprite, "test_portal")

        # Create player
        mock_player = MagicMock()

        # Enter portal
        mock_player.center_x = 105.0
        mock_player.center_y = 105.0
        self.plugin.check_portals(mock_player)
        assert self.mock_event_bus.publish.call_count == 1

        # Exit portal (move far away)
        mock_player.center_x = 500.0
        mock_player.center_y = 500.0
        self.plugin.check_portals(mock_player)
        assert self.mock_event_bus.publish.call_count == 1

        # Re-enter portal
        mock_player.center_x = 105.0
        mock_player.center_y = 105.0
        self.plugin.check_portals(mock_player)
        assert self.mock_event_bus.publish.call_count == 2

    def test_check_portals_player_too_far(self) -> None:
        """Test no event when player is too far from portal."""
        # Create portal
        mock_portal_sprite = MagicMock()
        mock_portal_sprite.center_x = 100.0
        mock_portal_sprite.center_y = 100.0
        self.plugin.register_portal(mock_portal_sprite, "test_portal")

        # Create player far from portal
        mock_player = MagicMock()
        mock_player.center_x = 500.0
        mock_player.center_y = 500.0

        self.plugin.check_portals(mock_player)

        # Verify no event published
        self.mock_event_bus.publish.assert_not_called()

    def test_clear(self) -> None:
        """Test clearing portals."""
        # Add some portals
        mock_sprite = MagicMock()
        self.plugin.register_portal(mock_sprite, "portal1")
        self.plugin.register_portal(mock_sprite, "portal2")
        self.plugin._portals_player_inside.add("portal1")

        self.plugin.clear()

        assert len(self.plugin.portals) == 0
        assert len(self.plugin._portals_player_inside) == 0

    def test_cleanup(self) -> None:
        """Test cleanup clears portals."""
        # Add some portals
        mock_sprite = MagicMock()
        self.plugin.register_portal(mock_sprite, "portal1")

        self.plugin.cleanup()

        assert len(self.plugin.portals) == 0

    def test_update(self) -> None:
        """Test update calls check_portals."""
        mock_player = MagicMock()
        self.mock_player_plugin.get_player_sprite.return_value = mock_player

        with patch.object(self.plugin, "check_portals") as mock_check:
            self.plugin.update(1.0)
            mock_check.assert_called_once_with(mock_player)


if __name__ == "__main__":
    unittest.main()
