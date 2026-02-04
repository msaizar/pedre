"""Unit tests for ScenePlugin in src/pedre/plugins/scene/plugin.py."""

import unittest
from unittest.mock import MagicMock, patch

import arcade

from pedre.plugins.scene.base import TransitionState
from pedre.plugins.scene.plugin import ScenePlugin


class TestScenePlugin(unittest.TestCase):
    """Test Suite for ScenePlugin."""

    def setUp(self) -> None:
        """Set up the ScenePlugin and mock context."""
        self.plugin = ScenePlugin()
        self.mock_context = MagicMock()

        # Mock dependent plugins
        self.mock_cache_plugin = MagicMock()
        self.mock_waypoint_plugin = MagicMock()
        self.mock_npc_plugin = MagicMock()
        self.mock_portal_plugin = MagicMock()
        self.mock_interaction_plugin = MagicMock()
        self.mock_player_plugin = MagicMock()
        self.mock_script_plugin = MagicMock()
        self.mock_physics_plugin = MagicMock()
        self.mock_save_plugin = MagicMock()
        self.mock_event_bus = MagicMock()

        self.mock_context.cache_plugin = self.mock_cache_plugin
        self.mock_context.waypoint_plugin = self.mock_waypoint_plugin
        self.mock_context.npc_plugin = self.mock_npc_plugin
        self.mock_context.portal_plugin = self.mock_portal_plugin
        self.mock_context.interaction_plugin = self.mock_interaction_plugin
        self.mock_context.player_plugin = self.mock_player_plugin
        self.mock_context.script_plugin = self.mock_script_plugin
        self.mock_context.physics_plugin = self.mock_physics_plugin
        self.mock_context.save_plugin = self.mock_save_plugin
        self.mock_context.event_bus = self.mock_event_bus

        # Mock get_plugins to return empty dict for basic tests
        self.mock_context.get_plugins.return_value = {}

        self.plugin.setup(self.mock_context)

    def test_initialization(self) -> None:
        """Test proper initialization of the plugin."""
        plugin = ScenePlugin()
        assert plugin.name == "scene"
        assert "cache" in plugin.dependencies
        assert "waypoint" in plugin.dependencies
        assert "npc" in plugin.dependencies
        assert "portal" in plugin.dependencies
        assert "interaction" in plugin.dependencies
        assert "player" in plugin.dependencies
        assert "script" in plugin.dependencies
        assert plugin.current_scene == ""
        assert plugin.current_map == ""
        assert plugin.transition_state == TransitionState.NONE
        assert plugin.tile_map is None
        assert plugin.arcade_scene is None

    def test_setup(self) -> None:
        """Test setup assigns context."""
        plugin = ScenePlugin()
        mock_context = MagicMock()
        plugin.setup(mock_context)
        assert plugin.context == mock_context

    def test_reset(self) -> None:
        """Test reset clears scene state."""
        self.plugin.current_scene = "test_scene"
        self.plugin.current_map = "test_map.tmx"
        self.plugin.transition_state = TransitionState.FADING_OUT
        self.plugin.transition_alpha = 0.5
        self.plugin.pending_map_file = "pending.tmx"
        self.plugin.pending_spawn_waypoint = "waypoint1"

        # Add some sprites to wall list
        mock_sprite = MagicMock()
        self.plugin.wall_list.append(mock_sprite)

        self.plugin.reset()

        assert self.plugin.current_scene == ""
        assert self.plugin.current_map == ""
        assert self.plugin.transition_state == TransitionState.NONE
        assert self.plugin.pending_map_file is None
        assert self.plugin.pending_spawn_waypoint is None
        assert len(self.plugin.wall_list) == 0

    def test_get_current_map(self) -> None:
        """Test getting current map."""
        self.plugin.current_map = "test_map.tmx"
        assert self.plugin.get_current_map() == "test_map.tmx"

    def test_get_current_scene(self) -> None:
        """Test getting current scene from map filename."""
        self.plugin.current_map = "test_map.tmx"
        assert self.plugin.get_current_scene() == "test_map"

        self.plugin.current_map = "UPPER_CASE.tmx"
        assert self.plugin.get_current_scene() == "upper_case"

    def test_get_transition_state(self) -> None:
        """Test getting transition state."""
        self.plugin.transition_state = TransitionState.FADING_OUT
        assert self.plugin.get_transition_state() == TransitionState.FADING_OUT

    def test_get_wall_list(self) -> None:
        """Test getting wall list."""
        wall_list = self.plugin.get_wall_list()
        assert wall_list is not None
        assert isinstance(wall_list, arcade.SpriteList)

    def test_add_to_wall_list(self) -> None:
        """Test adding sprite to wall list."""
        mock_sprite = MagicMock()
        self.plugin.add_to_wall_list(mock_sprite)
        assert mock_sprite in self.plugin.wall_list

    def test_remove_from_wall_list(self) -> None:
        """Test removing sprite from wall list."""
        mock_sprite = MagicMock()
        self.plugin.wall_list.append(mock_sprite)
        self.plugin.remove_from_wall_list(mock_sprite)
        assert mock_sprite not in self.plugin.wall_list

    def test_get_next_spawn_waypoint(self) -> None:
        """Test getting next spawn waypoint."""
        self.plugin.next_spawn_waypoint = "entrance"
        assert self.plugin.get_next_spawn_waypoint() == "entrance"

    def test_clear_next_spawn_waypoint(self) -> None:
        """Test clearing next spawn waypoint."""
        self.plugin.next_spawn_waypoint = "entrance"
        self.plugin.clear_next_spawn_waypoint()
        assert self.plugin.get_next_spawn_waypoint() == ""

    def test_request_transition(self) -> None:
        """Test requesting a scene transition."""
        self.plugin.request_transition("new_map.tmx", "entrance")

        assert self.plugin.transition_state == TransitionState.FADING_OUT
        assert self.plugin.pending_map_file == "new_map.tmx"
        assert self.plugin.pending_spawn_waypoint == "entrance"

    def test_request_transition_no_waypoint(self) -> None:
        """Test requesting a scene transition without waypoint."""
        self.plugin.request_transition("new_map.tmx")

        assert self.plugin.transition_state == TransitionState.FADING_OUT
        assert self.plugin.pending_map_file == "new_map.tmx"
        assert self.plugin.pending_spawn_waypoint is None

    def test_request_transition_already_in_progress(self) -> None:
        """Test requesting transition when one is already in progress."""
        self.plugin.transition_state = TransitionState.FADING_OUT
        self.plugin.pending_map_file = "first_map.tmx"

        self.plugin.request_transition("second_map.tmx")

        # Should still be the first map
        assert self.plugin.pending_map_file == "first_map.tmx"

    @patch("pedre.plugins.scene.plugin.arcade.load_tilemap")
    @patch("pedre.plugins.scene.plugin.arcade.Scene.from_tilemap")
    @patch("pedre.plugins.scene.plugin.asset_path")
    def test_load_map_basic(
        self,
        mock_asset_path: MagicMock,
        mock_from_tilemap: MagicMock,
        mock_load_tilemap: MagicMock,
    ) -> None:
        """Test basic map loading."""
        # Setup mocks
        mock_asset_path.return_value = "/path/to/map.tmx"
        mock_tile_map = MagicMock()
        mock_load_tilemap.return_value = mock_tile_map

        mock_arcade_scene = MagicMock()
        mock_from_tilemap.return_value = mock_arcade_scene

        # Mock arcade scene to not have collision layers
        mock_arcade_scene.__contains__ = MagicMock(return_value=False)

        # Load map
        self.plugin._load_map("test_map.tmx")

        # Verify
        assert self.plugin.current_map == "test_map.tmx"
        assert self.plugin.tile_map == mock_tile_map
        assert self.plugin.arcade_scene == mock_arcade_scene
        mock_load_tilemap.assert_called_once()
        self.mock_physics_plugin.invalidate.assert_called_once()

    @patch("pedre.plugins.scene.plugin.arcade.load_tilemap")
    @patch("pedre.plugins.scene.plugin.arcade.Scene.from_tilemap")
    @patch("pedre.plugins.scene.plugin.asset_path")
    def test_extract_collision_layers(
        self,
        mock_asset_path: MagicMock,
        mock_from_tilemap: MagicMock,
        mock_load_tilemap: MagicMock,
    ) -> None:
        """Test extracting collision layers into wall list."""
        # Setup mocks
        mock_asset_path.return_value = "/path/to/map.tmx"
        mock_tile_map = MagicMock()
        mock_load_tilemap.return_value = mock_tile_map

        # Create mock sprites for collision layer
        mock_sprite1 = MagicMock()
        mock_sprite2 = MagicMock()

        mock_arcade_scene = MagicMock()
        mock_from_tilemap.return_value = mock_arcade_scene

        # Mock the arcade scene to have a "Walls" layer
        def contains_side_effect(_self: object, layer_name: str) -> bool:
            return layer_name == "Walls"

        mock_arcade_scene.__contains__ = contains_side_effect
        mock_arcade_scene.__getitem__ = MagicMock(return_value=[mock_sprite1, mock_sprite2])

        # Load map
        with patch("pedre.plugins.scene.plugin.settings") as mock_settings:
            mock_settings.SCENE_COLLISION_LAYER_NAMES = ["Walls"]
            self.plugin._load_map("test_map.tmx")

        # Verify wall list contains sprites
        assert len(self.plugin.wall_list) == 2
        assert mock_sprite1 in self.plugin.wall_list
        assert mock_sprite2 in self.plugin.wall_list

    def test_load_plugins_from_tiled(self) -> None:
        """Test loading plugins from tiled data."""
        # Create mock plugins with load_from_tiled methods
        mock_plugin1 = MagicMock()
        mock_plugin1.name = "plugin1"
        mock_plugin1.load_from_tiled = MagicMock()

        mock_plugin2 = MagicMock()
        mock_plugin2.name = "plugin2"
        mock_plugin2.load_from_tiled = MagicMock()

        # Plugin without load_from_tiled
        mock_plugin3 = MagicMock()
        mock_plugin3.name = "plugin3"
        del mock_plugin3.load_from_tiled

        self.mock_context.get_plugins.return_value = {
            "plugin1": mock_plugin1,
            "plugin2": mock_plugin2,
            "plugin3": mock_plugin3,
        }

        # Setup tile_map and arcade_scene
        self.plugin.tile_map = MagicMock()
        self.plugin.arcade_scene = MagicMock()

        self.plugin._load_plugins_from_tiled()

        # Verify only plugins with load_from_tiled were called
        mock_plugin1.load_from_tiled.assert_called_once_with(self.plugin.tile_map, self.plugin.arcade_scene)
        mock_plugin2.load_from_tiled.assert_called_once_with(self.plugin.tile_map, self.plugin.arcade_scene)

    @patch.object(ScenePlugin, "_load_map")
    def test_load_level_initial(self, mock_load_map: MagicMock) -> None:
        """Test loading initial level doesn't cache."""
        self.plugin.current_map = "old_map.tmx"

        # Mock NPC plugin methods
        self.mock_npc_plugin.load_scene_dialogs = MagicMock()
        self.mock_npc_plugin.get_npcs.return_value = {}

        self.plugin.load_level("new_map.tmx", initial=True)

        # Should not cache when initial=True
        self.mock_cache_plugin.cache_scene.assert_not_called()
        mock_load_map.assert_called_once_with("new_map.tmx")
        self.mock_save_plugin.apply_entity_states.assert_called_once()
        self.mock_npc_plugin.load_scene_dialogs.assert_called_once_with("new_map")
        self.mock_cache_plugin.restore_scene.assert_called_once_with("new_map")

    @patch.object(ScenePlugin, "_load_map")
    def test_load_level_not_initial(self, mock_load_map: MagicMock) -> None:
        """Test loading non-initial level caches current scene."""
        self.plugin.current_map = "old_map.tmx"

        # Mock NPC plugin methods
        self.mock_npc_plugin.load_scene_dialogs = MagicMock()
        self.mock_npc_plugin.get_npcs.return_value = {}

        self.plugin.load_level("new_map.tmx", initial=False)

        # Should cache old scene before loading new one
        self.mock_cache_plugin.cache_scene.assert_called_once_with("old_map")
        mock_load_map.assert_called_once_with("new_map.tmx")

    @patch.object(ScenePlugin, "_load_map")
    def test_load_level_syncs_npc_visibility(self, mock_load_map: MagicMock) -> None:
        """Test load level syncs NPC visibility with wall list."""
        # Create mock NPCs
        visible_npc_sprite = MagicMock()
        visible_npc_sprite.visible = True
        visible_npc = MagicMock()
        visible_npc.sprite = visible_npc_sprite

        invisible_npc_sprite = MagicMock()
        invisible_npc_sprite.visible = False
        invisible_npc = MagicMock()
        invisible_npc.sprite = invisible_npc_sprite

        self.mock_npc_plugin.get_npcs.return_value = {
            "npc1": visible_npc,
            "npc2": invisible_npc,
        }

        # Add invisible NPC to wall list (should be removed)
        self.plugin.wall_list.append(invisible_npc_sprite)

        # Mock NPC plugin methods
        self.mock_npc_plugin.load_scene_dialogs = MagicMock()

        self.plugin.load_level("test_map.tmx", initial=True)

        # Verify _load_map was called
        mock_load_map.assert_called_once_with("test_map.tmx")

        # Verify invisible NPC was removed from wall list
        assert invisible_npc_sprite not in self.plugin.wall_list
        # Verify visible NPC was added to wall list
        assert visible_npc_sprite in self.plugin.wall_list

    def test_update_no_transition(self) -> None:
        """Test update when no transition is happening."""
        self.plugin.transition_state = TransitionState.NONE
        self.plugin.transition_alpha = 0.0

        self.plugin.update(0.016)

        # Should remain unchanged
        assert self.plugin.transition_state == TransitionState.NONE
        assert self.plugin.transition_alpha == 0.0

    def test_update_fading_out(self) -> None:
        """Test update during fade out transition."""
        self.plugin.transition_state = TransitionState.FADING_OUT
        self.plugin.transition_alpha = 0.0
        self.plugin.transition_speed = 2.0

        self.plugin.update(0.1)

        # Alpha should increase
        assert self.plugin.transition_alpha == 0.2
        assert self.plugin.transition_state == TransitionState.FADING_OUT

    @patch.object(ScenePlugin, "_perform_map_switch")
    def test_update_fading_out_complete(self, mock_perform_map_switch: MagicMock) -> None:
        """Test update completes fade out and starts loading."""
        self.plugin.transition_state = TransitionState.FADING_OUT
        self.plugin.transition_alpha = 0.9
        self.plugin.transition_speed = 1.0

        self.plugin.update(0.2)

        # Should complete fade out and transition to fading in
        assert self.plugin.transition_alpha == 1.0
        assert self.plugin.transition_state == TransitionState.FADING_IN
        mock_perform_map_switch.assert_called_once()

    def test_update_fading_in(self) -> None:
        """Test update during fade in transition."""
        self.plugin.transition_state = TransitionState.FADING_IN
        self.plugin.transition_alpha = 1.0
        self.plugin.transition_speed = 2.0

        self.plugin.update(0.1)

        # Alpha should decrease
        assert self.plugin.transition_alpha == 0.8
        assert self.plugin.transition_state == TransitionState.FADING_IN

    def test_update_fading_in_complete(self) -> None:
        """Test update completes fade in transition."""
        self.plugin.transition_state = TransitionState.FADING_IN
        self.plugin.transition_alpha = 0.1
        self.plugin.transition_speed = 1.0

        self.plugin.update(0.2)

        # Should complete fade in
        assert self.plugin.transition_alpha == 0.0
        assert self.plugin.transition_state == TransitionState.NONE

    @patch.object(ScenePlugin, "load_level")
    def test_perform_map_switch(self, mock_load_level: MagicMock) -> None:
        """Test performing map switch during transition."""
        self.plugin.pending_map_file = "new_map.tmx"
        self.plugin.pending_spawn_waypoint = "entrance"

        self.plugin._perform_map_switch()

        # Verify waypoint was set before loading
        assert self.plugin.next_spawn_waypoint == "entrance"
        # Verify pending data was cleared
        assert self.plugin.pending_map_file is None
        assert self.plugin.pending_spawn_waypoint is None
        # Verify load_level was called
        mock_load_level.assert_called_once_with("new_map.tmx")

    @patch.object(ScenePlugin, "load_level")
    def test_perform_map_switch_no_waypoint(self, mock_load_level: MagicMock) -> None:
        """Test performing map switch without waypoint."""
        self.plugin.pending_map_file = "new_map.tmx"
        self.plugin.pending_spawn_waypoint = None

        self.plugin._perform_map_switch()

        # Verify waypoint was not set
        assert self.plugin.next_spawn_waypoint == ""
        mock_load_level.assert_called_once_with("new_map.tmx")

    @patch.object(ScenePlugin, "load_level")
    def test_perform_map_switch_no_pending(self, mock_load_level: MagicMock) -> None:
        """Test performing map switch with no pending map."""
        self.plugin.pending_map_file = None

        self.plugin._perform_map_switch()

        # Should do nothing
        mock_load_level.assert_not_called()

    @patch("pedre.plugins.scene.plugin.arcade.get_window")
    @patch("pedre.plugins.scene.plugin.arcade.camera.Camera2D")
    @patch("pedre.plugins.scene.plugin.arcade.draw_lrbt_rectangle_filled")
    def test_draw_transition_overlay(
        self,
        mock_draw_rect: MagicMock,
        mock_camera: MagicMock,
        mock_get_window: MagicMock,
    ) -> None:
        """Test drawing transition overlay."""
        mock_window = MagicMock()
        mock_window.width = 1280
        mock_window.height = 720
        mock_get_window.return_value = mock_window

        mock_cam_instance = MagicMock()
        mock_camera.return_value = mock_cam_instance

        self.plugin.transition_alpha = 0.5

        self.plugin._draw_transition_overlay()

        # Verify camera was used
        mock_cam_instance.use.assert_called_once()

        # Verify rectangle was drawn with correct alpha
        mock_draw_rect.assert_called_once()
        call_args = mock_draw_rect.call_args[0]
        assert call_args[4] == (0, 0, 0, 127)  # 0.5 * 255 = 127

    def test_on_draw_no_scene(self) -> None:
        """Test on_draw when no scene is loaded."""
        self.plugin.arcade_scene = None
        self.plugin.transition_state = TransitionState.NONE

        # Should not crash
        self.plugin.on_draw()

    @patch.object(ScenePlugin, "_draw_transition_overlay")
    def test_on_draw_with_transition(self, mock_draw_overlay: MagicMock) -> None:
        """Test on_draw draws overlay during transition."""
        mock_scene = MagicMock()
        self.plugin.arcade_scene = mock_scene
        self.plugin.transition_state = TransitionState.FADING_OUT

        self.plugin.on_draw()

        mock_scene.draw.assert_called_once()
        mock_draw_overlay.assert_called_once()

    @patch("pedre.plugins.scene.plugin.arcade.get_window")
    @patch("pedre.plugins.scene.plugin.arcade.draw_lrbt_rectangle_filled")
    def test_draw_overlay(self, mock_draw_rect: MagicMock, mock_get_window: MagicMock) -> None:
        """Test draw_overlay method."""
        mock_window = MagicMock()
        mock_window.width = 1280
        mock_window.height = 720
        mock_get_window.return_value = mock_window

        self.plugin.transition_state = TransitionState.FADING_OUT
        self.plugin.transition_alpha = 0.75

        self.plugin.draw_overlay()

        mock_draw_rect.assert_called_once()
        call_args = mock_draw_rect.call_args[0]
        assert call_args[4] == (0, 0, 0, 191)  # 0.75 * 255 = 191

    def test_draw_overlay_no_transition(self) -> None:
        """Test draw_overlay does nothing when not transitioning."""
        self.plugin.transition_state = TransitionState.NONE

        with patch("pedre.plugins.scene.plugin.arcade.draw_lrbt_rectangle_filled") as mock_draw:
            self.plugin.draw_overlay()
            mock_draw.assert_not_called()

    def test_get_save_state(self) -> None:
        """Test getting save state."""
        self.plugin.current_map = "test_map.tmx"
        state = self.plugin.get_save_state()

        assert state["current_map"] == "test_map.tmx"

    def test_get_save_state_empty(self) -> None:
        """Test getting save state when no map is loaded."""
        self.plugin.current_map = ""
        state = self.plugin.get_save_state()

        assert state == {}

    def test_restore_save_state(self) -> None:
        """Test restoring save state."""
        state = {"current_map": "restored_map.tmx"}
        self.plugin.restore_save_state(state)

        assert self.plugin.current_map == "restored_map.tmx"

    def test_to_dict(self) -> None:
        """Test converting to dictionary."""
        self.plugin.current_map = "test_map.tmx"
        data = self.plugin.to_dict()

        assert data["current_map"] == "test_map.tmx"

    def test_to_dict_empty(self) -> None:
        """Test converting to dictionary when empty."""
        self.plugin.current_map = ""
        data = self.plugin.to_dict()

        assert data == {}

    def test_from_dict(self) -> None:
        """Test loading from dictionary."""
        data = {"current_map": "loaded_map.tmx"}
        self.plugin.from_dict(data)

        assert self.plugin.current_map == "loaded_map.tmx"

    def test_from_dict_missing_key(self) -> None:
        """Test loading from dictionary with missing key."""
        data: dict[str, str] = {}
        self.plugin.current_map = "original.tmx"
        self.plugin.from_dict(data)

        # Should not change when key is missing
        assert self.plugin.current_map == "original.tmx"


class TestTransitionState(unittest.TestCase):
    """Test Suite for TransitionState enum."""

    def test_transition_state_values(self) -> None:
        """Test TransitionState enum has all expected values."""
        assert TransitionState.NONE is not None
        assert TransitionState.FADING_OUT is not None
        assert TransitionState.LOADING is not None
        assert TransitionState.FADING_IN is not None

    def test_transition_state_uniqueness(self) -> None:
        """Test TransitionState enum values are unique."""
        states = [
            TransitionState.NONE,
            TransitionState.FADING_OUT,
            TransitionState.LOADING,
            TransitionState.FADING_IN,
        ]
        assert len(states) == len(set(states))


if __name__ == "__main__":
    unittest.main()
