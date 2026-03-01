"""Unit tests for PlayerPlugin in src/pedre/plugins/player/plugin.py."""

from unittest.mock import MagicMock, patch

from pedre.plugins.player.plugin import PlayerPlugin


def _make_plugin() -> tuple[PlayerPlugin, MagicMock]:
    """Create a fresh PlayerPlugin with a mock context, already set up."""
    plugin = PlayerPlugin()
    context = MagicMock()
    plugin.setup(context)
    return plugin, context


class TestPlayerPlugin:
    """Test Suite for PlayerPlugin."""

    def test_initialization(self) -> None:
        """Test proper initialization of the plugin."""
        plugin = PlayerPlugin()
        assert plugin.name == "player"
        assert "input" in plugin.dependencies
        assert "waypoint" in plugin.dependencies
        assert plugin.player_sprite is None
        assert plugin.player_list is None

    def test_get_player_sprite(self) -> None:
        """Test getting player sprite."""
        plugin, _ = _make_plugin()
        assert plugin.get_player_sprite() is None

        mock_sprite = MagicMock()
        plugin.player_sprite = mock_sprite
        assert plugin.get_player_sprite() == mock_sprite

    @patch("pedre.plugins.player.plugin.create_sprite_from_definition")
    @patch("pedre.plugins.player.plugin.arcade.SpriteList")
    @patch("pedre.plugins.player.plugin.asset_path")
    def test_load_from_tiled_basic(
        self,
        mock_asset_path: MagicMock,
        mock_sprite_list_cls: MagicMock,
        mock_create_sprite: MagicMock,
    ) -> None:
        """Test loading player from Tiled map."""
        plugin, context = _make_plugin()
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_asset_path.return_value = "/path/to/sprite.png"

        # Set up content registry mock
        context.content_registry.sprites.has.return_value = True
        context.content_registry.sprites.get.return_value = {"sprite_sheet": "player.png", "states": {}}

        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {
            "sprite_sheet": "player.png",
            "spawn_at_portal": False,
        }
        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        mock_sprite_list = MagicMock()
        mock_sprite_list_cls.return_value = mock_sprite_list

        mock_sprite = MagicMock()
        mock_create_sprite.return_value = mock_sprite

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        mock_create_sprite.assert_called_once()
        call_kwargs = mock_create_sprite.call_args[1]
        assert call_kwargs["center_x"] == 100.0
        assert call_kwargs["center_y"] == 200.0
        mock_sprite_list.append.assert_called_once_with(mock_sprite)
        mock_arcade_scene.add_sprite_list.assert_called_once()

    @patch("pedre.plugins.player.plugin.create_sprite_from_definition")
    @patch("pedre.plugins.player.plugin.arcade.SpriteList")
    @patch("pedre.plugins.player.plugin.asset_path")
    def test_load_from_tiled_with_waypoint(
        self,
        mock_asset_path: MagicMock,
        mock_sprite_list_cls: MagicMock,
        mock_create_sprite: MagicMock,
    ) -> None:
        """Test loading player with waypoint spawn override."""
        plugin, context = _make_plugin()
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_asset_path.return_value = "/path/to/sprite.png"

        context.content_registry.sprites.has.return_value = True
        context.content_registry.sprites.get.return_value = {"sprite_sheet": "player.png", "states": {}}

        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {
            "sprite_sheet": "player.png",
            "spawn_at_portal": True,
        }
        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        mock_sprite_list_cls.return_value = MagicMock()
        mock_create_sprite.return_value = MagicMock()

        context.scene_plugin.get_next_spawn_waypoint.return_value = "entrance"
        context.waypoint_plugin.get_waypoints.return_value = {
            "entrance": (176.0, 336.0),
        }

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        call_kwargs = mock_create_sprite.call_args[1]
        assert call_kwargs["center_x"] == 176.0
        assert call_kwargs["center_y"] == 336.0
        context.scene_plugin.clear_next_spawn_waypoint.assert_called_once()

    @patch("pedre.plugins.player.plugin.create_sprite_from_definition")
    @patch("pedre.plugins.player.plugin.arcade.SpriteList")
    @patch("pedre.plugins.player.plugin.asset_path")
    def test_load_from_tiled_with_incorrect_waypoint(
        self,
        mock_asset_path: MagicMock,
        mock_sprite_list_cls: MagicMock,
        mock_create_sprite: MagicMock,
    ) -> None:
        """Test loading player with incorrect waypoint."""
        plugin, context = _make_plugin()
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_asset_path.return_value = "/path/to/sprite.png"

        context.content_registry.sprites.has.return_value = True
        context.content_registry.sprites.get.return_value = {"sprite_sheet": "player.png", "states": {}}

        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {
            "sprite_sheet": "player.png",
            "spawn_at_portal": True,
        }
        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        mock_sprite_list_cls.return_value = MagicMock()
        mock_create_sprite.return_value = MagicMock()

        context.scene_plugin.get_next_spawn_waypoint.return_value = "entrance"
        context.waypoint_plugin.get_waypoints.return_value = {
            "entrance2": (176.0, 336.0),
        }

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        call_kwargs = mock_create_sprite.call_args[1]
        assert call_kwargs["center_x"] == 100.0
        assert call_kwargs["center_y"] == 200.0
        context.scene_plugin.clear_next_spawn_waypoint.assert_not_called()

    @patch("pedre.plugins.player.plugin.logger")
    @patch("pedre.plugins.player.plugin.create_sprite_from_definition")
    @patch("pedre.plugins.player.plugin.arcade.SpriteList")
    @patch("pedre.plugins.player.plugin.asset_path")
    def test_load_from_tiled_wrong_tile_size_type(
        self,
        mock_asset_path: MagicMock,
        mock_sprite_list_cls: MagicMock,
        mock_create_sprite: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Test loading player with invalid tile_size type logs a warning."""
        plugin, context = _make_plugin()
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_asset_path.return_value = "/path/to/sprite.png"

        context.content_registry.sprites.has.return_value = True
        context.content_registry.sprites.get.return_value = {"sprite_sheet": "player.png", "states": {}}

        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {"spawn_at_portal": True, "sprite_sheet": "player.png", "tile_size": "12"}
        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        mock_sprite_list_cls.return_value = MagicMock()
        mock_create_sprite.return_value = MagicMock()

        context.scene_plugin.get_next_spawn_waypoint.return_value = "entrance"
        context.waypoint_plugin.get_waypoints.return_value = {
            "entrance": (176.0, 336.0),
        }

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        call_kwargs = mock_create_sprite.call_args[1]
        assert call_kwargs["center_x"] == 176.0
        assert call_kwargs["center_y"] == 336.0
        assert mock_logger.warning.called

    def test_load_from_tiled_no_player_layer(self) -> None:
        """Test loading when no Player layer exists."""
        plugin, _ = _make_plugin()
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_tile_map.object_lists.get.return_value = None

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert plugin.player_sprite is None

    def test_update_no_sprite(self) -> None:
        """Test update when no player sprite exists."""
        plugin, _ = _make_plugin()
        plugin.update(1.0)

    def test_update_with_movement(self) -> None:
        """Test update applies movement from input plugin."""
        plugin, context = _make_plugin()
        mock_sprite = MagicMock()
        mock_sprite.current_direction = "down"
        mock_sprite.__class__.__name__ = "AnimatedPlayer"
        plugin.player_sprite = mock_sprite

        context.input_plugin.get_movement_vector.return_value = (5.0, 0.0)
        context.dialog_plugin.is_showing.return_value = False

        with patch("pedre.plugins.player.plugin.isinstance", return_value=True):
            plugin.update(1.0)

        assert mock_sprite.change_x == 5.0
        assert mock_sprite.change_y == 0.0
        mock_sprite.set_direction.assert_called_with("right")
        mock_sprite.update_animation.assert_called_once()

    def test_update_blocked_by_dialog(self) -> None:
        """Test update blocks movement when dialog is showing."""
        plugin, context = _make_plugin()
        mock_sprite = MagicMock()
        mock_sprite.current_direction = "down"
        plugin.player_sprite = mock_sprite

        context.dialog_plugin.is_showing.return_value = True

        plugin.update(1.0)

        assert mock_sprite.change_x == 0.0
        assert mock_sprite.change_y == 0.0

    def test_save_and_restore_state(self) -> None:
        """Test saving and restoring player state."""
        plugin, _ = _make_plugin()
        mock_sprite = MagicMock()
        mock_sprite.center_x = 123.5
        mock_sprite.center_y = 456.7
        plugin.player_sprite = mock_sprite

        state = plugin.get_save_state()
        assert state["player_x"] == 123.5
        assert state["player_y"] == 456.7

        new_sprite = MagicMock()
        plugin.player_sprite = new_sprite
        plugin.apply_entity_state(state)

        assert new_sprite.center_x == 123.5
        assert new_sprite.center_y == 456.7

    def test_to_dict_no_sprite(self) -> None:
        """Test to_dict returns empty when no sprite."""
        plugin, _ = _make_plugin()
        assert plugin.to_dict() == {}

    def test_from_dict_no_sprite(self) -> None:
        """Test from_dict does nothing when no sprite."""
        plugin, _ = _make_plugin()
        plugin.from_dict({"player_x": 100.0, "player_y": 200.0})

    def test_reset(self) -> None:
        """Test reset clears player state."""
        plugin, _ = _make_plugin()
        plugin.player_sprite = MagicMock()
        plugin.player_list = MagicMock()

        plugin.reset()

        assert plugin.player_sprite is None
        assert plugin.player_list is None

    def test_load_from_tiled_missing_sprite_sheet(self) -> None:
        """Test loading player when sprite_sheet property is missing."""
        plugin, context = _make_plugin()
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()

        # No content registry entry → plugin returns early
        context.content_registry.sprites.has.return_value = False

        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {"spawn_at_portal": False}
        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert plugin.player_sprite is None

    @patch("pedre.plugins.player.plugin.logger")
    @patch("pedre.plugins.player.plugin.create_sprite_from_definition")
    @patch("pedre.plugins.player.plugin.arcade.SpriteList")
    @patch("pedre.plugins.player.plugin.asset_path")
    def test_load_from_tiled_invalid_scale_type(
        self,
        mock_asset_path: MagicMock,
        mock_sprite_list_cls: MagicMock,
        mock_create_sprite: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Test loading player with invalid scale type."""
        plugin, context = _make_plugin()
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_asset_path.return_value = "/path/to/sprite.png"

        context.content_registry.sprites.has.return_value = True
        context.content_registry.sprites.get.return_value = {"sprite_sheet": "player.png", "states": {}}

        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {
            "sprite_sheet": "player.png",
            "spawn_at_portal": False,
            "scale": "invalid_string",
        }
        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        mock_sprite_list_cls.return_value = MagicMock()
        mock_create_sprite.return_value = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert mock_logger.warning.called
        warning_call = mock_logger.warning.call_args[0][0]
        assert "scale" in warning_call
        mock_create_sprite.assert_called_once()
        call_kwargs = mock_create_sprite.call_args[1]
        assert call_kwargs.get("scale") is None

    @patch("pedre.plugins.player.plugin.create_sprite_from_definition")
    @patch("pedre.plugins.player.plugin.arcade.SpriteList")
    @patch("pedre.plugins.player.plugin.asset_path")
    def test_load_from_tiled_with_scale_and_tile_size(
        self,
        mock_asset_path: MagicMock,
        mock_sprite_list_cls: MagicMock,
        mock_create_sprite: MagicMock,
    ) -> None:
        """Test loading player with valid scale and tile_size parameters."""
        plugin, context = _make_plugin()
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_asset_path.return_value = "/path/to/sprite.png"

        context.content_registry.sprites.has.return_value = True
        context.content_registry.sprites.get.return_value = {"sprite_sheet": "player.png", "states": {}}

        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {
            "sprite_sheet": "player.png",
            "spawn_at_portal": False,
            "scale": 2.5,
            "tile_size": 32,
        }
        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        mock_sprite_list_cls.return_value = MagicMock()
        mock_create_sprite.return_value = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        mock_create_sprite.assert_called_once()
        call_kwargs = mock_create_sprite.call_args[1]
        assert call_kwargs["scale"] == 2.5
        assert call_kwargs["tile_size"] == 32

    @patch("pedre.plugins.player.plugin.create_sprite_from_definition")
    @patch("pedre.plugins.player.plugin.arcade.SpriteList")
    @patch("pedre.plugins.player.plugin.asset_path")
    def test_load_from_tiled_replaces_existing_player_in_scene(
        self,
        mock_asset_path: MagicMock,
        mock_sprite_list_cls: MagicMock,
        mock_create_sprite: MagicMock,
    ) -> None:
        """Test loading player removes existing Player sprite list from scene."""
        plugin, context = _make_plugin()
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_arcade_scene.__contains__ = MagicMock(return_value=True)
        mock_asset_path.return_value = "/path/to/sprite.png"

        context.content_registry.sprites.has.return_value = True
        context.content_registry.sprites.get.return_value = {"sprite_sheet": "player.png", "states": {}}

        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {
            "sprite_sheet": "player.png",
            "spawn_at_portal": False,
        }
        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        mock_sprite_list_cls.return_value = MagicMock()
        mock_create_sprite.return_value = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        mock_create_sprite.assert_called_once()
        mock_arcade_scene.remove_sprite_list_by_name.assert_called_once_with("Player")
        mock_arcade_scene.add_sprite_list.assert_called_once()

    def test_update_with_left_movement(self) -> None:
        """Test update applies left movement and updates direction."""
        plugin, context = _make_plugin()
        mock_sprite = MagicMock()
        mock_sprite.current_direction = "down"
        mock_sprite.__class__.__name__ = "AnimatedPlayer"
        plugin.player_sprite = mock_sprite

        context.input_plugin.get_movement_vector.return_value = (-5.0, 0.0)
        context.dialog_plugin.is_showing.return_value = False

        with patch("pedre.plugins.player.plugin.isinstance", return_value=True):
            plugin.update(1.0)

        assert mock_sprite.change_x == -5.0
        assert mock_sprite.change_y == 0.0
        mock_sprite.set_direction.assert_called_with("left")
        mock_sprite.update_animation.assert_called_once()

    def test_update_with_up_movement(self) -> None:
        """Test update applies up movement and updates direction."""
        plugin, context = _make_plugin()
        mock_sprite = MagicMock()
        mock_sprite.current_direction = "down"
        mock_sprite.__class__.__name__ = "AnimatedPlayer"
        plugin.player_sprite = mock_sprite

        context.input_plugin.get_movement_vector.return_value = (0.0, 5.0)
        context.dialog_plugin.is_showing.return_value = False

        with patch("pedre.plugins.player.plugin.isinstance", return_value=True):
            plugin.update(1.0)

        assert mock_sprite.change_x == 0.0
        assert mock_sprite.change_y == 5.0
        mock_sprite.set_direction.assert_called_with("up")
        mock_sprite.update_animation.assert_called_once()

    def test_update_with_down_movement(self) -> None:
        """Test update applies down movement and updates direction."""
        plugin, context = _make_plugin()
        mock_sprite = MagicMock()
        mock_sprite.current_direction = "up"
        mock_sprite.__class__.__name__ = "AnimatedPlayer"
        plugin.player_sprite = mock_sprite

        context.input_plugin.get_movement_vector.return_value = (0.0, -5.0)
        context.dialog_plugin.is_showing.return_value = False

        with patch("pedre.plugins.player.plugin.isinstance", return_value=True):
            plugin.update(1.0)

        assert mock_sprite.change_x == 0.0
        assert mock_sprite.change_y == -5.0
        mock_sprite.set_direction.assert_called_with("down")
        mock_sprite.update_animation.assert_called_once()

    def test_update_no_direction_change(self) -> None:
        """Test update when direction doesn't change."""
        plugin, context = _make_plugin()
        mock_sprite = MagicMock()
        mock_sprite.current_direction = "right"
        mock_sprite.__class__.__name__ = "AnimatedPlayer"
        plugin.player_sprite = mock_sprite

        context.input_plugin.get_movement_vector.return_value = (5.0, 0.0)
        context.dialog_plugin.is_showing.return_value = False

        with patch("pedre.plugins.player.plugin.isinstance", return_value=True):
            plugin.update(1.0)

        assert mock_sprite.change_x == 5.0
        assert mock_sprite.change_y == 0.0
        mock_sprite.set_direction.assert_not_called()
        mock_sprite.update_animation.assert_called_once()

    @patch("pedre.plugins.player.plugin.logger")
    def test_apply_entity_state_with_position(self, mock_logger: MagicMock) -> None:
        """Test apply_entity_state logs when position is applied."""
        plugin, _ = _make_plugin()
        mock_sprite = MagicMock()
        mock_sprite.center_x = 0.0
        mock_sprite.center_y = 0.0
        plugin.player_sprite = mock_sprite

        plugin.apply_entity_state({"player_x": 100.5, "player_y": 200.5})

        assert mock_sprite.center_x == 100.5
        assert mock_sprite.center_y == 200.5
        assert mock_logger.info.called

    def test_from_dict_missing_keys(self) -> None:
        """Test from_dict with missing coordinate keys."""
        plugin, _ = _make_plugin()
        mock_sprite = MagicMock()
        mock_sprite.center_x = 50.0
        mock_sprite.center_y = 50.0
        plugin.player_sprite = mock_sprite

        plugin.from_dict({"player_y": 100.0})
        assert mock_sprite.center_x == 50.0
        assert mock_sprite.center_y == 50.0

        plugin.from_dict({"player_x": 100.0})
        assert mock_sprite.center_x == 50.0
        assert mock_sprite.center_y == 50.0

        plugin.from_dict({})
        assert mock_sprite.center_x == 50.0
        assert mock_sprite.center_y == 50.0

    def test_update_no_movement(self) -> None:
        """Test update when there's no movement (dx=0, dy=0)."""
        plugin, context = _make_plugin()
        mock_sprite = MagicMock()
        mock_sprite.current_direction = "down"
        mock_sprite.__class__.__name__ = "AnimatedPlayer"
        plugin.player_sprite = mock_sprite

        context.input_plugin.get_movement_vector.return_value = (0.0, 0.0)
        context.dialog_plugin.is_showing.return_value = False

        with patch("pedre.plugins.player.plugin.isinstance", return_value=True):
            plugin.update(1.0)

        assert mock_sprite.change_x == 0.0
        assert mock_sprite.change_y == 0.0
        mock_sprite.set_direction.assert_not_called()
        mock_sprite.update_animation.assert_called_once()

    def test_apply_entity_state_no_sprite(self) -> None:
        """Test apply_entity_state when player_sprite is None (branch 213->exit)."""
        plugin, _ = _make_plugin()
        plugin.player_sprite = None

        plugin.apply_entity_state({"player_x": 100.5, "player_y": 200.5})

        assert plugin.player_sprite is None

    def test_apply_entity_state_missing_player_x(self) -> None:
        """Test apply_entity_state when player_x is missing (branch 213->exit)."""
        plugin, _ = _make_plugin()
        mock_sprite = MagicMock()
        mock_sprite.center_x = 50.0
        mock_sprite.center_y = 50.0
        plugin.player_sprite = mock_sprite

        plugin.apply_entity_state({"player_y": 200.5})

        assert mock_sprite.center_x == 50.0
        assert mock_sprite.center_y == 50.0
