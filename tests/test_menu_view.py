"""Tests for MenuView."""

from unittest.mock import Mock

import arcade
import pytest

from pedre.types import MenuOption
from pedre.view_manager import ViewManager
from pedre.views.menu_view import MenuView


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
def menu_view(mock_view_manager: Mock) -> MenuView:
    """Create a MenuView instance.

    Args:
        mock_view_manager: Mock ViewManager fixture.

    Returns:
        MenuView instance.
    """
    return MenuView(mock_view_manager)


def test_menu_view_initialization(menu_view: MenuView) -> None:
    """Test that MenuView initializes with correct defaults.

    Args:
        menu_view: MenuView fixture.
    """
    assert menu_view.selected_option == MenuOption.CONTINUE
    assert menu_view.menu_enabled[MenuOption.CONTINUE] is False  # Initially disabled, updated on show
    assert menu_view.menu_enabled[MenuOption.NEW_GAME] is True
    assert menu_view.menu_enabled[MenuOption.LOAD_GAME] is True
    assert menu_view.menu_enabled[MenuOption.EXIT] is True


def test_menu_view_has_view_manager_reference(
    menu_view: MenuView,
    mock_view_manager: Mock,
) -> None:
    """Test that MenuView stores ViewManager reference.

    Args:
        menu_view: MenuView fixture.
        mock_view_manager: Mock ViewManager fixture.
    """
    assert menu_view.view_manager == mock_view_manager


def test_move_selection_down(menu_view: MenuView) -> None:
    """Test moving selection down through menu options.

    Args:
        menu_view: MenuView fixture.
    """
    # Start at CONTINUE (default), but it's disabled
    assert menu_view.selected_option == MenuOption.CONTINUE

    # Move down, should skip CONTINUE (disabled) and go to NEW_GAME
    menu_view._move_selection(1)
    assert menu_view.selected_option == MenuOption.NEW_GAME


def test_move_selection_up(menu_view: MenuView) -> None:
    """Test moving selection up through menu options.

    Args:
        menu_view: MenuView fixture.
    """
    # Start at NEW_GAME
    menu_view.selected_option = MenuOption.NEW_GAME

    # Move up, should wrap to EXIT (skipping LOAD_GAME)
    menu_view._move_selection(-1)
    assert menu_view.selected_option == MenuOption.EXIT


def test_move_selection_wraps_around(menu_view: MenuView) -> None:
    """Test that selection wraps around the menu.

    Args:
        menu_view: MenuView fixture.
    """
    # Start at EXIT
    menu_view.selected_option = MenuOption.EXIT

    # Move down, should wrap to NEW_GAME
    menu_view._move_selection(1)
    assert menu_view.selected_option == MenuOption.NEW_GAME


def test_move_selection_skips_disabled_options(menu_view: MenuView) -> None:
    """Test that navigation skips disabled options.

    Args:
        menu_view: MenuView fixture.
    """
    # Disable SAVE_GAME to test skipping
    menu_view.menu_enabled[MenuOption.SAVE_GAME] = False

    # Start at NEW_GAME, move down
    menu_view.selected_option = MenuOption.NEW_GAME
    menu_view._move_selection(1)

    # Should skip SAVE_GAME (disabled) and go to LOAD_GAME
    assert menu_view.selected_option == MenuOption.LOAD_GAME


def test_on_key_press_up(menu_view: MenuView) -> None:
    """Test UP key moves selection up.

    Args:
        menu_view: MenuView fixture.
    """
    menu_view.selected_option = MenuOption.EXIT
    menu_view.on_key_press(arcade.key.UP, 0)
    assert menu_view.selected_option == MenuOption.LOAD_GAME


def test_on_key_press_down(menu_view: MenuView) -> None:
    """Test DOWN key moves selection down.

    Args:
        menu_view: MenuView fixture.
    """
    menu_view.selected_option = MenuOption.NEW_GAME
    menu_view.on_key_press(arcade.key.DOWN, 0)
    # Move down from NEW_GAME goes to SAVE_GAME (which is disabled by default) then LOAD_GAME
    assert menu_view.selected_option == MenuOption.LOAD_GAME


def test_on_key_press_enter_new_game(
    menu_view: MenuView,
    mock_view_manager: Mock,
) -> None:
    """Test ENTER on NEW_GAME calls show_game.

    Args:
        menu_view: MenuView fixture.
        mock_view_manager: Mock ViewManager fixture.
    """
    menu_view.selected_option = MenuOption.NEW_GAME
    menu_view.on_key_press(arcade.key.ENTER, 0)
    mock_view_manager.show_game.assert_called_once()


def test_on_key_press_enter_exit(menu_view: MenuView, mock_view_manager: Mock) -> None:
    """Test ENTER on EXIT calls exit_game.

    Args:
        menu_view: MenuView fixture.
        mock_view_manager: Mock ViewManager fixture.
    """
    menu_view.selected_option = MenuOption.EXIT
    menu_view.on_key_press(arcade.key.ENTER, 0)
    mock_view_manager.exit_game.assert_called_once()


def test_on_key_press_enter_disabled_option(
    menu_view: MenuView,
    mock_view_manager: Mock,
) -> None:
    """Test ENTER on disabled option does nothing.

    Args:
        menu_view: MenuView fixture.
        mock_view_manager: Mock ViewManager fixture.
    """
    # Use CONTINUE which is disabled by default
    menu_view.selected_option = MenuOption.CONTINUE
    menu_view.on_key_press(arcade.key.ENTER, 0)

    # Should not call any view manager methods
    mock_view_manager.show_game.assert_not_called()
    mock_view_manager.show_menu.assert_not_called()
    mock_view_manager.exit_game.assert_not_called()


def test_on_key_press_return_key_works(
    menu_view: MenuView,
    mock_view_manager: Mock,
) -> None:
    """Test RETURN key also triggers selection.

    Args:
        menu_view: MenuView fixture.
        mock_view_manager: Mock ViewManager fixture.
    """
    menu_view.selected_option = MenuOption.NEW_GAME
    menu_view.on_key_press(arcade.key.RETURN, 0)
    mock_view_manager.show_game.assert_called_once()


def test_execute_selection_new_game(menu_view: MenuView, mock_view_manager: Mock) -> None:
    """Test executing NEW_GAME selection.

    Args:
        menu_view: MenuView fixture.
        mock_view_manager: Mock ViewManager fixture.
    """
    menu_view.selected_option = MenuOption.NEW_GAME
    menu_view._execute_selection()
    mock_view_manager.show_game.assert_called_once()


def test_execute_selection_exit(menu_view: MenuView, mock_view_manager: Mock) -> None:
    """Test executing EXIT selection.

    Args:
        menu_view: MenuView fixture.
        mock_view_manager: Mock ViewManager fixture.
    """
    menu_view.selected_option = MenuOption.EXIT
    menu_view._execute_selection()
    mock_view_manager.exit_game.assert_called_once()


def test_execute_selection_disabled_does_nothing(
    menu_view: MenuView,
    mock_view_manager: Mock,
) -> None:
    """Test executing disabled option does nothing.

    Args:
        menu_view: MenuView fixture.
        mock_view_manager: Mock ViewManager fixture.
    """
    # Use CONTINUE which is disabled by default
    menu_view.selected_option = MenuOption.CONTINUE
    menu_view._execute_selection()

    # No view manager methods should be called
    mock_view_manager.show_game.assert_not_called()
    mock_view_manager.exit_game.assert_not_called()
