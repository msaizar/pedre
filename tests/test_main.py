"""Unit tests for main game functions in src/pedre/main.py."""

import logging
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import arcade

from pedre.conf import settings
from pedre.main import create_game, run_game, setup_logging, setup_resources


class TestRunGame(unittest.TestCase):
    """Test Suite for run_game function."""

    @patch("pedre.main.arcade.run")
    @patch("pedre.main.create_game")
    def test_run_game(self, mock_create_game: MagicMock, mock_arcade_run: MagicMock) -> None:
        """Test run_game creates game, starts it, and runs arcade loop."""
        mock_window = MagicMock(spec=arcade.Window)
        mock_game = MagicMock()
        mock_window.game = mock_game
        mock_create_game.return_value = mock_window

        run_game()

        # Verify game was created
        mock_create_game.assert_called_once()

        # Verify game was started
        mock_game.start_game_or_load.assert_called_once()

        # Verify arcade.run() was called
        mock_arcade_run.assert_called_once()


class TestSetupLogging(unittest.TestCase):
    """Test Suite for setup_logging function."""

    @patch("pedre.main.logging.basicConfig")
    def test_setup_logging_default_debug(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with default DEBUG level."""
        setup_logging()

        mock_basic_config.assert_called_once()
        _args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.DEBUG
        assert kwargs["format"] == "%(message)s"
        assert len(kwargs["handlers"]) == 1

    @patch("pedre.main.logging.basicConfig")
    def test_setup_logging_info_level(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with INFO level."""
        setup_logging("INFO")

        mock_basic_config.assert_called_once()
        _args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.INFO

    @patch("pedre.main.logging.basicConfig")
    def test_setup_logging_warning_level(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with WARNING level."""
        setup_logging("WARNING")

        mock_basic_config.assert_called_once()
        _args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.WARNING

    @patch("pedre.main.logging.basicConfig")
    def test_setup_logging_error_level(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with ERROR level."""
        setup_logging("ERROR")

        mock_basic_config.assert_called_once()
        _args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.ERROR

    @patch("pedre.main.logging.basicConfig")
    def test_setup_logging_critical_level(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with CRITICAL level."""
        setup_logging("CRITICAL")

        mock_basic_config.assert_called_once()
        _args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.CRITICAL

    @patch("pedre.main.logging.basicConfig")
    def test_setup_logging_lowercase_level(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging converts lowercase to uppercase."""
        setup_logging("info")

        mock_basic_config.assert_called_once()
        _args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.INFO


class TestSetupResources(unittest.TestCase):
    """Test Suite for setup_resources function."""

    @patch("pedre.main.arcade.resources.add_resource_handle")
    @patch("pedre.main.Path.cwd")
    @patch("pedre.main.settings")
    @patch.object(sys, "frozen", new=False, create=True)
    def test_setup_resources_not_frozen(
        self,
        mock_settings: MagicMock,
        mock_cwd: MagicMock,
        mock_add_resource_handle: MagicMock,
    ) -> None:
        """Test setup_resources when not running from PyInstaller bundle."""
        mock_settings.ASSETS_DIRECTORY = "assets"
        mock_cwd.return_value = Path("/path/to/project")

        setup_resources(settings.ASSETS_HANDLE)

        expected_path = Path("/path/to/project/assets").resolve()
        mock_add_resource_handle.assert_called_once_with(settings.ASSETS_HANDLE, expected_path)

    @patch("pedre.main.arcade.resources.add_resource_handle")
    @patch("pedre.main.settings")
    @patch.object(sys, "_MEIPASS", new="/var/app/_MEI12345", create=True)
    @patch.object(sys, "frozen", new=True, create=True)
    def test_setup_resources_frozen(self, mock_settings: MagicMock, mock_add_resource_handle: MagicMock) -> None:
        """Test setup_resources when running from PyInstaller bundle."""
        mock_settings.ASSETS_DIRECTORY = "assets"

        setup_resources(settings.ASSETS_HANDLE)

        expected_path = Path("/var/app/_MEI12345/assets").resolve()
        mock_add_resource_handle.assert_called_once_with(settings.ASSETS_HANDLE, expected_path)


class TestCreateGame(unittest.TestCase):
    """Test Suite for create_game function."""

    @patch("pedre.main.Game")
    @patch("pedre.main.arcade.Window")
    @patch("pedre.main.setup_resources")
    @patch("pedre.main.setup_logging")
    @patch("pedre.main.settings")
    def test_create_game(
        self,
        mock_settings: MagicMock,
        mock_setup_logging: MagicMock,
        mock_setup_resources: MagicMock,
        mock_window_class: MagicMock,
        mock_game_class: MagicMock,
    ) -> None:
        """Test create_game creates window and attaches game."""
        mock_settings.SCREEN_WIDTH = 1920
        mock_settings.SCREEN_HEIGHT = 1080
        mock_settings.WINDOW_TITLE = "Test Game"
        mock_settings.ASSETS_HANDLE = "assets"

        mock_window = MagicMock()
        mock_window_class.return_value = mock_window

        mock_game = MagicMock()
        mock_game_class.return_value = mock_game

        result = create_game()

        # Verify setup functions were called
        mock_setup_logging.assert_called_once()
        mock_setup_resources.assert_called_once_with("assets")

        # Verify window was created with correct settings
        mock_window_class.assert_called_once_with(1920, 1080, "Test Game")

        # Verify game was created with window
        mock_game_class.assert_called_once_with(mock_window)

        # Verify game was attached to window
        assert mock_window.game == mock_game

        # Verify window is returned
        assert result == mock_window
