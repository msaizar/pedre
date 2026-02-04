"""Unit tests for PhysicsPlugin in src/pedre/plugins/physics/plugin.py."""

import unittest
from unittest.mock import MagicMock, patch

from pedre.plugins.physics.plugin import PhysicsPlugin


class TestPhysicsPlugin(unittest.TestCase):
    """Test Suite for PhysicsPlugin."""

    def setUp(self) -> None:
        """Set up the PhysicsPlugin and mock context."""
        self.plugin = PhysicsPlugin()
        self.mock_context = MagicMock()

        # Mock dependent plugins
        self.mock_player_plugin = MagicMock()
        self.mock_scene_plugin = MagicMock()
        self.mock_context.player_plugin = self.mock_player_plugin
        self.mock_context.scene_plugin = self.mock_scene_plugin

        # Setup mocks for engine creation
        self.mock_player = MagicMock()
        self.mock_player_plugin.get_player_sprite.return_value = self.mock_player

        self.mock_wall_list = MagicMock()
        self.mock_scene_plugin.get_wall_list.return_value = self.mock_wall_list

    @patch("pedre.plugins.physics.plugin.arcade.PhysicsEngineSimple")
    def test_initialization(self, mock_engine_cls: MagicMock) -> None:
        """Test proper initialization of the plugin."""
        assert self.plugin.name == "physics"
        assert "player" in self.plugin.dependencies
        # Verify it starts needing recreation (but setup calls create)
        plugin = PhysicsPlugin()
        assert plugin._needs_recreate is True
        assert plugin.physics_engine is None
        # Verify the mock was patched but not called yet
        mock_engine_cls.assert_not_called()

    @patch("pedre.plugins.physics.plugin.arcade.PhysicsEngineSimple")
    def test_setup_creates_engine(self, mock_engine_cls: MagicMock) -> None:
        """Test setup creates the physics engine."""
        self.plugin.setup(self.mock_context)

        mock_engine_cls.assert_called_once_with(self.mock_player, self.mock_wall_list)
        assert self.plugin.physics_engine == mock_engine_cls.return_value
        assert self.plugin._needs_recreate is False
        assert self.plugin.context == self.mock_context

    @patch("pedre.plugins.physics.plugin.arcade.PhysicsEngineSimple")
    def test_update_calls_engine_update(self, mock_engine_cls: MagicMock) -> None:
        """Test update calls physics engine update."""
        mock_engine_instance = MagicMock()
        mock_engine_cls.return_value = mock_engine_instance

        self.plugin.setup(self.mock_context)
        self.plugin.update(1.0)

        mock_engine_instance.update.assert_called_once()

    @patch("pedre.plugins.physics.plugin.arcade.PhysicsEngineSimple")
    def test_invalidate_triggers_recreation(self, mock_engine_cls: MagicMock) -> None:
        """Test invalidate causes engine recreation on next update."""
        self.plugin.setup(self.mock_context)
        mock_engine_cls.reset_mock()

        self.plugin.invalidate()
        assert self.plugin._needs_recreate is True

        # Update should trigger recreation
        self.plugin.update(1.0)

        mock_engine_cls.assert_called_once_with(self.mock_player, self.mock_wall_list)
        assert self.plugin._needs_recreate is False

    @patch("pedre.plugins.physics.plugin.arcade.PhysicsEngineSimple")
    def test_create_engine_handles_missing_player(self, mock_engine_cls: MagicMock) -> None:
        """Test engine is not created if player sprite is missing."""
        self.mock_player_plugin.get_player_sprite.return_value = None

        self.plugin.setup(self.mock_context)

        assert self.plugin.physics_engine is None
        mock_engine_cls.assert_not_called()
        assert self.plugin._needs_recreate is False


if __name__ == "__main__":
    unittest.main()
