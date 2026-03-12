"""Unit tests for ScenePlugin in src/pedre/plugins/scene/plugin.py."""

from unittest.mock import MagicMock, patch

import arcade
import pytest

from pedre.plugins.scene.base import TransitionState
from pedre.plugins.scene.plugin import ScenePlugin

ScenePluginCtx = tuple[ScenePlugin, MagicMock]


@pytest.fixture
def scene_plugin_ctx() -> ScenePluginCtx:
    """Create a fresh ScenePlugin with a mock context."""
    plugin = ScenePlugin()
    mock_context = MagicMock()
    mock_context.get_plugins.return_value = {}
    plugin.setup(mock_context)
    return plugin, mock_context


class TestScenePlugin:
    """Test Suite for ScenePlugin."""

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

    def test_reset(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test reset clears scene state."""
        plugin, _ = scene_plugin_ctx
        plugin.current_scene = "test_scene"
        plugin.current_map = "test_map.tmx"
        plugin.transition_state = TransitionState.FADING_OUT
        plugin.transition_alpha = 0.5
        plugin.pending_map_file = "pending.tmx"
        plugin.pending_spawn_waypoint = "waypoint1"

        # Add some sprites to wall list
        mock_sprite = MagicMock()
        plugin.wall_list.append(mock_sprite)

        plugin.reset()

        assert plugin.current_scene == ""
        assert plugin.current_map == ""
        assert plugin.transition_state == TransitionState.NONE
        assert plugin.pending_map_file is None
        assert plugin.pending_spawn_waypoint is None
        assert len(plugin.wall_list) == 0

    def test_get_current_map(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test getting current map."""
        plugin, _ = scene_plugin_ctx
        plugin.current_map = "test_map.tmx"
        assert plugin.get_current_map() == "test_map.tmx"

    def test_get_current_scene(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test getting current scene from map filename."""
        plugin, _ = scene_plugin_ctx
        plugin.current_map = "test_map.tmx"
        assert plugin.get_current_scene() == "test_map"

        plugin.current_map = "UPPER_CASE.tmx"
        assert plugin.get_current_scene() == "upper_case"

    def test_get_transition_state(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test getting transition state."""
        plugin, _ = scene_plugin_ctx
        plugin.transition_state = TransitionState.FADING_OUT
        assert plugin.get_transition_state() == TransitionState.FADING_OUT

    def test_get_wall_list(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test getting wall list."""
        plugin, _ = scene_plugin_ctx
        wall_list = plugin.get_wall_list()
        assert wall_list is not None
        assert isinstance(wall_list, arcade.SpriteList)

    def test_add_to_wall_list(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test adding sprite to wall list."""
        plugin, _ = scene_plugin_ctx
        mock_sprite = MagicMock()
        plugin.add_to_wall_list(mock_sprite)
        assert mock_sprite in plugin.wall_list

    def test_remove_from_wall_list(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test removing sprite from wall list."""
        plugin, _ = scene_plugin_ctx
        mock_sprite = MagicMock()
        plugin.wall_list.append(mock_sprite)
        plugin.remove_from_wall_list(mock_sprite)
        assert mock_sprite not in plugin.wall_list

    def test_get_next_spawn_waypoint(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test getting next spawn waypoint."""
        plugin, _ = scene_plugin_ctx
        plugin.next_spawn_waypoint = "entrance"
        assert plugin.get_next_spawn_waypoint() == "entrance"

    def test_clear_next_spawn_waypoint(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test clearing next spawn waypoint."""
        plugin, _ = scene_plugin_ctx
        plugin.next_spawn_waypoint = "entrance"
        plugin.clear_next_spawn_waypoint()
        assert plugin.get_next_spawn_waypoint() == ""

    def test_request_transition(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test requesting a scene transition."""
        plugin, _ = scene_plugin_ctx
        plugin.request_transition("new_map.tmx", "entrance")

        assert plugin.transition_state == TransitionState.FADING_OUT
        assert plugin.pending_map_file == "new_map.tmx"
        assert plugin.pending_spawn_waypoint == "entrance"

    def test_request_transition_no_waypoint(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test requesting a scene transition without waypoint."""
        plugin, _ = scene_plugin_ctx
        plugin.request_transition("new_map.tmx")

        assert plugin.transition_state == TransitionState.FADING_OUT
        assert plugin.pending_map_file == "new_map.tmx"
        assert plugin.pending_spawn_waypoint is None

    def test_request_transition_already_in_progress(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test requesting transition when one is already in progress."""
        plugin, _ = scene_plugin_ctx
        plugin.transition_state = TransitionState.FADING_OUT
        plugin.pending_map_file = "first_map.tmx"

        plugin.request_transition("second_map.tmx")

        # Should still be the first map
        assert plugin.pending_map_file == "first_map.tmx"

    @patch("pedre.plugins.scene.plugin.arcade.load_tilemap")
    @patch("pedre.plugins.scene.plugin.arcade.Scene.from_tilemap")
    @patch("pedre.plugins.scene.plugin.asset_path")
    def test_load_map_basic(
        self,
        mock_asset_path: MagicMock,
        mock_from_tilemap: MagicMock,
        mock_load_tilemap: MagicMock,
        scene_plugin_ctx: ScenePluginCtx,
    ) -> None:
        """Test basic map loading."""
        plugin, mock_context = scene_plugin_ctx

        # Setup mocks
        mock_asset_path.return_value = "/path/to/map.tmx"
        mock_tile_map = MagicMock()
        mock_load_tilemap.return_value = mock_tile_map

        mock_arcade_scene = MagicMock()
        mock_from_tilemap.return_value = mock_arcade_scene

        # Mock arcade scene to not have collision layers
        mock_arcade_scene.__contains__ = MagicMock(return_value=False)

        # Load map
        plugin._load_map("test_map.tmx")

        # Verify
        assert plugin.current_map == "test_map.tmx"
        assert plugin.tile_map == mock_tile_map
        assert plugin.arcade_scene == mock_arcade_scene
        mock_load_tilemap.assert_called_once()
        mock_context.physics_plugin.invalidate.assert_called_once()

    @patch("pedre.plugins.scene.plugin.arcade.load_tilemap")
    @patch("pedre.plugins.scene.plugin.arcade.Scene.from_tilemap")
    @patch("pedre.plugins.scene.plugin.asset_path")
    def test_extract_collision_layers(
        self,
        mock_asset_path: MagicMock,
        mock_from_tilemap: MagicMock,
        mock_load_tilemap: MagicMock,
        scene_plugin_ctx: ScenePluginCtx,
    ) -> None:
        """Test extracting collision layers into wall list."""
        plugin, _ = scene_plugin_ctx

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
            plugin._load_map("test_map.tmx")

        # Verify wall list contains sprites
        assert len(plugin.wall_list) == 2
        assert mock_sprite1 in plugin.wall_list
        assert mock_sprite2 in plugin.wall_list

    def test_extract_collision_layers_none_scene(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test extracting collision layers when arcade scene is None."""
        plugin, _ = scene_plugin_ctx
        wall_list = plugin._extract_collision_layers(None)

        # Should return empty sprite list
        assert isinstance(wall_list, arcade.SpriteList)
        assert len(wall_list) == 0

    def test_load_plugins_from_tiled(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test loading plugins from tiled data."""
        plugin, mock_context = scene_plugin_ctx

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

        mock_context.get_plugins.return_value = {
            "plugin1": mock_plugin1,
            "plugin2": mock_plugin2,
            "plugin3": mock_plugin3,
        }

        # Setup tile_map and arcade_scene
        plugin.tile_map = MagicMock()
        plugin.arcade_scene = MagicMock()

        plugin._load_plugins_from_tiled()

        # Verify only plugins with load_from_tiled were called
        mock_plugin1.load_from_tiled.assert_called_once_with(plugin.tile_map, plugin.arcade_scene)
        mock_plugin2.load_from_tiled.assert_called_once_with(plugin.tile_map, plugin.arcade_scene)

    def test_notify_plugins_scene_loaded(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test that _notify_plugins_scene_loaded calls on_scene_loaded on every plugin."""
        plugin, mock_context = scene_plugin_ctx

        mock_plugin1 = MagicMock()
        mock_plugin1.name = "plugin1"
        mock_plugin2 = MagicMock()
        mock_plugin2.name = "plugin2"

        mock_context.get_plugins.return_value = {
            "plugin1": mock_plugin1,
            "plugin2": mock_plugin2,
        }

        plugin._notify_plugins_scene_loaded("town")

        mock_plugin1.on_scene_loaded.assert_called_once_with("town")
        mock_plugin2.on_scene_loaded.assert_called_once_with("town")

    @patch.object(ScenePlugin, "_load_map")
    def test_load_level_initial(self, mock_load_map: MagicMock, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test loading initial level doesn't cache."""
        plugin, mock_context = scene_plugin_ctx
        plugin.current_map = "old_map.tmx"

        mock_context.npc_plugin.get_npcs.return_value = {}

        plugin.load_level("new_map.tmx", initial=True)

        # Should not cache when initial=True
        mock_context.cache_plugin.cache_scene.assert_not_called()
        mock_load_map.assert_called_once_with("new_map.tmx")
        mock_context.save_plugin.apply_entity_states.assert_called_once()
        mock_context.cache_plugin.restore_scene.assert_called_once_with("new_map")

    @patch.object(ScenePlugin, "_load_map")
    def test_load_level_not_initial(self, mock_load_map: MagicMock, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test loading non-initial level caches current scene."""
        plugin, mock_context = scene_plugin_ctx
        plugin.current_map = "old_map.tmx"

        mock_context.npc_plugin.get_npcs.return_value = {}

        plugin.load_level("new_map.tmx", initial=False)

        # Should cache old scene before loading new one
        mock_context.cache_plugin.cache_scene.assert_called_once_with("old_map")
        mock_load_map.assert_called_once_with("new_map.tmx")

    @patch.object(ScenePlugin, "_load_map")
    def test_load_level_syncs_npc_visibility(self, mock_load_map: MagicMock, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test load level syncs NPC visibility with wall list."""
        plugin, mock_context = scene_plugin_ctx

        # Create mock NPCs
        visible_npc_sprite = MagicMock()
        visible_npc_sprite.visible = True
        visible_npc = MagicMock()
        visible_npc.sprite = visible_npc_sprite

        invisible_npc_sprite = MagicMock()
        invisible_npc_sprite.visible = False
        invisible_npc = MagicMock()
        invisible_npc.sprite = invisible_npc_sprite

        mock_context.npc_plugin.get_npcs.return_value = {
            "npc1": visible_npc,
            "npc2": invisible_npc,
        }

        # Add invisible NPC to wall list (should be removed)
        plugin.wall_list.append(invisible_npc_sprite)

        plugin.load_level("test_map.tmx", initial=True)

        # Verify _load_map was called
        mock_load_map.assert_called_once_with("test_map.tmx")

        # Verify invisible NPC was removed from wall list
        assert invisible_npc_sprite not in plugin.wall_list
        # Verify visible NPC was added to wall list
        assert visible_npc_sprite in plugin.wall_list

    @patch.object(ScenePlugin, "_load_map")
    def test_load_level_npc_already_in_wall_list(
        self, mock_load_map: MagicMock, scene_plugin_ctx: ScenePluginCtx
    ) -> None:
        """Test load level handles NPC that's already in wall list."""
        plugin, mock_context = scene_plugin_ctx

        # Create mock NPC that's visible
        visible_npc_sprite = MagicMock()
        visible_npc_sprite.visible = True
        visible_npc = MagicMock()
        visible_npc.sprite = visible_npc_sprite

        mock_context.npc_plugin.get_npcs.return_value = {"npc1": visible_npc}

        # NPC is already in wall list
        plugin.wall_list.append(visible_npc_sprite)
        initial_wall_list_length = len(plugin.wall_list)

        plugin.load_level("test_map.tmx", initial=True)

        # Verify _load_map was called
        mock_load_map.assert_called_once_with("test_map.tmx")

        # Verify NPC is still in wall list and wasn't duplicated
        assert visible_npc_sprite in plugin.wall_list
        assert len(plugin.wall_list) == initial_wall_list_length

    def test_update_no_transition(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test update when no transition is happening."""
        plugin, _ = scene_plugin_ctx
        plugin.transition_state = TransitionState.NONE
        plugin.transition_alpha = 0.0

        plugin.update(0.016)

        # Should remain unchanged
        assert plugin.transition_state == TransitionState.NONE
        assert plugin.transition_alpha == 0.0

    def test_update_fading_out(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test update during fade out transition."""
        plugin, _ = scene_plugin_ctx
        plugin.transition_state = TransitionState.FADING_OUT
        plugin.transition_alpha = 0.0
        plugin.transition_speed = 2.0

        plugin.update(0.1)

        # Alpha should increase
        assert plugin.transition_alpha == 0.2
        assert plugin.transition_state == TransitionState.FADING_OUT

    @patch.object(ScenePlugin, "_perform_map_switch")
    def test_update_fading_out_complete(
        self, mock_perform_map_switch: MagicMock, scene_plugin_ctx: ScenePluginCtx
    ) -> None:
        """Test update completes fade out and starts loading."""
        plugin, _ = scene_plugin_ctx
        plugin.transition_state = TransitionState.FADING_OUT
        plugin.transition_alpha = 0.9
        plugin.transition_speed = 1.0

        plugin.update(0.2)

        # Should complete fade out and transition to fading in
        assert plugin.transition_alpha == 1.0
        assert plugin.transition_state == TransitionState.FADING_IN
        mock_perform_map_switch.assert_called_once()

    def test_update_fading_in(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test update during fade in transition."""
        plugin, _ = scene_plugin_ctx
        plugin.transition_state = TransitionState.FADING_IN
        plugin.transition_alpha = 1.0
        plugin.transition_speed = 2.0

        plugin.update(0.1)

        # Alpha should decrease
        assert plugin.transition_alpha == 0.8
        assert plugin.transition_state == TransitionState.FADING_IN

    def test_update_fading_in_complete(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test update completes fade in transition."""
        plugin, _ = scene_plugin_ctx
        plugin.transition_state = TransitionState.FADING_IN
        plugin.transition_alpha = 0.1
        plugin.transition_speed = 1.0

        plugin.update(0.2)

        # Should complete fade in
        assert plugin.transition_alpha == 0.0
        assert plugin.transition_state == TransitionState.NONE

    def test_update_loading_state(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test update handles LOADING state (though typically brief)."""
        plugin, _ = scene_plugin_ctx
        plugin.transition_state = TransitionState.LOADING
        plugin.transition_alpha = 1.0

        plugin.update(0.016)

        # Should remain in LOADING state (not handled by update)
        assert plugin.transition_state == TransitionState.LOADING
        assert plugin.transition_alpha == 1.0

    @patch.object(ScenePlugin, "load_level")
    def test_perform_map_switch(self, mock_load_level: MagicMock, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test performing map switch during transition."""
        plugin, _ = scene_plugin_ctx
        plugin.pending_map_file = "new_map.tmx"
        plugin.pending_spawn_waypoint = "entrance"

        plugin._perform_map_switch()

        # Verify waypoint was set before loading
        assert plugin.next_spawn_waypoint == "entrance"
        # Verify pending data was cleared
        assert plugin.pending_map_file is None
        assert plugin.pending_spawn_waypoint is None
        # Verify load_level was called
        mock_load_level.assert_called_once_with("new_map.tmx")

    @patch.object(ScenePlugin, "load_level")
    def test_perform_map_switch_no_waypoint(self, mock_load_level: MagicMock, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test performing map switch without waypoint."""
        plugin, _ = scene_plugin_ctx
        plugin.pending_map_file = "new_map.tmx"
        plugin.pending_spawn_waypoint = None

        plugin._perform_map_switch()

        # Verify waypoint was not set
        assert plugin.next_spawn_waypoint == ""
        mock_load_level.assert_called_once_with("new_map.tmx")

    @patch.object(ScenePlugin, "load_level")
    def test_perform_map_switch_no_pending(self, mock_load_level: MagicMock, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test performing map switch with no pending map."""
        plugin, _ = scene_plugin_ctx
        plugin.pending_map_file = None

        plugin._perform_map_switch()

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
        scene_plugin_ctx: ScenePluginCtx,
    ) -> None:
        """Test drawing transition overlay."""
        plugin, _ = scene_plugin_ctx
        mock_window = MagicMock()
        mock_window.width = 1280
        mock_window.height = 720
        mock_get_window.return_value = mock_window

        mock_cam_instance = MagicMock()
        mock_camera.return_value = mock_cam_instance

        plugin.transition_alpha = 0.5

        plugin._draw_transition_overlay()

        # Verify camera was used
        mock_cam_instance.use.assert_called_once()

        # Verify rectangle was drawn with correct alpha
        mock_draw_rect.assert_called_once()
        call_args = mock_draw_rect.call_args[0]
        assert call_args[4] == (0, 0, 0, 127)  # 0.5 * 255 = 127

    def test_on_draw_no_scene(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test on_draw when no scene is loaded."""
        plugin, _ = scene_plugin_ctx
        plugin.arcade_scene = None
        plugin.transition_state = TransitionState.NONE

        # Should not crash
        plugin.on_draw()

    @patch.object(ScenePlugin, "_draw_transition_overlay")
    def test_on_draw_with_transition(self, mock_draw_overlay: MagicMock, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test on_draw draws overlay during transition."""
        plugin, _ = scene_plugin_ctx
        mock_scene = MagicMock()
        plugin.arcade_scene = mock_scene
        plugin.transition_state = TransitionState.FADING_OUT

        plugin.on_draw()

        mock_scene.draw.assert_called_once()
        mock_draw_overlay.assert_called_once()

    @patch("pedre.plugins.scene.plugin.arcade.get_window")
    @patch("pedre.plugins.scene.plugin.arcade.draw_lrbt_rectangle_filled")
    def test_draw_overlay(
        self,
        mock_draw_rect: MagicMock,
        mock_get_window: MagicMock,
        scene_plugin_ctx: ScenePluginCtx,
    ) -> None:
        """Test draw_overlay method."""
        plugin, _ = scene_plugin_ctx
        mock_window = MagicMock()
        mock_window.width = 1280
        mock_window.height = 720
        mock_get_window.return_value = mock_window

        plugin.transition_state = TransitionState.FADING_OUT
        plugin.transition_alpha = 0.75

        plugin.draw_overlay()

        mock_draw_rect.assert_called_once()
        call_args = mock_draw_rect.call_args[0]
        assert call_args[4] == (0, 0, 0, 191)  # 0.75 * 255 = 191

    def test_draw_overlay_no_transition(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test draw_overlay does nothing when not transitioning."""
        plugin, _ = scene_plugin_ctx
        plugin.transition_state = TransitionState.NONE

        with patch("pedre.plugins.scene.plugin.arcade.draw_lrbt_rectangle_filled") as mock_draw:
            plugin.draw_overlay()
            mock_draw.assert_not_called()

    def test_get_save_state(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test getting save state."""
        plugin, _ = scene_plugin_ctx
        plugin.current_map = "test_map.tmx"
        state = plugin.get_save_state()

        assert state["current_map"] == "test_map.tmx"

    def test_get_save_state_empty(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test getting save state when no map is loaded."""
        plugin, _ = scene_plugin_ctx
        plugin.current_map = ""
        state = plugin.get_save_state()

        assert state == {}

    def test_restore_save_state(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test restoring save state."""
        plugin, _ = scene_plugin_ctx
        state = {"current_map": "restored_map.tmx"}
        plugin.restore_save_state(state)

        assert plugin.current_map == "restored_map.tmx"

    def test_to_dict(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test converting to dictionary."""
        plugin, _ = scene_plugin_ctx
        plugin.current_map = "test_map.tmx"
        data = plugin.to_dict()

        assert data["current_map"] == "test_map.tmx"

    def test_to_dict_empty(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test converting to dictionary when empty."""
        plugin, _ = scene_plugin_ctx
        plugin.current_map = ""
        data = plugin.to_dict()

        assert data == {}

    def test_from_dict(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test loading from dictionary."""
        plugin, _ = scene_plugin_ctx
        data = {"current_map": "loaded_map.tmx"}
        plugin.from_dict(data)

        assert plugin.current_map == "loaded_map.tmx"

    def test_from_dict_missing_key(self, scene_plugin_ctx: ScenePluginCtx) -> None:
        """Test loading from dictionary with missing key."""
        plugin, _ = scene_plugin_ctx
        data: dict[str, str] = {}
        plugin.current_map = "original.tmx"
        plugin.from_dict(data)

        # Should not change when key is missing
        assert plugin.current_map == "original.tmx"


class TestTransitionState:
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
