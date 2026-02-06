"""Unit tests for Game class in src/pedre/game.py."""

import unittest
from unittest.mock import MagicMock, patch

import arcade

from pedre.game import Game


class TestGame(unittest.TestCase):
    """Test Suite for Game class."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.mock_window = MagicMock(spec=arcade.Window)

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    def test_init(
        self,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test initialization of Game."""
        # Setup mocks
        mock_event_bus = MagicMock()
        mock_event_bus_class.return_value = mock_event_bus

        mock_game_context = MagicMock()
        mock_game_context_class.return_value = mock_game_context

        mock_action_loader = MagicMock()
        mock_action_loader_class.return_value = mock_action_loader

        mock_event_loader = MagicMock()
        mock_event_loader_class.return_value = mock_event_loader

        mock_condition_loader = MagicMock()
        mock_condition_loader_class.return_value = mock_condition_loader

        mock_plugin_loader = MagicMock()
        mock_plugin_instances = {"plugin1": MagicMock(), "plugin2": MagicMock()}
        mock_plugin_loader.instantiate_all.return_value = mock_plugin_instances
        mock_plugin_loader_class.return_value = mock_plugin_loader

        # Create game instance
        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()

        # Verify window is set
        assert game.window == self.mock_window

        # Verify event bus created
        mock_event_bus_class.assert_called_once()
        assert game.event_bus == mock_event_bus

        # Verify game context created with correct args
        mock_game_context_class.assert_called_once_with(
            event_bus=mock_event_bus,
            window=self.mock_window,
        )
        assert game.game_context == mock_game_context

        # Verify action loader created and loaded
        mock_action_loader_class.assert_called_once()
        mock_action_loader.load_modules.assert_called_once()

        # Verify event loader created and loaded
        mock_event_loader_class.assert_called_once()
        mock_event_loader.load_modules.assert_called_once()

        # Verify condition loader created and loaded
        mock_condition_loader_class.assert_called_once()
        mock_condition_loader.load_modules.assert_called_once()

        # Verify plugin loader created
        mock_plugin_loader_class.assert_called_once()
        assert game.plugin_loader == mock_plugin_loader

        # Verify plugins instantiated and registered
        mock_plugin_loader.instantiate_all.assert_called_once()
        assert mock_game_context.register_plugin.call_count == 2
        mock_game_context.register_plugin.assert_any_call("plugin1", mock_plugin_instances["plugin1"])
        mock_game_context.register_plugin.assert_any_call("plugin2", mock_plugin_instances["plugin2"])

        # Verify plugins setup
        mock_plugin_loader.setup_all.assert_called_once_with(mock_game_context)

        # Verify game view is not created yet (lazy initialization)
        assert game._game_view is None

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    @patch("pedre.game.GameView")
    def test_game_view_property_lazy_initialization(
        self,
        mock_game_view_class: MagicMock,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test game_view property creates GameView on first access."""
        # Setup mocks for plugin loader
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_view = MagicMock()
        mock_game_view_class.return_value = mock_game_view

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()

        # Game view should not exist initially
        assert game._game_view is None

        # First access creates the view
        result = game.game_view
        assert result == mock_game_view
        mock_game_view_class.assert_called_once_with(game)

        # Subsequent access returns cached view
        result2 = game.game_view
        assert result2 == mock_game_view
        # Still only called once (cached)
        assert mock_game_view_class.call_count == 1

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    def test_has_game_view_false(
        self,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test has_game_view returns False when no view exists."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()

        assert game.has_game_view() is False

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    @patch("pedre.game.GameView")
    def test_has_game_view_true(
        self,
        mock_game_view_class: MagicMock,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test has_game_view returns True when view exists."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()

        # Access game_view property to create it
        _ = game.game_view
        mock_game_view_class.assert_called_once()
        assert game.has_game_view() is True

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    @patch("pedre.game.GameView")
    def test_show_game(
        self,
        mock_game_view_class: MagicMock,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test show_game displays the game view."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_view = MagicMock()
        mock_game_view_class.return_value = mock_game_view

        game = Game(self.mock_window)
        game.show_game()

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()

        # Verify window.show_view was called with game_view
        mock_game_view_class.assert_called_once_with(game)
        self.mock_window.show_view.assert_called_once_with(mock_game_view)

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    @patch("pedre.game.GameView")
    def test_start_new_game_no_existing_view(
        self,
        mock_game_view_class: MagicMock,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test start_new_game when no existing view."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_view = MagicMock()
        mock_game_view_class.return_value = mock_game_view

        game = Game(self.mock_window)
        game.start_new_game()

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()

        # Verify show_view was called
        mock_game_view_class.assert_called_once_with(game)
        self.mock_window.show_view.assert_called_once()

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    @patch("pedre.game.GameView")
    def test_start_new_game_with_existing_view(
        self,
        mock_game_view_class: MagicMock,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test start_new_game cleans up existing view."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_old_view = MagicMock()
        mock_new_view = MagicMock()
        mock_game_view_class.side_effect = [mock_old_view, mock_new_view]

        game = Game(self.mock_window)
        # Create initial view
        _ = game.game_view

        # Start new game
        game.start_new_game()

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()

        # Verify old view was cleaned up
        mock_old_view.cleanup.assert_called_once()

        # Verify new view was created and shown
        assert mock_game_view_class.call_count == 2
        self.mock_window.show_view.assert_called_once_with(mock_new_view)

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    def test_start_game_or_load_with_autosave(
        self,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test start_game_or_load loads autosave when it exists."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_context = MagicMock()
        mock_game_context_class.return_value = mock_game_context

        mock_save_plugin = MagicMock()
        mock_save_data = {"some": "data"}
        mock_save_plugin.save_exists.return_value = True
        mock_save_plugin.load_auto_save.return_value = mock_save_data
        mock_game_context.save_plugin = mock_save_plugin

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()
        with patch.object(game, "load_game") as mock_load_game:
            game.start_game_or_load()

            # Verify autosave was checked
            mock_save_plugin.save_exists.assert_called_once_with(slot=0)
            mock_save_plugin.load_auto_save.assert_called_once()

            # Verify load_game was called
            mock_load_game.assert_called_once_with(mock_save_data)

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    def test_start_game_or_load_without_autosave(
        self,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test start_game_or_load starts new game when no autosave."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_context = MagicMock()
        mock_game_context_class.return_value = mock_game_context

        mock_save_plugin = MagicMock()
        mock_save_plugin.save_exists.return_value = False
        mock_game_context.save_plugin = mock_save_plugin

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()

        with patch.object(game, "start_new_game") as mock_start_new_game:
            game.start_game_or_load()

            # Verify autosave was checked
            mock_save_plugin.save_exists.assert_called_once_with(slot=0)

            # Verify start_new_game was called
            mock_start_new_game.assert_called_once()

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    def test_start_game_or_load_autosave_exists_but_load_returns_none(
        self,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test start_game_or_load starts new game when autosave exists but load returns None."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_context = MagicMock()
        mock_game_context_class.return_value = mock_game_context

        mock_save_plugin = MagicMock()
        mock_save_plugin.save_exists.return_value = True
        mock_save_plugin.load_auto_save.return_value = None  # Returns None
        mock_game_context.save_plugin = mock_save_plugin

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()

        with patch.object(game, "start_new_game") as mock_start_new_game:
            game.start_game_or_load()

            # Verify autosave was checked
            mock_save_plugin.save_exists.assert_called_once_with(slot=0)
            mock_save_plugin.load_auto_save.assert_called_once()

            # Verify start_new_game was called (fallback)
            mock_start_new_game.assert_called_once()

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    def test_start_game_or_load_no_save_plugin(
        self,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test start_game_or_load starts new game when no save plugin."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_context = MagicMock()
        mock_game_context_class.return_value = mock_game_context
        mock_game_context.save_plugin = None

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()

        with patch.object(game, "start_new_game") as mock_start_new_game:
            game.start_game_or_load()

            # Verify start_new_game was called
            mock_start_new_game.assert_called_once()

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    @patch("pedre.game.GameView")
    def test_continue_game_with_existing_view(
        self,
        mock_game_view_class: MagicMock,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test continue_game resumes existing view."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_view = MagicMock()
        mock_game_view_class.return_value = mock_game_view

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()
        # Create view
        _ = game.game_view

        game.continue_game()

        # Verify window.show_view was called (resume)
        self.mock_window.show_view.assert_called_once_with(mock_game_view)

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    def test_continue_game_with_autosave(
        self,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test continue_game loads autosave when no existing view."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_context = MagicMock()
        mock_game_context_class.return_value = mock_game_context

        mock_save_plugin = MagicMock()
        mock_save_data = {"some": "data"}
        mock_save_plugin.load_auto_save.return_value = mock_save_data
        mock_game_context.save_plugin = mock_save_plugin

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()

        with patch.object(game, "load_game") as mock_load_game:
            game.continue_game()

            # Verify autosave was loaded
            mock_save_plugin.load_auto_save.assert_called_once()

            # Verify load_game was called
            mock_load_game.assert_called_once_with(mock_save_data)

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    def test_continue_game_no_save_plugin(
        self,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test continue_game does nothing when no save plugin."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_context = MagicMock()
        mock_game_context_class.return_value = mock_game_context
        mock_game_context.save_plugin = None

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()
        game.continue_game()

        # Window show_view should not be called
        self.mock_window.show_view.assert_not_called()

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    def test_continue_game_no_autosave(
        self,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test continue_game does nothing when no autosave."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_context = MagicMock()
        mock_game_context_class.return_value = mock_game_context

        mock_save_plugin = MagicMock()
        mock_save_plugin.load_auto_save.return_value = None
        mock_game_context.save_plugin = mock_save_plugin

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()
        game.continue_game()

        # Verify autosave was attempted
        mock_save_plugin.load_auto_save.assert_called_once()

        # Window show_view should not be called
        self.mock_window.show_view.assert_not_called()

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    @patch("pedre.game.GameView")
    def test_load_game(
        self,
        mock_game_view_class: MagicMock,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test load_game restores save data."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_context = MagicMock()
        mock_game_context_class.return_value = mock_game_context

        mock_save_plugin = MagicMock()
        mock_game_context.save_plugin = mock_save_plugin

        mock_game_view = MagicMock()
        mock_game_view_class.return_value = mock_game_view

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()

        mock_save_data = MagicMock()
        game.load_game(mock_save_data)

        # Verify save data was restored
        mock_save_plugin.restore_game_data.assert_called_once_with(mock_save_data)

        # Verify new game view was created
        mock_game_view_class.assert_called_once_with(game)

        # Verify window.show_view was called
        self.mock_window.show_view.assert_called_once_with(mock_game_view)

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    @patch("pedre.game.GameView")
    def test_load_game_with_existing_view(
        self,
        mock_game_view_class: MagicMock,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test load_game cleans up existing view before loading."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_context = MagicMock()
        mock_game_context_class.return_value = mock_game_context

        mock_save_plugin = MagicMock()
        mock_game_context.save_plugin = mock_save_plugin

        mock_old_view = MagicMock()
        mock_new_view = MagicMock()
        mock_game_view_class.side_effect = [mock_old_view, mock_new_view]

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()
        # Create existing view
        _ = game.game_view

        mock_save_data = MagicMock()
        game.load_game(mock_save_data)

        # Verify old view was cleaned up
        mock_old_view.cleanup.assert_called_once()

        # Verify new view was created
        assert mock_game_view_class.call_count == 2

    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    def test_load_game_no_save_plugin(
        self,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
    ) -> None:
        """Test load_game does nothing when no save plugin."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_context = MagicMock()
        mock_game_context_class.return_value = mock_game_context
        mock_game_context.save_plugin = None

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()

        mock_save_data = MagicMock()
        game.load_game(mock_save_data)

        # Window show_view should not be called
        self.mock_window.show_view.assert_not_called()

    @patch("pedre.game.arcade.close_window")
    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    @patch("pedre.game.GameView")
    def test_exit_game_with_view(
        self,
        mock_game_view_class: MagicMock,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
        mock_close_window: MagicMock,
    ) -> None:
        """Test exit_game saves and cleans up before exiting."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_context = MagicMock()
        mock_game_context_class.return_value = mock_game_context

        mock_save_plugin = MagicMock()
        mock_save_plugin.auto_save.return_value = True
        mock_game_context.save_plugin = mock_save_plugin

        mock_game_view = MagicMock()
        mock_game_view_class.return_value = mock_game_view

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()
        # Create view
        _ = game.game_view

        game.exit_game()

        # Verify autosave was called
        mock_save_plugin.auto_save.assert_called_once()

        # Verify cleanup was called
        mock_game_view.cleanup.assert_called_once()

        # Verify window was closed
        mock_close_window.assert_called_once()

    @patch("pedre.game.arcade.close_window")
    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    @patch("pedre.game.GameView")
    def test_exit_game_autosave_fails(
        self,
        mock_game_view_class: MagicMock,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
        mock_close_window: MagicMock,
    ) -> None:
        """Test exit_game continues even if autosave fails."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        mock_game_context = MagicMock()
        mock_game_context_class.return_value = mock_game_context

        mock_save_plugin = MagicMock()
        mock_save_plugin.auto_save.return_value = False
        mock_game_context.save_plugin = mock_save_plugin

        mock_game_view = MagicMock()
        mock_game_view_class.return_value = mock_game_view

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()
        # Create view
        _ = game.game_view

        game.exit_game()

        # Verify autosave was attempted
        mock_save_plugin.auto_save.assert_called_once()

        # Verify cleanup and close still happened
        mock_game_view.cleanup.assert_called_once()
        mock_close_window.assert_called_once()

    @patch("pedre.game.arcade.close_window")
    @patch("pedre.game.PluginLoader")
    @patch("pedre.game.ConditionLoader")
    @patch("pedre.game.EventLoader")
    @patch("pedre.game.ActionLoader")
    @patch("pedre.game.GameContext")
    @patch("pedre.game.EventBus")
    def test_exit_game_without_view(
        self,
        mock_event_bus_class: MagicMock,
        mock_game_context_class: MagicMock,
        mock_action_loader_class: MagicMock,
        mock_event_loader_class: MagicMock,
        mock_condition_loader_class: MagicMock,
        mock_plugin_loader_class: MagicMock,
        mock_close_window: MagicMock,
    ) -> None:
        """Test exit_game without active view just closes window."""
        mock_plugin_loader = MagicMock()
        mock_plugin_loader.instantiate_all.return_value = {}
        mock_plugin_loader_class.return_value = mock_plugin_loader

        game = Game(self.mock_window)

        # Verify all loaders were called during init
        mock_event_bus_class.assert_called_once()
        mock_game_context_class.assert_called_once()
        mock_action_loader_class.assert_called_once()
        mock_event_loader_class.assert_called_once()
        mock_condition_loader_class.assert_called_once()
        mock_plugin_loader_class.assert_called_once()
        game.exit_game()

        # Verify window was closed
        mock_close_window.assert_called_once()


if __name__ == "__main__":
    unittest.main()
