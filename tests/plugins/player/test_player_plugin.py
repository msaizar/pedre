"""Unit tests for PlayerPlugin in src/pedre/plugins/player/plugin.py."""

import unittest
from unittest.mock import MagicMock, patch

from pedre.plugins.player.plugin import PlayerPlugin


class TestPlayerPlugin(unittest.TestCase):
    """Test Suite for PlayerPlugin."""

    def setUp(self) -> None:
        """Set up the PlayerPlugin and mock context."""
        self.plugin = PlayerPlugin()
        self.mock_context = MagicMock()

        # Mock dependent plugins
        self.mock_input_plugin = MagicMock()
        self.mock_dialog_plugin = MagicMock()
        self.mock_waypoint_plugin = MagicMock()
        self.mock_scene_plugin = MagicMock()

        self.mock_context.input_plugin = self.mock_input_plugin
        self.mock_context.dialog_plugin = self.mock_dialog_plugin
        self.mock_context.waypoint_plugin = self.mock_waypoint_plugin
        self.mock_context.scene_plugin = self.mock_scene_plugin

        self.plugin.setup(self.mock_context)

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
        assert self.plugin.get_player_sprite() is None

        mock_sprite = MagicMock()
        self.plugin.player_sprite = mock_sprite
        assert self.plugin.get_player_sprite() == mock_sprite

    @patch("pedre.plugins.player.plugin.AnimatedPlayer")
    @patch("pedre.plugins.player.plugin.arcade.SpriteList")
    @patch("pedre.plugins.player.plugin.asset_path")
    def test_load_from_tiled_basic(
        self,
        mock_asset_path: MagicMock,
        mock_sprite_list_cls: MagicMock,
        mock_player_cls: MagicMock,
    ) -> None:
        """Test loading player from Tiled map."""
        # Setup mocks
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_asset_path.return_value = "/path/to/sprite.png"

        # Mock player object
        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {
            "sprite_sheet": "player.png",
            "spawn_at_portal": False,
        }

        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        # Mock sprite list
        mock_sprite_list = MagicMock()
        mock_sprite_list_cls.return_value = mock_sprite_list

        # Mock player sprite
        mock_sprite = MagicMock()
        mock_player_cls.return_value = mock_sprite

        # Load player
        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Verify sprite created
        mock_player_cls.assert_called_once()
        call_kwargs = mock_player_cls.call_args[1]
        assert call_kwargs["center_x"] == 100.0
        assert call_kwargs["center_y"] == 200.0

        # Verify added to sprite list
        mock_sprite_list.append.assert_called_once_with(mock_sprite)

        # Verify added to scene
        mock_arcade_scene.add_sprite_list.assert_called_once()

    @patch("pedre.plugins.player.plugin.AnimatedPlayer")
    @patch("pedre.plugins.player.plugin.arcade.SpriteList")
    @patch("pedre.plugins.player.plugin.asset_path")
    def test_load_from_tiled_with_waypoint(
        self,
        mock_asset_path: MagicMock,
        mock_sprite_list_cls: MagicMock,
        mock_player_cls: MagicMock,
    ) -> None:
        """Test loading player with waypoint spawn override."""
        # Setup mocks
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_asset_path.return_value = "/path/to/sprite.png"

        # Mock player object
        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {
            "sprite_sheet": "player.png",
            "spawn_at_portal": True,
        }

        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        # Mock sprite list
        mock_sprite_list = MagicMock()
        mock_sprite_list_cls.return_value = mock_sprite_list

        # Mock waypoint spawn - waypoints now return pixel coordinates
        self.mock_scene_plugin.get_next_spawn_waypoint.return_value = "entrance"
        self.mock_waypoint_plugin.get_waypoints.return_value = {
            "entrance": (176.0, 336.0),  # Pixel coordinates (previously tile 5,10)
        }

        # Load player
        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Verify spawned at waypoint (pixel coordinates)
        call_kwargs = mock_player_cls.call_args[1]
        assert call_kwargs["center_x"] == 176.0
        assert call_kwargs["center_y"] == 336.0

        # Verify waypoint cleared
        self.mock_scene_plugin.clear_next_spawn_waypoint.assert_called_once()

    @patch("pedre.plugins.player.plugin.AnimatedPlayer")
    @patch("pedre.plugins.player.plugin.arcade.SpriteList")
    @patch("pedre.plugins.player.plugin.asset_path")
    def test_load_from_tiled_with_incorrect_waypoint(
        self,
        mock_asset_path: MagicMock,
        mock_sprite_list_cls: MagicMock,
        mock_player_cls: MagicMock,
    ) -> None:
        """Test loading player with incorrect waypoint."""
        # Setup mocks
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_asset_path.return_value = "/path/to/sprite.png"

        # Mock player object
        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {
            "sprite_sheet": "player.png",
            "spawn_at_portal": True,
        }

        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        # Mock sprite list
        mock_sprite_list = MagicMock()
        mock_sprite_list_cls.return_value = mock_sprite_list

        # Mock waypoint spawn - waypoints now return pixel coordinates
        self.mock_scene_plugin.get_next_spawn_waypoint.return_value = "entrance"
        self.mock_waypoint_plugin.get_waypoints.return_value = {
            "entrance2": (176.0, 336.0),  # Pixel coordinates (previously tile 5,10)
        }

        # Load player
        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        call_kwargs = mock_player_cls.call_args[1]
        assert call_kwargs["center_x"] == 100.0
        assert call_kwargs["center_y"] == 200.0

        # Verify waypoint cleared
        self.mock_scene_plugin.clear_next_spawn_waypoint.assert_not_called()

    @patch("pedre.plugins.player.plugin.logger")
    @patch("pedre.plugins.player.plugin.AnimatedPlayer")
    @patch("pedre.plugins.player.plugin.arcade.SpriteList")
    @patch("pedre.plugins.player.plugin.asset_path")
    def test_load_from_tiled_wrong_tile_size_type(
        self,
        mock_asset_path: MagicMock,
        mock_sprite_list_cls: MagicMock,
        mock_player_cls: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Test loading player with waypoint spawn override."""
        # Setup mocks
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_asset_path.return_value = "/path/to/sprite.png"

        # Mock player object
        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {"spawn_at_portal": True, "sprite_sheet": "player.png", "tile_size": "12"}

        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        # Mock sprite list
        mock_sprite_list = MagicMock()
        mock_sprite_list_cls.return_value = mock_sprite_list

        # Mock waypoint spawn - waypoints now return pixel coordinates
        self.mock_scene_plugin.get_next_spawn_waypoint.return_value = "entrance"
        self.mock_waypoint_plugin.get_waypoints.return_value = {
            "entrance": (176.0, 336.0),  # Pixel coordinates (previously tile 5,10)
        }

        # Load player
        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)
        call_kwargs = mock_player_cls.call_args[1]
        assert call_kwargs["center_x"] == 176.0
        assert call_kwargs["center_y"] == 336.0
        assert mock_logger.warning.called

    def test_load_from_tiled_no_player_layer(self) -> None:
        """Test loading when no Player layer exists."""
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_tile_map.object_lists.get.return_value = None

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        assert self.plugin.player_sprite is None

    def test_update_no_sprite(self) -> None:
        """Test update when no player sprite exists."""
        self.plugin.update(1.0)
        # Should not crash

    def test_update_with_movement(self) -> None:
        """Test update applies movement from input plugin."""
        mock_sprite = MagicMock()
        mock_sprite.current_direction = "down"
        mock_sprite.__class__.__name__ = "AnimatedPlayer"
        self.plugin.player_sprite = mock_sprite

        # Mock input
        self.mock_input_plugin.get_movement_vector.return_value = (5.0, 0.0)
        self.mock_dialog_plugin.is_showing.return_value = False

        # Patch isinstance to return True for AnimatedPlayer check
        with patch("pedre.plugins.player.plugin.isinstance", return_value=True):
            self.plugin.update(1.0)

        # Verify movement applied
        assert mock_sprite.change_x == 5.0
        assert mock_sprite.change_y == 0.0

        # Verify direction changed to right
        mock_sprite.set_direction.assert_called_with("right")
        mock_sprite.update_animation.assert_called_once()

    def test_update_blocked_by_dialog(self) -> None:
        """Test update blocks movement when dialog is showing."""
        mock_sprite = MagicMock()
        mock_sprite.current_direction = "down"
        self.plugin.player_sprite = mock_sprite

        # Mock dialog showing
        self.mock_dialog_plugin.is_showing.return_value = True

        self.plugin.update(1.0)

        # Verify no movement
        assert mock_sprite.change_x == 0.0
        assert mock_sprite.change_y == 0.0

    def test_save_and_restore_state(self) -> None:
        """Test saving and restoring player state."""
        mock_sprite = MagicMock()
        mock_sprite.center_x = 123.5
        mock_sprite.center_y = 456.7
        self.plugin.player_sprite = mock_sprite

        # Get save state
        state = self.plugin.get_save_state()
        assert state["player_x"] == 123.5
        assert state["player_y"] == 456.7

        # Restore state
        new_sprite = MagicMock()
        self.plugin.player_sprite = new_sprite
        self.plugin.apply_entity_state(state)

        assert new_sprite.center_x == 123.5
        assert new_sprite.center_y == 456.7

    def test_to_dict_no_sprite(self) -> None:
        """Test to_dict returns empty when no sprite."""
        assert self.plugin.to_dict() == {}

    def test_from_dict_no_sprite(self) -> None:
        """Test from_dict does nothing when no sprite."""
        self.plugin.from_dict({"player_x": 100.0, "player_y": 200.0})
        # Should not crash

    def test_reset(self) -> None:
        """Test reset clears player state."""
        self.plugin.player_sprite = MagicMock()
        self.plugin.player_list = MagicMock()

        self.plugin.reset()

        assert self.plugin.player_sprite is None
        assert self.plugin.player_list is None

    def test_get_animation_properties(self) -> None:
        """Test extracting animation properties."""
        properties = {
            "idle_down_frames": 4,
            "idle_down_row": 0,
            "walk_right_frames": 4,
            "walk_right_row": 2,
            "invalid_prop": "not_an_int",
            "non_anim_prop": 999,
        }

        result = self.plugin._get_animation_properties(properties)

        # Should include valid animation properties
        assert "idle_down_frames" in result
        assert result["idle_down_frames"] == 4
        assert "walk_right_frames" in result

        # Should exclude invalid types
        assert "invalid_prop" not in result

        # Should exclude non-animation properties
        assert "non_anim_prop" not in result

    def test_get_animation_properties_empty(self) -> None:
        """Test extracting animation properties from empty dict."""
        result = self.plugin._get_animation_properties({})
        assert result == {}

    def test_load_from_tiled_missing_sprite_sheet(self) -> None:
        """Test loading player when sprite_sheet property is missing."""
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()

        # Mock player object without sprite_sheet
        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {"spawn_at_portal": False}

        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Should not create sprite
        assert self.plugin.player_sprite is None

    @patch("pedre.plugins.player.plugin.logger")
    @patch("pedre.plugins.player.plugin.AnimatedPlayer")
    @patch("pedre.plugins.player.plugin.arcade.SpriteList")
    @patch("pedre.plugins.player.plugin.asset_path")
    def test_load_from_tiled_invalid_scale_type(
        self,
        mock_asset_path: MagicMock,
        mock_sprite_list_cls: MagicMock,
        mock_player_cls: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Test loading player with invalid scale type."""
        # Setup mocks
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_asset_path.return_value = "/path/to/sprite.png"

        # Mock player object with invalid scale
        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {
            "sprite_sheet": "player.png",
            "spawn_at_portal": False,
            "scale": "invalid_string",  # Should be int or float
        }

        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        # Mock sprite list
        mock_sprite_list = MagicMock()
        mock_sprite_list_cls.return_value = mock_sprite_list

        # Load player
        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Verify warning was logged
        assert mock_logger.warning.called
        warning_call = mock_logger.warning.call_args[0][0]
        assert "scale" in warning_call

        # Verify sprite was still created (without scale param)
        mock_player_cls.assert_called_once()
        call_kwargs = mock_player_cls.call_args[1]
        assert "scale" not in call_kwargs

    @patch("pedre.plugins.player.plugin.AnimatedPlayer")
    @patch("pedre.plugins.player.plugin.arcade.SpriteList")
    @patch("pedre.plugins.player.plugin.asset_path")
    def test_load_from_tiled_with_scale_and_tile_size(
        self,
        mock_asset_path: MagicMock,
        mock_sprite_list_cls: MagicMock,
        mock_player_cls: MagicMock,
    ) -> None:
        """Test loading player with valid scale and tile_size parameters."""
        # Setup mocks
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_asset_path.return_value = "/path/to/sprite.png"

        # Mock player object with scale and tile_size
        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {
            "sprite_sheet": "player.png",
            "spawn_at_portal": False,
            "scale": 2.5,
            "tile_size": 32,
        }

        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        # Mock sprite list
        mock_sprite_list = MagicMock()
        mock_sprite_list_cls.return_value = mock_sprite_list

        # Load player
        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Verify sprite created with scale and tile_size
        mock_player_cls.assert_called_once()
        call_kwargs = mock_player_cls.call_args[1]
        assert call_kwargs["scale"] == 2.5
        assert call_kwargs["tile_size"] == 32

    @patch("pedre.plugins.player.plugin.AnimatedPlayer")
    @patch("pedre.plugins.player.plugin.arcade.SpriteList")
    @patch("pedre.plugins.player.plugin.asset_path")
    def test_load_from_tiled_replaces_existing_player_in_scene(
        self,
        mock_asset_path: MagicMock,
        mock_sprite_list_cls: MagicMock,
        mock_player_cls: MagicMock,
    ) -> None:
        """Test loading player removes existing Player sprite list from scene."""
        # Setup mocks
        mock_tile_map = MagicMock()
        mock_arcade_scene = MagicMock()
        mock_arcade_scene.__contains__ = MagicMock(return_value=True)  # "Player" exists
        mock_asset_path.return_value = "/path/to/sprite.png"

        # Mock player object
        mock_player_obj = MagicMock()
        mock_player_obj.shape = [100.0, 200.0]
        mock_player_obj.properties = {
            "sprite_sheet": "player.png",
            "spawn_at_portal": False,
        }

        mock_tile_map.object_lists.get.return_value = [mock_player_obj]

        # Mock sprite list
        mock_sprite_list = MagicMock()
        mock_sprite_list_cls.return_value = mock_sprite_list

        # Mock player sprite
        mock_sprite = MagicMock()
        mock_player_cls.return_value = mock_sprite

        # Load player
        self.plugin.load_from_tiled(mock_tile_map, mock_arcade_scene)

        # Verify sprite was created
        mock_player_cls.assert_called_once()

        # Verify existing sprite list was removed
        mock_arcade_scene.remove_sprite_list_by_name.assert_called_once_with("Player")

        # Verify new sprite list was added
        mock_arcade_scene.add_sprite_list.assert_called_once()

    def test_update_with_left_movement(self) -> None:
        """Test update applies left movement and updates direction."""
        mock_sprite = MagicMock()
        mock_sprite.current_direction = "down"
        mock_sprite.__class__.__name__ = "AnimatedPlayer"
        self.plugin.player_sprite = mock_sprite

        # Mock input for left movement
        self.mock_input_plugin.get_movement_vector.return_value = (-5.0, 0.0)
        self.mock_dialog_plugin.is_showing.return_value = False

        # Patch isinstance to return True for AnimatedPlayer check
        with patch("pedre.plugins.player.plugin.isinstance", return_value=True):
            self.plugin.update(1.0)

        # Verify movement applied
        assert mock_sprite.change_x == -5.0
        assert mock_sprite.change_y == 0.0

        # Verify direction changed to left
        mock_sprite.set_direction.assert_called_with("left")
        mock_sprite.update_animation.assert_called_once()

    def test_update_with_up_movement(self) -> None:
        """Test update applies up movement and updates direction."""
        mock_sprite = MagicMock()
        mock_sprite.current_direction = "down"
        mock_sprite.__class__.__name__ = "AnimatedPlayer"
        self.plugin.player_sprite = mock_sprite

        # Mock input for up movement
        self.mock_input_plugin.get_movement_vector.return_value = (0.0, 5.0)
        self.mock_dialog_plugin.is_showing.return_value = False

        # Patch isinstance to return True for AnimatedPlayer check
        with patch("pedre.plugins.player.plugin.isinstance", return_value=True):
            self.plugin.update(1.0)

        # Verify movement applied
        assert mock_sprite.change_x == 0.0
        assert mock_sprite.change_y == 5.0

        # Verify direction changed to up
        mock_sprite.set_direction.assert_called_with("up")
        mock_sprite.update_animation.assert_called_once()

    def test_update_with_down_movement(self) -> None:
        """Test update applies down movement and updates direction."""
        mock_sprite = MagicMock()
        mock_sprite.current_direction = "up"
        mock_sprite.__class__.__name__ = "AnimatedPlayer"
        self.plugin.player_sprite = mock_sprite

        # Mock input for down movement
        self.mock_input_plugin.get_movement_vector.return_value = (0.0, -5.0)
        self.mock_dialog_plugin.is_showing.return_value = False

        # Patch isinstance to return True for AnimatedPlayer check
        with patch("pedre.plugins.player.plugin.isinstance", return_value=True):
            self.plugin.update(1.0)

        # Verify movement applied
        assert mock_sprite.change_x == 0.0
        assert mock_sprite.change_y == -5.0

        # Verify direction changed to down
        mock_sprite.set_direction.assert_called_with("down")
        mock_sprite.update_animation.assert_called_once()

    def test_update_no_direction_change(self) -> None:
        """Test update when direction doesn't change."""
        mock_sprite = MagicMock()
        mock_sprite.current_direction = "right"
        mock_sprite.__class__.__name__ = "AnimatedPlayer"
        self.plugin.player_sprite = mock_sprite

        # Mock input for right movement (same as current direction)
        self.mock_input_plugin.get_movement_vector.return_value = (5.0, 0.0)
        self.mock_dialog_plugin.is_showing.return_value = False

        # Patch isinstance to return True for AnimatedPlayer check
        with patch("pedre.plugins.player.plugin.isinstance", return_value=True):
            self.plugin.update(1.0)

        # Verify movement applied
        assert mock_sprite.change_x == 5.0
        assert mock_sprite.change_y == 0.0

        # Verify set_direction was NOT called (no change)
        mock_sprite.set_direction.assert_not_called()

        # But animation should still update
        mock_sprite.update_animation.assert_called_once()

    @patch("pedre.plugins.player.plugin.logger")
    def test_apply_entity_state_with_position(self, mock_logger: MagicMock) -> None:
        """Test apply_entity_state logs when position is applied."""
        mock_sprite = MagicMock()
        mock_sprite.center_x = 0.0
        mock_sprite.center_y = 0.0
        self.plugin.player_sprite = mock_sprite

        state = {"player_x": 100.5, "player_y": 200.5}
        self.plugin.apply_entity_state(state)

        # Verify position was applied
        assert mock_sprite.center_x == 100.5
        assert mock_sprite.center_y == 200.5

        # Verify logging occurred
        assert mock_logger.info.called

    def test_from_dict_missing_keys(self) -> None:
        """Test from_dict with missing coordinate keys."""
        mock_sprite = MagicMock()
        mock_sprite.center_x = 50.0
        mock_sprite.center_y = 50.0
        self.plugin.player_sprite = mock_sprite

        # Test with missing player_x
        self.plugin.from_dict({"player_y": 100.0})
        assert mock_sprite.center_x == 50.0  # Unchanged
        assert mock_sprite.center_y == 50.0  # Unchanged

        # Test with missing player_y
        self.plugin.from_dict({"player_x": 100.0})
        assert mock_sprite.center_x == 50.0  # Unchanged
        assert mock_sprite.center_y == 50.0  # Unchanged

        # Test with empty dict
        self.plugin.from_dict({})
        assert mock_sprite.center_x == 50.0  # Unchanged
        assert mock_sprite.center_y == 50.0  # Unchanged

    @patch("pedre.plugins.player.plugin.logger")
    def test_get_animation_properties_invalid_type(self, mock_logger: MagicMock) -> None:
        """Test animation property with invalid type triggers warning."""
        properties = {
            "idle_down_frames": "not_an_int",  # Invalid type
            "walk_right_row": 2,  # Valid
        }

        result = self.plugin._get_animation_properties(properties)

        # Should exclude invalid type
        assert "idle_down_frames" not in result

        # Should include valid property
        assert "walk_right_row" in result
        assert result["walk_right_row"] == 2

        # Verify warning was logged
        assert mock_logger.warning.called

    def test_update_no_movement(self) -> None:
        """Test update when there's no movement (dx=0, dy=0)."""
        mock_sprite = MagicMock()
        mock_sprite.current_direction = "down"
        mock_sprite.__class__.__name__ = "AnimatedPlayer"
        self.plugin.player_sprite = mock_sprite

        # Mock input with no movement (branch 193->197)
        self.mock_input_plugin.get_movement_vector.return_value = (0.0, 0.0)
        self.mock_dialog_plugin.is_showing.return_value = False

        # Patch isinstance to return True for AnimatedPlayer check
        with patch("pedre.plugins.player.plugin.isinstance", return_value=True):
            self.plugin.update(1.0)

        # Verify no movement
        assert mock_sprite.change_x == 0.0
        assert mock_sprite.change_y == 0.0

        # Verify direction did NOT change (no movement means no direction update)
        mock_sprite.set_direction.assert_not_called()

        # Animation should still update (with moving=False)
        mock_sprite.update_animation.assert_called_once()

    def test_apply_entity_state_no_sprite(self) -> None:
        """Test apply_entity_state when player_sprite is None (branch 213->exit)."""
        # No sprite
        self.plugin.player_sprite = None

        state = {"player_x": 100.5, "player_y": 200.5}

        # Should not crash, just skip logging
        self.plugin.apply_entity_state(state)

        # Verify no sprite was modified (since there is none)
        assert self.plugin.player_sprite is None

    def test_apply_entity_state_missing_player_x(self) -> None:
        """Test apply_entity_state when player_x is missing (branch 213->exit)."""
        mock_sprite = MagicMock()
        mock_sprite.center_x = 50.0
        mock_sprite.center_y = 50.0
        self.plugin.player_sprite = mock_sprite

        # State without player_x
        state = {"player_y": 200.5}

        # Should not log since player_x is missing
        self.plugin.apply_entity_state(state)

        # Position should be unchanged (from_dict early returns)
        assert mock_sprite.center_x == 50.0
        assert mock_sprite.center_y == 50.0


if __name__ == "__main__":
    unittest.main()
