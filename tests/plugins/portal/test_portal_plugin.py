"""Unit tests for PortalPlugin in src/pedre/plugins/portal/plugin.py."""

from unittest.mock import MagicMock, patch

import pytest

from pedre.plugins.portal.events import PortalEnteredEvent
from pedre.plugins.portal.plugin import PortalPlugin

PortalPluginCtx = tuple[PortalPlugin, MagicMock, MagicMock]


@pytest.fixture
def portal_plugin_ctx() -> PortalPluginCtx:
    """Create a fresh PortalPlugin with a mock context, event bus, and player plugin."""
    plugin = PortalPlugin()
    mock_context = MagicMock()
    mock_event_bus = MagicMock()
    mock_player_plugin = MagicMock()

    mock_context.event_bus = mock_event_bus
    mock_context.player_plugin = mock_player_plugin

    plugin.setup(mock_context)
    return plugin, mock_event_bus, mock_player_plugin


class TestPortalPlugin:
    """Test Suite for PortalPlugin."""

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
        mock_context = MagicMock()
        plugin.setup(mock_context)
        assert plugin.context == mock_context

    def test_register_portal(self, portal_plugin_ctx: PortalPluginCtx) -> None:
        """Test registering a portal."""
        plugin, _, _ = portal_plugin_ctx
        mock_sprite = MagicMock()

        plugin.register_portal(mock_sprite, "test_portal")

        assert len(plugin.portals) == 1
        assert plugin.portals[0].name == "test_portal"
        assert plugin.portals[0].sprite == mock_sprite

    @patch("pedre.plugins.portal.plugin.arcade.Sprite")
    def test_load_from_tiled_basic(self, mock_sprite_cls: MagicMock, portal_plugin_ctx: PortalPluginCtx) -> None:
        """Test loading portals from Tiled map."""
        plugin, _, _ = portal_plugin_ctx
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

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Verify portal registered
        assert len(plugin.portals) == 1
        assert plugin.portals[0].name == "entrance"

        # Verify sprite configured
        assert mock_sprite.center_x == 100.0
        assert mock_sprite.center_y == 200.0

    @patch("pedre.plugins.portal.plugin.arcade.Sprite")
    def test_load_from_tiled_polygon_shape(
        self, mock_sprite_cls: MagicMock, portal_plugin_ctx: PortalPluginCtx
    ) -> None:
        """Test loading portal with polygon shape."""
        plugin, _, _ = portal_plugin_ctx
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

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Verify portal registered
        assert len(plugin.portals) == 1

        # Verify sprite configured with bounding box
        # Center should be at (100, 150) - midpoint of (50-150, 100-200)
        assert mock_sprite.center_x == 100.0
        assert mock_sprite.center_y == 150.0
        assert mock_sprite.width == 100.0  # 150 - 50
        assert mock_sprite.height == 100.0  # 200 - 100

    def test_load_from_tiled_no_layer(self, portal_plugin_ctx: PortalPluginCtx) -> None:
        """Test loading when no Portals layer exists."""
        plugin, _, _ = portal_plugin_ctx
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_tile_map.object_lists.get.return_value = None

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert len(plugin.portals) == 0

    def test_load_from_tiled_invalid_portal(self, portal_plugin_ctx: PortalPluginCtx) -> None:
        """Test loading skips portals with missing data."""
        plugin, _, _ = portal_plugin_ctx
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()

        # Mock portal without name
        mock_portal = MagicMock()
        mock_portal.name = None
        mock_portal.properties = {}
        mock_portal.shape = [100.0, 200.0]

        mock_tile_map.object_lists.get.return_value = [mock_portal]

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Should skip invalid portal
        assert len(plugin.portals) == 0

    @patch("pedre.plugins.portal.plugin.logger")
    def test_load_from_tiled_shape_wrong_type(self, mock_logger: MagicMock, portal_plugin_ctx: PortalPluginCtx) -> None:
        """Test loading skips portals with shape that is wrong type (not list/tuple)."""
        plugin, _, _ = portal_plugin_ctx
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()

        # Mock portal with shape as string (truthy but wrong type)
        mock_portal = MagicMock()
        mock_portal.name = "broken_portal"
        mock_portal.properties = {"some": "prop"}
        mock_portal.shape = "invalid"  # Truthy but not list/tuple

        mock_tile_map.object_lists.get.return_value = [mock_portal]

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Should skip portal with invalid shape type
        assert len(plugin.portals) == 0
        # Should log warning about invalid shape
        assert mock_logger.warning.call_count == 1
        assert "invalid shape" in str(mock_logger.warning.call_args)

    @patch("pedre.plugins.portal.plugin.arcade.Sprite")
    def test_load_from_tiled_polygon_with_invalid_point(
        self, mock_sprite_cls: MagicMock, portal_plugin_ctx: PortalPluginCtx
    ) -> None:
        """Test loading polygon portal with invalid point in shape."""
        plugin, _, _ = portal_plugin_ctx
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

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Portal should still be registered (valid points are used)
        assert len(plugin.portals) == 1

    def test_load_from_tiled_flat_shape_invalid_second_elem(self, portal_plugin_ctx: PortalPluginCtx) -> None:
        """Test loading skips portal when flat shape has non-numeric second element."""
        plugin, _, _ = portal_plugin_ctx
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()

        mock_portal = MagicMock()
        mock_portal.name = "bad_portal"
        mock_portal.properties = {}
        # First element is scalar (enters else branch), second is a tuple (triggers guard)
        mock_portal.shape = [100.0, (10.0, 20.0)]

        mock_tile_map.object_lists.get.return_value = [mock_portal]

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert len(plugin.portals) == 0

    def test_check_portals_no_player(self, portal_plugin_ctx: PortalPluginCtx) -> None:
        """Test check_portals handles missing player."""
        plugin, _, _ = portal_plugin_ctx
        plugin.check_portals(None)
        # Should not crash

    def test_check_portals_player_enters_portal(self, portal_plugin_ctx: PortalPluginCtx) -> None:
        """Test event published when player enters portal."""
        plugin, mock_event_bus, _ = portal_plugin_ctx

        # Create portal
        mock_portal_sprite = MagicMock()
        mock_portal_sprite.center_x = 100.0
        mock_portal_sprite.center_y = 100.0
        plugin.register_portal(mock_portal_sprite, "test_portal")

        # Create player near portal
        mock_player = MagicMock()
        mock_player.center_x = 105.0
        mock_player.center_y = 105.0

        plugin.check_portals(mock_player)

        # Verify event published
        mock_event_bus.publish.assert_called_once()
        event = mock_event_bus.publish.call_args[0][0]
        assert isinstance(event, PortalEnteredEvent)
        assert event.portal_name == "test_portal"

    def test_check_portals_player_stays_in_portal(self, portal_plugin_ctx: PortalPluginCtx) -> None:
        """Test event not re-published when player stays in portal."""
        plugin, mock_event_bus, _ = portal_plugin_ctx

        # Create portal
        mock_portal_sprite = MagicMock()
        mock_portal_sprite.center_x = 100.0
        mock_portal_sprite.center_y = 100.0
        plugin.register_portal(mock_portal_sprite, "test_portal")

        # Create player near portal
        mock_player = MagicMock()
        mock_player.center_x = 105.0
        mock_player.center_y = 105.0

        # First check - should publish
        plugin.check_portals(mock_player)
        assert mock_event_bus.publish.call_count == 1

        # Second check - should not publish again
        plugin.check_portals(mock_player)
        assert mock_event_bus.publish.call_count == 1

    def test_check_portals_player_exits_and_reenters(self, portal_plugin_ctx: PortalPluginCtx) -> None:
        """Test event published again when player exits and re-enters."""
        plugin, mock_event_bus, _ = portal_plugin_ctx

        # Create portal
        mock_portal_sprite = MagicMock()
        mock_portal_sprite.center_x = 100.0
        mock_portal_sprite.center_y = 100.0
        plugin.register_portal(mock_portal_sprite, "test_portal")

        # Create player
        mock_player = MagicMock()

        # Enter portal
        mock_player.center_x = 105.0
        mock_player.center_y = 105.0
        plugin.check_portals(mock_player)
        assert mock_event_bus.publish.call_count == 1

        # Exit portal (move far away)
        mock_player.center_x = 500.0
        mock_player.center_y = 500.0
        plugin.check_portals(mock_player)
        assert mock_event_bus.publish.call_count == 1

        # Re-enter portal
        mock_player.center_x = 105.0
        mock_player.center_y = 105.0
        plugin.check_portals(mock_player)
        assert mock_event_bus.publish.call_count == 2

    def test_check_portals_player_too_far(self, portal_plugin_ctx: PortalPluginCtx) -> None:
        """Test no event when player is too far from portal."""
        plugin, mock_event_bus, _ = portal_plugin_ctx

        # Create portal
        mock_portal_sprite = MagicMock()
        mock_portal_sprite.center_x = 100.0
        mock_portal_sprite.center_y = 100.0
        plugin.register_portal(mock_portal_sprite, "test_portal")

        # Create player far from portal
        mock_player = MagicMock()
        mock_player.center_x = 500.0
        mock_player.center_y = 500.0

        plugin.check_portals(mock_player)

        # Verify no event published
        mock_event_bus.publish.assert_not_called()

    def test_clear(self, portal_plugin_ctx: PortalPluginCtx) -> None:
        """Test clearing portals."""
        plugin, _, _ = portal_plugin_ctx

        # Add some portals
        mock_sprite = MagicMock()
        plugin.register_portal(mock_sprite, "portal1")
        plugin.register_portal(mock_sprite, "portal2")
        plugin._portals_player_inside.add("portal1")

        plugin.clear()

        assert len(plugin.portals) == 0
        assert len(plugin._portals_player_inside) == 0

    def test_cleanup(self, portal_plugin_ctx: PortalPluginCtx) -> None:
        """Test cleanup clears portals."""
        plugin, _, _ = portal_plugin_ctx

        # Add some portals
        mock_sprite = MagicMock()
        plugin.register_portal(mock_sprite, "portal1")

        plugin.cleanup()

        assert len(plugin.portals) == 0

    def test_update(self, portal_plugin_ctx: PortalPluginCtx) -> None:
        """Test update calls check_portals."""
        plugin, _, mock_player_plugin = portal_plugin_ctx
        mock_player = MagicMock()
        mock_player_plugin.get_player_sprite.return_value = mock_player

        with patch.object(plugin, "check_portals") as mock_check:
            plugin.update(1.0)
            mock_check.assert_called_once_with(mock_player)
