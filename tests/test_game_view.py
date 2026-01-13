"""Tests for GameView."""

from unittest.mock import Mock

import arcade
import pytest

from pedre.view_manager import ViewManager
from pedre.views.game_view import GameView


@pytest.fixture
def mock_view_manager(headless_window: arcade.Window) -> Mock:
    """Create a mock ViewManager.

    Args:
        headless_window: Headless window fixture.

    Returns:
        Mock ViewManager.
    """
    manager = Mock(spec=ViewManager)
    manager.window = headless_window
    return manager


@pytest.fixture
def game_view(mock_view_manager: Mock) -> GameView:
    """Create a GameView instance.

    Args:
        mock_view_manager: Mock ViewManager fixture.

    Returns:
        GameView instance.
    """
    return GameView(mock_view_manager)


def test_game_view_initialization(game_view: GameView, mock_view_manager: Mock) -> None:
    """Test that GameView initializes correctly.

    Args:
        game_view: GameView fixture.
        mock_view_manager: Mock ViewManager fixture.
    """
    assert game_view.view_manager == mock_view_manager


def test_on_key_press_escape_returns_to_menu(
    game_view: GameView,
    mock_view_manager: Mock,
) -> None:
    """Test that ESC key returns to menu.

    Args:
        game_view: GameView fixture.
        mock_view_manager: Mock ViewManager fixture.
    """
    result = game_view.on_key_press(arcade.key.ESCAPE, 0)
    mock_view_manager.show_menu.assert_called_once()
    assert result is None


def test_on_key_press_other_keys_do_nothing(
    game_view: GameView,
    mock_view_manager: Mock,
) -> None:
    """Test that other keys don't trigger menu return.

    Args:
        game_view: GameView fixture.
        mock_view_manager: Mock ViewManager fixture.
    """
    # Test various keys
    for key in [arcade.key.SPACE, arcade.key.ENTER, arcade.key.A, arcade.key.UP]:
        result = game_view.on_key_press(key, 0)
        assert result is None

    # show_menu should not have been called
    mock_view_manager.show_menu.assert_not_called()
