"""Unit tests for CameraPlugin in src/pedre/plugins/camera/plugin.py."""

from unittest.mock import MagicMock, patch

import arcade
import pytest

from pedre.conf import settings
from pedre.plugins.camera.plugin import CameraPlugin


class TestCameraPlugin:
    """Test Suite for CameraPlugin."""

    @pytest.fixture
    def mock_camera(self) -> MagicMock:
        """Fixture for mock camera."""
        camera = MagicMock(spec=arcade.camera.Camera2D)
        camera.position = (0.0, 0.0)
        return camera

    @pytest.fixture
    def plugin(self, mock_camera: MagicMock) -> CameraPlugin:
        """Fixture for CameraPlugin with mock camera."""
        return CameraPlugin(camera=mock_camera, lerp_speed=0.1)

    def test_initialization(self, plugin: CameraPlugin, mock_camera: MagicMock) -> None:
        """Test proper initialization of the plugin."""
        assert plugin.name == "camera"
        assert plugin.dependencies == ["player", "npc"]
        assert plugin.camera == mock_camera
        assert plugin.lerp_speed == 0.1
        assert plugin.bounds is None
        assert plugin.follow_mode is None
        assert plugin.follow_target_npc is None
        assert plugin.follow_smooth is True

    def test_initialization_with_defaults(self) -> None:
        """Test initialization with default parameters."""
        plugin = CameraPlugin()
        assert plugin.camera is None
        assert plugin.lerp_speed == settings.CAMERA_LERP_SPEED
        assert plugin.bounds is None

    def test_cleanup(self, plugin: CameraPlugin) -> None:
        """Test cleanup method resets all state."""
        plugin.bounds = (0, 100, 0, 100)
        plugin.follow_mode = "player"
        plugin.follow_target_npc = "test_npc"
        plugin._follow_config = {"mode": "player"}

        plugin.cleanup()

        assert plugin.camera is None
        assert plugin.bounds is None
        assert plugin.follow_mode is None
        assert plugin.follow_target_npc is None
        assert plugin._follow_config is None

    def test_get_save_state(self, plugin: CameraPlugin) -> None:
        """Test get_save_state returns correct state."""
        plugin.lerp_speed = 0.2
        plugin.follow_mode = "npc"
        plugin.follow_target_npc = "merchant"
        plugin.follow_smooth = False

        state = plugin.get_save_state()

        assert state["lerp_speed"] == 0.2
        assert state["follow_mode"] == "npc"
        assert state["follow_target_npc"] == "merchant"
        assert state["follow_smooth"] is False

    def test_restore_save_state(self, plugin: CameraPlugin) -> None:
        """Test restore_save_state restores correct state."""
        state = {
            "lerp_speed": 0.15,
            "follow_mode": "player",
            "follow_target_npc": None,
            "follow_smooth": True,
        }

        plugin.restore_save_state(state)

        assert plugin.lerp_speed == 0.15
        assert plugin.follow_mode == "player"
        assert plugin.follow_target_npc is None
        assert plugin.follow_smooth is True

    def test_restore_save_state_with_defaults(self, plugin: CameraPlugin) -> None:
        """Test restore_save_state uses defaults for missing keys."""
        state: dict[str, str | None] = {}

        plugin.restore_save_state(state)

        assert plugin.lerp_speed == settings.CAMERA_LERP_SPEED
        assert plugin.follow_mode is None
        assert plugin.follow_target_npc is None
        assert plugin.follow_smooth is True

    def test_set_camera(self, plugin: CameraPlugin) -> None:
        """Test set_camera sets the camera."""
        new_camera = MagicMock(spec=arcade.camera.Camera2D)
        plugin.set_camera(new_camera)

        assert plugin.camera == new_camera

    def test_set_bounds_normal_map(self, plugin: CameraPlugin) -> None:
        """Test set_bounds with normal sized map."""
        # Map: 1600x1280, Viewport: 800x600
        plugin.set_bounds(1600, 1280, 800, 600)

        assert plugin.bounds is not None
        min_x, max_x, min_y, max_y = plugin.bounds

        # Camera center should be at least half viewport from edges
        assert min_x == 400  # half of 800
        assert max_x == 1200  # 1600 - 400
        assert min_y == 300  # half of 600
        assert max_y == 980  # 1280 - 300

    def test_set_bounds_small_map_width(self, plugin: CameraPlugin) -> None:
        """Test set_bounds when map width is smaller than viewport."""
        # Map: 600x1000, Viewport: 800x600
        plugin.set_bounds(600, 1000, 800, 600)

        assert plugin.bounds is not None
        min_x, max_x, min_y, max_y = plugin.bounds

        # When map < viewport, min_x and max_x should be map_width/2
        assert min_x == 300  # 600 / 2
        assert max_x == 300  # 600 / 2
        assert min_y == 300  # normal
        assert max_y == 700  # 1000 - 300

    def test_set_bounds_small_map_height(self, plugin: CameraPlugin) -> None:
        """Test set_bounds when map height is smaller than viewport."""
        # Map: 1000x400, Viewport: 800x600
        plugin.set_bounds(1000, 400, 800, 600)

        assert plugin.bounds is not None
        min_x, max_x, min_y, max_y = plugin.bounds

        assert min_x == 400  # normal
        assert max_x == 600  # 1000 - 400
        # When map < viewport, min_y and max_y should be map_height/2
        assert min_y == 200  # 400 / 2
        assert max_y == 200  # 400 / 2

    def test_set_bounds_small_map_both_dimensions(self, plugin: CameraPlugin) -> None:
        """Test set_bounds when map is smaller than viewport in both dimensions."""
        # Map: 400x300, Viewport: 800x600
        plugin.set_bounds(400, 300, 800, 600)

        assert plugin.bounds is not None
        min_x, max_x, min_y, max_y = plugin.bounds

        # Both should center
        assert min_x == 200  # 400 / 2
        assert max_x == 200  # 400 / 2
        assert min_y == 150  # 300 / 2
        assert max_y == 150  # 300 / 2

    def test_smooth_follow_without_bounds(self, plugin: CameraPlugin, mock_camera: MagicMock) -> None:
        """Test smooth_follow without boundary constraints."""
        mock_camera.position = (100.0, 100.0)
        plugin.lerp_speed = 0.1

        plugin.smooth_follow(200.0, 200.0)

        # Expected: new = current + (target - current) * lerp_speed = 100 + (200 - 100) * 0.1 = 110
        assert mock_camera.position == (110.0, 110.0)

    def test_smooth_follow_with_bounds(self, plugin: CameraPlugin, mock_camera: MagicMock) -> None:
        """Test smooth_follow with boundary constraints."""
        plugin.set_bounds(1000, 1000, 800, 600)
        mock_camera.position = (500.0, 400.0)
        plugin.lerp_speed = 0.2

        # Try to follow a target outside bounds
        plugin.smooth_follow(1200.0, 1200.0)

        # Target should be clamped to bounds first
        # bounds: min_x=400, max_x=600, min_y=300, max_y=700
        # clamped target: (600, 700)
        # new = 500 + (600 - 500) * 0.2 = 520
        # new = 400 + (700 - 400) * 0.2 = 460
        assert mock_camera.position == (520.0, 460.0)

    def test_smooth_follow_no_camera(self, plugin: CameraPlugin) -> None:
        """Test smooth_follow does nothing without camera."""
        plugin.camera = None
        plugin.smooth_follow(100.0, 100.0)
        # Should not crash

    def test_instant_follow_without_bounds(self, plugin: CameraPlugin, mock_camera: MagicMock) -> None:
        """Test instant_follow without boundary constraints."""
        plugin.instant_follow(300.0, 400.0)

        assert mock_camera.position == (300.0, 400.0)

    def test_instant_follow_with_bounds(self, plugin: CameraPlugin, mock_camera: MagicMock) -> None:
        """Test instant_follow with boundary constraints."""
        plugin.set_bounds(1000, 1000, 800, 600)

        # Try to set camera outside bounds
        plugin.instant_follow(1200.0, 1200.0)

        # Should be clamped to bounds: max_x=600, max_y=700
        assert mock_camera.position == (600.0, 700.0)

    def test_instant_follow_no_camera(self, plugin: CameraPlugin) -> None:
        """Test instant_follow does nothing without camera."""
        plugin.camera = None
        plugin.instant_follow(100.0, 100.0)
        # Should not crash

    def test_set_follow_player_smooth(self, plugin: CameraPlugin) -> None:
        """Test set_follow_player with smooth following."""
        plugin.set_follow_player(smooth=True)

        assert plugin.follow_mode == "player"
        assert plugin.follow_target_npc is None
        assert plugin.follow_smooth is True

    def test_set_follow_player_instant(self, plugin: CameraPlugin) -> None:
        """Test set_follow_player with instant following."""
        plugin.set_follow_player(smooth=False)

        assert plugin.follow_mode == "player"
        assert plugin.follow_target_npc is None
        assert plugin.follow_smooth is False

    def test_set_follow_npc_smooth(self, plugin: CameraPlugin) -> None:
        """Test set_follow_npc with smooth following."""
        plugin.set_follow_npc("merchant", smooth=True)

        assert plugin.follow_mode == "npc"
        assert plugin.follow_target_npc == "merchant"
        assert plugin.follow_smooth is True

    def test_set_follow_npc_instant(self, plugin: CameraPlugin) -> None:
        """Test set_follow_npc with instant following."""
        plugin.set_follow_npc("guard", smooth=False)

        assert plugin.follow_mode == "npc"
        assert plugin.follow_target_npc == "guard"
        assert plugin.follow_smooth is False

    def test_stop_follow(self, plugin: CameraPlugin) -> None:
        """Test stop_follow clears following state."""
        plugin.follow_mode = "player"
        plugin.follow_target_npc = "test"

        plugin.stop_follow()

        assert plugin.follow_mode is None
        assert plugin.follow_target_npc is None

    def test_update_follow_player_smooth(self, plugin: CameraPlugin, mock_camera: MagicMock) -> None:
        """Test update method with player follow mode (smooth)."""
        # Setup mock context
        mock_context = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 100.0
        mock_player_sprite.center_y = 200.0
        mock_context.player_plugin.get_player_sprite.return_value = mock_player_sprite
        plugin.setup(mock_context)

        plugin.set_follow_player(smooth=True)
        mock_camera.position = (0.0, 0.0)

        with patch.object(plugin, "smooth_follow") as mock_smooth:
            plugin.update(0.016)
            mock_smooth.assert_called_once_with(100.0, 200.0)

    def test_update_follow_player_instant(self, plugin: CameraPlugin) -> None:
        """Test update method with player follow mode (instant)."""
        mock_context = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 150.0
        mock_player_sprite.center_y = 250.0
        mock_context.player_plugin.get_player_sprite.return_value = mock_player_sprite
        plugin.setup(mock_context)

        plugin.set_follow_player(smooth=False)

        with patch.object(plugin, "instant_follow") as mock_instant:
            plugin.update(0.016)
            mock_instant.assert_called_once_with(150.0, 250.0)

    def test_update_follow_player_no_sprite(self, plugin: CameraPlugin) -> None:
        """Test update with player mode but no sprite available."""
        mock_context = MagicMock()
        mock_context.player_plugin.get_player_sprite.return_value = None
        plugin.setup(mock_context)

        plugin.set_follow_player(smooth=True)

        with patch.object(plugin, "smooth_follow") as mock_smooth:
            plugin.update(0.016)
            mock_smooth.assert_not_called()

    def test_update_follow_npc_smooth(self, plugin: CameraPlugin) -> None:
        """Test update method with NPC follow mode (smooth)."""
        mock_context = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.sprite.center_x = 300.0
        mock_npc_state.sprite.center_y = 400.0
        mock_context.npc_plugin.get_npc_by_name.return_value = mock_npc_state
        plugin.setup(mock_context)

        plugin.set_follow_npc("merchant", smooth=True)

        with patch.object(plugin, "smooth_follow") as mock_smooth:
            plugin.update(0.016)
            mock_smooth.assert_called_once_with(300.0, 400.0)

    def test_update_follow_npc_instant(self, plugin: CameraPlugin) -> None:
        """Test update method with NPC follow mode (instant)."""
        mock_context = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.sprite.center_x = 350.0
        mock_npc_state.sprite.center_y = 450.0
        mock_context.npc_plugin.get_npc_by_name.return_value = mock_npc_state
        plugin.setup(mock_context)

        plugin.set_follow_npc("guard", smooth=False)

        with patch.object(plugin, "instant_follow") as mock_instant:
            plugin.update(0.016)
            mock_instant.assert_called_once_with(350.0, 450.0)

    def test_update_follow_npc_not_found(self, plugin: CameraPlugin) -> None:
        """Test update with NPC mode but NPC not found."""
        mock_context = MagicMock()
        mock_context.npc_plugin.get_npc_by_name.return_value = None
        plugin.setup(mock_context)

        plugin.set_follow_npc("nonexistent", smooth=True)

        with patch.object(plugin, "smooth_follow") as mock_smooth:
            plugin.update(0.016)
            mock_smooth.assert_not_called()

    def test_update_follow_npc_no_plugin(self, plugin: CameraPlugin) -> None:
        """Test update with NPC mode but no npc_plugin available."""
        mock_context = MagicMock()
        mock_context.npc_plugin = None
        plugin.setup(mock_context)

        plugin.set_follow_npc("merchant", smooth=True)

        with patch.object(plugin, "smooth_follow") as mock_smooth:
            plugin.update(0.016)
            mock_smooth.assert_not_called()

    def test_update_follow_npc_no_target_name(self, plugin: CameraPlugin) -> None:
        """Test update with NPC mode but no target NPC name set."""
        mock_context = MagicMock()
        plugin.setup(mock_context)

        plugin.follow_mode = "npc"
        plugin.follow_target_npc = None  # No target

        with patch.object(plugin, "smooth_follow") as mock_smooth:
            plugin.update(0.016)
            mock_smooth.assert_not_called()

    def test_update_no_follow_mode(self, plugin: CameraPlugin) -> None:
        """Test update with no follow mode set."""
        mock_context = MagicMock()
        plugin.setup(mock_context)

        with (
            patch.object(plugin, "smooth_follow") as mock_smooth,
            patch.object(plugin, "instant_follow") as mock_instant,
        ):
            plugin.update(0.016)
            mock_smooth.assert_not_called()
            mock_instant.assert_not_called()

    def test_use(self, plugin: CameraPlugin, mock_camera: MagicMock) -> None:
        """Test use method activates the camera."""
        plugin.use()
        mock_camera.use.assert_called_once()

    def test_use_no_camera(self, plugin: CameraPlugin) -> None:
        """Test use method with no camera does nothing."""
        plugin.camera = None
        plugin.use()
        # Should not crash

    def test_get_follow_config(self, plugin: CameraPlugin) -> None:
        """Test get_follow_config returns stored config."""
        config = {"mode": "player", "smooth": True}
        plugin._follow_config = config

        result = plugin.get_follow_config()

        assert result == config

    def test_get_follow_config_none(self, plugin: CameraPlugin) -> None:
        """Test get_follow_config returns None when no config."""
        assert plugin.get_follow_config() is None

    def test_apply_follow_config_none(self, plugin: CameraPlugin) -> None:
        """Test apply_follow_config with no config uses default."""
        plugin._follow_config = None

        with patch.object(plugin, "set_follow_player") as mock_set:
            plugin.apply_follow_config()
            mock_set.assert_called_once_with(smooth=True)

    def test_apply_follow_config_none_mode(self, plugin: CameraPlugin) -> None:
        """Test apply_follow_config with 'none' mode."""
        plugin._follow_config = {"mode": "none", "smooth": True}

        with patch.object(plugin, "stop_follow") as mock_stop:
            plugin.apply_follow_config()
            mock_stop.assert_called_once()

    def test_apply_follow_config_player_mode(self, plugin: CameraPlugin) -> None:
        """Test apply_follow_config with 'player' mode."""
        plugin._follow_config = {"mode": "player", "smooth": False}

        with patch.object(plugin, "set_follow_player") as mock_set:
            plugin.apply_follow_config()
            mock_set.assert_called_once_with(smooth=False)

    def test_apply_follow_config_npc_mode(self, plugin: CameraPlugin) -> None:
        """Test apply_follow_config with 'npc' mode."""
        plugin._follow_config = {"mode": "npc", "target": "merchant", "smooth": True}

        with patch.object(plugin, "set_follow_npc") as mock_set:
            plugin.apply_follow_config()
            mock_set.assert_called_once_with("merchant", smooth=True)

    def test_apply_follow_config_npc_mode_no_target(self, plugin: CameraPlugin) -> None:
        """Test apply_follow_config with 'npc' mode but no target."""
        plugin._follow_config = {"mode": "npc", "smooth": True}

        with patch.object(plugin, "set_follow_npc") as mock_set:
            plugin.apply_follow_config()
            mock_set.assert_not_called()

    def test_apply_follow_config_unknown_mode(self, plugin: CameraPlugin) -> None:
        """Test apply_follow_config with unknown mode does nothing."""
        plugin._follow_config = {"mode": "unknown", "smooth": True}

        with (
            patch.object(plugin, "stop_follow") as mock_stop,
            patch.object(plugin, "set_follow_player") as mock_player,
            patch.object(plugin, "set_follow_npc") as mock_npc,
        ):
            plugin.apply_follow_config()
            # None of the methods should be called
            mock_stop.assert_not_called()
            mock_player.assert_not_called()
            mock_npc.assert_not_called()

    @patch("arcade.get_window")
    @patch("arcade.camera.Camera2D")
    def test_load_from_tiled_no_properties(
        self, mock_camera_cls: MagicMock, mock_get_window: MagicMock, plugin: CameraPlugin
    ) -> None:
        """Test load_from_tiled when tile_map has no properties."""
        mock_tile_map = MagicMock()
        mock_tile_map.width = 50
        mock_tile_map.height = 40
        mock_tile_map.tile_width = 32
        mock_tile_map.tile_height = 32
        # No properties attribute
        del mock_tile_map.properties

        mock_scene = MagicMock()
        mock_window = MagicMock()
        mock_window.width = 800
        mock_window.height = 600
        mock_get_window.return_value = mock_window

        mock_context = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 100.0
        mock_player_sprite.center_y = 100.0
        mock_context.player_plugin.get_player_sprite.return_value = mock_player_sprite
        plugin.setup(mock_context)

        plugin.load_from_tiled(mock_tile_map, mock_scene)

        assert plugin._follow_config == {"mode": "player", "smooth": True}
        assert plugin.camera is not None
        mock_get_window.assert_called()
        mock_camera_cls.assert_called_once()

    @patch("arcade.get_window")
    @patch("arcade.camera.Camera2D")
    def test_load_from_tiled_with_player_config(
        self, mock_camera_cls: MagicMock, mock_get_window: MagicMock, plugin: CameraPlugin
    ) -> None:
        """Test load_from_tiled with player camera configuration."""
        mock_tile_map = MagicMock()
        mock_tile_map.width = 50
        mock_tile_map.height = 40
        mock_tile_map.tile_width = 32
        mock_tile_map.tile_height = 32
        mock_tile_map.properties = {"camera_follow": "player", "camera_smooth": True}

        mock_scene = MagicMock()
        mock_window = MagicMock()
        mock_window.width = 800
        mock_window.height = 600
        mock_get_window.return_value = mock_window

        mock_context = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 200.0
        mock_player_sprite.center_y = 200.0
        mock_context.player_plugin.get_player_sprite.return_value = mock_player_sprite
        plugin.setup(mock_context)

        plugin.load_from_tiled(mock_tile_map, mock_scene)

        assert plugin._follow_config == {"mode": "player", "smooth": True}
        assert plugin.follow_mode == "player"
        mock_get_window.assert_called()
        mock_camera_cls.assert_called_once()

    @patch("arcade.get_window")
    @patch("arcade.camera.Camera2D")
    def test_load_from_tiled_with_npc_config(
        self, mock_camera_cls: MagicMock, mock_get_window: MagicMock, plugin: CameraPlugin
    ) -> None:
        """Test load_from_tiled with NPC camera configuration."""
        mock_tile_map = MagicMock()
        mock_tile_map.width = 50
        mock_tile_map.height = 40
        mock_tile_map.tile_width = 32
        mock_tile_map.tile_height = 32
        mock_tile_map.properties = {"camera_follow": "npc:merchant", "camera_smooth": False}

        mock_scene = MagicMock()
        mock_window = MagicMock()
        mock_window.width = 800
        mock_window.height = 600
        mock_get_window.return_value = mock_window

        mock_context = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.sprite.center_x = 300.0
        mock_npc_state.sprite.center_y = 300.0
        mock_context.npc_plugin.get_npc_by_name.return_value = mock_npc_state
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 100.0
        mock_player_sprite.center_y = 100.0
        mock_context.player_plugin.get_player_sprite.return_value = mock_player_sprite
        plugin.setup(mock_context)

        plugin.load_from_tiled(mock_tile_map, mock_scene)

        assert plugin._follow_config == {"mode": "npc", "target": "merchant", "smooth": False}
        assert plugin.follow_mode == "npc"
        assert plugin.follow_target_npc == "merchant"
        mock_get_window.assert_called()
        mock_camera_cls.assert_called_once()

    @patch("arcade.get_window")
    @patch("arcade.camera.Camera2D")
    def test_load_from_tiled_with_none_config(
        self, mock_camera_cls: MagicMock, mock_get_window: MagicMock, plugin: CameraPlugin
    ) -> None:
        """Test load_from_tiled with 'none' camera configuration."""
        mock_tile_map = MagicMock()
        mock_tile_map.width = 50
        mock_tile_map.height = 40
        mock_tile_map.tile_width = 32
        mock_tile_map.tile_height = 32
        mock_tile_map.properties = {"camera_follow": "none", "camera_smooth": True}

        mock_scene = MagicMock()
        mock_window = MagicMock()
        mock_window.width = 800
        mock_window.height = 600
        mock_get_window.return_value = mock_window

        mock_context = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 100.0
        mock_player_sprite.center_y = 100.0
        mock_context.player_plugin.get_player_sprite.return_value = mock_player_sprite
        plugin.setup(mock_context)

        plugin.load_from_tiled(mock_tile_map, mock_scene)

        assert plugin._follow_config == {"mode": "none", "smooth": True}
        assert plugin.follow_mode is None
        mock_get_window.assert_called()
        mock_camera_cls.assert_called_once()

    @patch("arcade.get_window")
    @patch("arcade.camera.Camera2D")
    def test_load_from_tiled_invalid_camera_follow_type(
        self, mock_camera_cls: MagicMock, mock_get_window: MagicMock, plugin: CameraPlugin
    ) -> None:
        """Test load_from_tiled with invalid camera_follow type."""
        mock_tile_map = MagicMock()
        mock_tile_map.width = 50
        mock_tile_map.height = 40
        mock_tile_map.tile_width = 32
        mock_tile_map.tile_height = 32
        mock_tile_map.properties = {"camera_follow": 123, "camera_smooth": True}  # Invalid type

        mock_scene = MagicMock()
        mock_window = MagicMock()
        mock_window.width = 800
        mock_window.height = 600
        mock_get_window.return_value = mock_window

        mock_context = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 100.0
        mock_player_sprite.center_y = 100.0
        mock_context.player_plugin.get_player_sprite.return_value = mock_player_sprite
        plugin.setup(mock_context)

        plugin.load_from_tiled(mock_tile_map, mock_scene)

        # Should default to player
        assert plugin._follow_config == {"mode": "player", "smooth": True}
        mock_get_window.assert_called()
        mock_camera_cls.assert_called_once()

    @patch("arcade.get_window")
    @patch("arcade.camera.Camera2D")
    def test_load_from_tiled_invalid_camera_smooth_type(
        self, mock_camera_cls: MagicMock, mock_get_window: MagicMock, plugin: CameraPlugin
    ) -> None:
        """Test load_from_tiled with invalid camera_smooth type."""
        mock_tile_map = MagicMock()
        mock_tile_map.width = 50
        mock_tile_map.height = 40
        mock_tile_map.tile_width = 32
        mock_tile_map.tile_height = 32
        mock_tile_map.properties = {"camera_follow": "player", "camera_smooth": "yes"}  # Invalid type

        mock_scene = MagicMock()
        mock_window = MagicMock()
        mock_window.width = 800
        mock_window.height = 600
        mock_get_window.return_value = mock_window

        mock_context = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 100.0
        mock_player_sprite.center_y = 100.0
        mock_context.player_plugin.get_player_sprite.return_value = mock_player_sprite
        plugin.setup(mock_context)

        plugin.load_from_tiled(mock_tile_map, mock_scene)

        # Should default smooth to True
        assert plugin._follow_config == {"mode": "player", "smooth": True}
        mock_get_window.assert_called()
        mock_camera_cls.assert_called_once()

    @patch("arcade.get_window")
    @patch("arcade.camera.Camera2D")
    def test_load_from_tiled_npc_without_name(
        self, mock_camera_cls: MagicMock, mock_get_window: MagicMock, plugin: CameraPlugin
    ) -> None:
        """Test load_from_tiled with 'npc:' but no NPC name."""
        mock_tile_map = MagicMock()
        mock_tile_map.width = 50
        mock_tile_map.height = 40
        mock_tile_map.tile_width = 32
        mock_tile_map.tile_height = 32
        mock_tile_map.properties = {"camera_follow": "npc:", "camera_smooth": True}

        mock_scene = MagicMock()
        mock_window = MagicMock()
        mock_window.width = 800
        mock_window.height = 600
        mock_get_window.return_value = mock_window

        mock_context = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 100.0
        mock_player_sprite.center_y = 100.0
        mock_context.player_plugin.get_player_sprite.return_value = mock_player_sprite
        plugin.setup(mock_context)

        plugin.load_from_tiled(mock_tile_map, mock_scene)

        # Should default to player
        assert plugin._follow_config == {"mode": "player", "smooth": True}
        mock_get_window.assert_called()
        mock_camera_cls.assert_called_once()

    @patch("arcade.get_window")
    @patch("arcade.camera.Camera2D")
    def test_load_from_tiled_npc_not_found(
        self, mock_camera_cls: MagicMock, mock_get_window: MagicMock, plugin: CameraPlugin
    ) -> None:
        """Test load_from_tiled with NPC that doesn't exist."""
        mock_tile_map = MagicMock()
        mock_tile_map.width = 50
        mock_tile_map.height = 40
        mock_tile_map.tile_width = 32
        mock_tile_map.tile_height = 32
        mock_tile_map.properties = {"camera_follow": "npc:nonexistent", "camera_smooth": True}

        mock_scene = MagicMock()
        mock_window = MagicMock()
        mock_window.width = 800
        mock_window.height = 600
        mock_get_window.return_value = mock_window

        mock_context = MagicMock()
        mock_context.npc_plugin.get_npc_by_name.return_value = None
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 100.0
        mock_player_sprite.center_y = 100.0
        mock_context.player_plugin.get_player_sprite.return_value = mock_player_sprite
        plugin.setup(mock_context)

        plugin.load_from_tiled(mock_tile_map, mock_scene)

        # Should default to player
        assert plugin._follow_config == {"mode": "player", "smooth": True}
        mock_get_window.assert_called()
        mock_camera_cls.assert_called_once()

    @patch("arcade.get_window")
    @patch("arcade.camera.Camera2D")
    def test_load_from_tiled_invalid_camera_follow_value(
        self, mock_camera_cls: MagicMock, mock_get_window: MagicMock, plugin: CameraPlugin
    ) -> None:
        """Test load_from_tiled with invalid camera_follow value."""
        mock_tile_map = MagicMock()
        mock_tile_map.width = 50
        mock_tile_map.height = 40
        mock_tile_map.tile_width = 32
        mock_tile_map.tile_height = 32
        mock_tile_map.properties = {"camera_follow": "invalid_value", "camera_smooth": True}

        mock_scene = MagicMock()
        mock_window = MagicMock()
        mock_window.width = 800
        mock_window.height = 600
        mock_get_window.return_value = mock_window

        mock_context = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 100.0
        mock_player_sprite.center_y = 100.0
        mock_context.player_plugin.get_player_sprite.return_value = mock_player_sprite
        plugin.setup(mock_context)

        plugin.load_from_tiled(mock_tile_map, mock_scene)

        # Should default to player
        assert plugin._follow_config == {"mode": "player", "smooth": True}
        mock_get_window.assert_called()
        mock_camera_cls.assert_called_once()

    def test_get_initial_position_npc_mode(self, plugin: CameraPlugin) -> None:
        """Test _get_initial_position with NPC follow mode."""
        mock_context = MagicMock()
        mock_npc_state = MagicMock()
        mock_npc_state.sprite.center_x = 500.0
        mock_npc_state.sprite.center_y = 600.0
        mock_context.npc_plugin.get_npc_by_name.return_value = mock_npc_state
        plugin.setup(mock_context)

        plugin._follow_config = {"mode": "npc", "target": "merchant"}

        pos = plugin._get_initial_position(1000, 1000)

        assert pos == (500.0, 600.0)

    def test_get_initial_position_player_mode(self, plugin: CameraPlugin) -> None:
        """Test _get_initial_position with player mode."""
        mock_context = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 250.0
        mock_player_sprite.center_y = 350.0
        mock_context.player_plugin.get_player_sprite.return_value = mock_player_sprite
        plugin.setup(mock_context)

        plugin._follow_config = {"mode": "player"}

        pos = plugin._get_initial_position(1000, 1000)

        assert pos == (250.0, 350.0)

    def test_get_initial_position_no_player_sprite(self, plugin: CameraPlugin) -> None:
        """Test _get_initial_position when no player sprite available."""
        mock_context = MagicMock()
        mock_context.player_plugin.get_player_sprite.return_value = None
        plugin.setup(mock_context)

        plugin._follow_config = {"mode": "player"}

        pos = plugin._get_initial_position(800, 600)

        # Should fallback to map center
        assert pos == (400.0, 300.0)

    def test_get_initial_position_no_map_dimensions(self, plugin: CameraPlugin) -> None:
        """Test _get_initial_position with no map dimensions."""
        mock_context = MagicMock()
        mock_context.player_plugin.get_player_sprite.return_value = None
        plugin.setup(mock_context)

        pos = plugin._get_initial_position(0, 0)

        # Should fallback to origin
        assert pos == (0.0, 0.0)

    def test_get_initial_position_npc_mode_no_target(self, plugin: CameraPlugin) -> None:
        """Test _get_initial_position with NPC mode but no target specified."""
        mock_context = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 100.0
        mock_player_sprite.center_y = 150.0
        mock_context.player_plugin.get_player_sprite.return_value = mock_player_sprite
        plugin.setup(mock_context)

        plugin._follow_config = {"mode": "npc"}  # No target

        pos = plugin._get_initial_position(1000, 1000)

        # Should fallback to player
        assert pos == (100.0, 150.0)

    def test_get_initial_position_npc_mode_no_plugin(self, plugin: CameraPlugin) -> None:
        """Test _get_initial_position with NPC mode but no npc_plugin."""
        mock_context = MagicMock()
        mock_context.npc_plugin = None
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 200.0
        mock_player_sprite.center_y = 250.0
        mock_context.player_plugin.get_player_sprite.return_value = mock_player_sprite
        plugin.setup(mock_context)

        plugin._follow_config = {"mode": "npc", "target": "merchant"}

        pos = plugin._get_initial_position(1000, 1000)

        # Should fallback to player
        assert pos == (200.0, 250.0)

    def test_get_initial_position_npc_mode_npc_not_found(self, plugin: CameraPlugin) -> None:
        """Test _get_initial_position with NPC mode but NPC not found."""
        mock_context = MagicMock()
        mock_context.npc_plugin.get_npc_by_name.return_value = None
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 300.0
        mock_player_sprite.center_y = 350.0
        mock_context.player_plugin.get_player_sprite.return_value = mock_player_sprite
        plugin.setup(mock_context)

        plugin._follow_config = {"mode": "npc", "target": "nonexistent"}

        pos = plugin._get_initial_position(1000, 1000)

        # Should fallback to player
        assert pos == (300.0, 350.0)
