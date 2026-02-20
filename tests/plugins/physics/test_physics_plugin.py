"""Unit tests for PhysicsPlugin in src/pedre/plugins/physics/plugin.py."""

from unittest.mock import MagicMock, patch

from pedre.plugins.physics.plugin import PhysicsPlugin


def _make_context() -> MagicMock:
    """Create a mock context with player and scene plugins pre-configured."""
    context = MagicMock()
    context.player_plugin.get_player_sprite.return_value = MagicMock()
    context.scene_plugin.get_wall_list.return_value = MagicMock()
    return context


class TestPhysicsPlugin:
    """Test Suite for PhysicsPlugin."""

    @patch("pedre.plugins.physics.plugin.arcade.PhysicsEngineSimple")
    def test_initialization(self, mock_engine_cls: MagicMock) -> None:
        """Test proper initialization of the plugin."""
        plugin = PhysicsPlugin()
        assert plugin.name == "physics"
        assert "player" in plugin.dependencies
        assert plugin._needs_recreate is True
        assert plugin.physics_engine is None
        mock_engine_cls.assert_not_called()

    @patch("pedre.plugins.physics.plugin.arcade.PhysicsEngineSimple")
    def test_setup_creates_engine(self, mock_engine_cls: MagicMock) -> None:
        """Test setup creates the physics engine."""
        context = _make_context()
        mock_player = context.player_plugin.get_player_sprite.return_value
        mock_wall_list = context.scene_plugin.get_wall_list.return_value
        plugin = PhysicsPlugin()

        plugin.setup(context)

        mock_engine_cls.assert_called_once_with(mock_player, mock_wall_list)
        assert plugin.physics_engine == mock_engine_cls.return_value
        assert plugin._needs_recreate is False
        assert plugin.context == context

    @patch("pedre.plugins.physics.plugin.arcade.PhysicsEngineSimple")
    def test_update_calls_engine_update(self, mock_engine_cls: MagicMock) -> None:
        """Test update calls physics engine update."""
        context = _make_context()
        mock_engine_instance = MagicMock()
        mock_engine_cls.return_value = mock_engine_instance
        plugin = PhysicsPlugin()

        plugin.setup(context)
        plugin.update(1.0)

        mock_engine_instance.update.assert_called_once()

    @patch("pedre.plugins.physics.plugin.arcade.PhysicsEngineSimple")
    def test_invalidate_triggers_recreation(self, mock_engine_cls: MagicMock) -> None:
        """Test invalidate causes engine recreation on next update."""
        context = _make_context()
        mock_player = context.player_plugin.get_player_sprite.return_value
        mock_wall_list = context.scene_plugin.get_wall_list.return_value
        plugin = PhysicsPlugin()

        plugin.setup(context)
        mock_engine_cls.reset_mock()

        plugin.invalidate()
        assert plugin._needs_recreate is True

        plugin.update(1.0)

        mock_engine_cls.assert_called_once_with(mock_player, mock_wall_list)
        assert plugin._needs_recreate is False

    @patch("pedre.plugins.physics.plugin.arcade.PhysicsEngineSimple")
    def test_create_engine_handles_missing_player(self, mock_engine_cls: MagicMock) -> None:
        """Test engine is not created if player sprite is missing."""
        context = _make_context()
        context.player_plugin.get_player_sprite.return_value = None
        plugin = PhysicsPlugin()

        plugin.setup(context)

        assert plugin.physics_engine is None
        mock_engine_cls.assert_not_called()
        assert plugin._needs_recreate is False

    @patch("pedre.plugins.physics.plugin.arcade.PhysicsEngineSimple")
    def test_update_with_no_physics_engine(self, mock_engine_cls: MagicMock) -> None:
        """Test update handles missing physics engine gracefully."""
        context = _make_context()
        context.player_plugin.get_player_sprite.return_value = None
        plugin = PhysicsPlugin()

        plugin.setup(context)
        plugin.update(1.0)

        assert plugin.physics_engine is None
        mock_engine_cls.assert_not_called()
