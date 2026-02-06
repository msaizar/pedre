"""Tests for GameView."""

from unittest.mock import Mock

import arcade
import pytest

from pedre.game import Game
from pedre.views.game_view import GameView


@pytest.fixture
def mock_game(headless_window: arcade.Window) -> Mock:
    """Create a mock Game coordinator.

    Args:
        headless_window: Headless window fixture.

    Returns:
        Mock Game coordinator.
    """
    game = Mock(spec=Game)
    game.window = headless_window
    game.plugin_loader = Mock()
    game.game_context = Mock()
    return game


@pytest.fixture
def game_view(mock_game: Mock) -> GameView:
    """Create a GameView instance.

    Args:
        mock_game: Mock Game coordinator fixture.

    Returns:
        GameView instance.
    """
    return GameView(mock_game)


@pytest.mark.window
def test_game_view_initialization(game_view: GameView, mock_game: Mock) -> None:
    """Test that GameView initializes correctly.

    Args:
        game_view: GameView fixture.
        mock_game: Mock Game coordinator fixture.
    """
    assert game_view.game == mock_game


@pytest.mark.window
def test_on_key_press_other_keys_do_nothing(
    game_view: GameView,
    mock_game: Mock,
) -> None:
    """Test that other keys don't trigger menu return.

    Args:
        game_view: GameView fixture.
        mock_game: Mock Game coordinator fixture.
    """
    # Test various keys
    mock_game.plugin_loader.on_key_press_all.return_value = False
    for key in [arcade.key.SPACE, arcade.key.ENTER, arcade.key.A, arcade.key.UP]:
        result = game_view.on_key_press(key, 0)
        assert result is None
