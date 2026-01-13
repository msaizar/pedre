"""Tests for ViewManager."""

from unittest.mock import Mock

import arcade
import pytest

from pedre.view_manager import ViewManager
from pedre.views.game_view import GameView
from pedre.views.menu_view import MenuView


@pytest.fixture
def view_manager(headless_window: arcade.Window) -> ViewManager:
    """Create a ViewManager instance with a headless window.

    Args:
        headless_window: Headless window fixture.

    Returns:
        ViewManager instance.
    """
    return ViewManager(headless_window)


def test_view_manager_initialization(
    view_manager: ViewManager,
    headless_window: arcade.Window,
) -> None:
    """Test that ViewManager initializes correctly.

    Args:
        view_manager: ViewManager fixture.
        headless_window: Headless window fixture.
    """
    assert view_manager.window == headless_window
    assert isinstance(view_manager.menu_view, MenuView)
    assert isinstance(view_manager.game_view, GameView)


def test_view_manager_creates_views_with_self_reference(view_manager: ViewManager) -> None:
    """Test that views are created with reference to ViewManager.

    Args:
        view_manager: ViewManager fixture.
    """
    assert view_manager.menu_view.view_manager == view_manager
    assert view_manager.game_view.view_manager == view_manager


def test_show_menu(view_manager: ViewManager, headless_window: arcade.Window) -> None:
    """Test that show_menu switches to menu view.

    Args:
        view_manager: ViewManager fixture.
        headless_window: Headless window fixture.
    """
    view_manager.show_menu()
    assert headless_window.current_view == view_manager.menu_view


def test_show_game(
    view_manager: ViewManager,
    headless_window: arcade.Window,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test that show_game switches to game view.

    Args:
        view_manager: ViewManager fixture.
        headless_window: Headless window fixture.
        monkeypatch: Pytest monkeypatch fixture.
    """
    # Mock the setup method to avoid loading map assets
    mock_setup = Mock()
    monkeypatch.setattr(view_manager.game_view, "setup", mock_setup)

    view_manager.show_game()
    assert headless_window.current_view == view_manager.game_view


def test_exit_game(view_manager: ViewManager, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that exit_game closes the window.

    Args:
        view_manager: ViewManager fixture.
        monkeypatch: Pytest monkeypatch fixture.
    """
    mock_close = Mock()
    monkeypatch.setattr(arcade, "close_window", mock_close)

    view_manager.exit_game()

    mock_close.assert_called_once()


def test_views_are_reused(view_manager: ViewManager, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that views are created once and reused.

    Args:
        view_manager: ViewManager fixture.
        monkeypatch: Pytest monkeypatch fixture.
    """
    # Mock the setup method to avoid loading map assets
    mock_setup = Mock()
    monkeypatch.setattr(view_manager.game_view, "setup", mock_setup)

    # Store references to original views
    original_menu_view = view_manager.menu_view
    original_game_view = view_manager.game_view

    # Switch views multiple times
    view_manager.show_menu()
    view_manager.show_game()
    view_manager.show_menu()

    # Views should be the same instances
    assert view_manager.menu_view is original_menu_view
    assert view_manager.game_view is original_game_view
