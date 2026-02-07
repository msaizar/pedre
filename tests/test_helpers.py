"""Unit tests for helper functions in src/pedre/helpers.py."""

import logging
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import arcade

from pedre.helpers import (
    calculate_responsive_value,
    compute_ui_scale,
    create_game,
    get_app_data_dir,
    matches_key,
    run_game,
    scale,
    scale_font,
    setup_logging,
    setup_resources,
)


class TestSetupLogging(unittest.TestCase):
    """Test Suite for setup_logging function."""

    @patch("pedre.helpers.logging.basicConfig")
    def test_setup_logging_default_debug(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with default DEBUG level."""
        setup_logging()

        mock_basic_config.assert_called_once()
        _args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.DEBUG
        assert kwargs["format"] == "%(message)s"
        assert len(kwargs["handlers"]) == 1

    @patch("pedre.helpers.logging.basicConfig")
    def test_setup_logging_info_level(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with INFO level."""
        setup_logging("INFO")

        mock_basic_config.assert_called_once()
        _args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.INFO

    @patch("pedre.helpers.logging.basicConfig")
    def test_setup_logging_warning_level(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with WARNING level."""
        setup_logging("WARNING")

        mock_basic_config.assert_called_once()
        _args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.WARNING

    @patch("pedre.helpers.logging.basicConfig")
    def test_setup_logging_error_level(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with ERROR level."""
        setup_logging("ERROR")

        mock_basic_config.assert_called_once()
        _args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.ERROR

    @patch("pedre.helpers.logging.basicConfig")
    def test_setup_logging_critical_level(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging with CRITICAL level."""
        setup_logging("CRITICAL")

        mock_basic_config.assert_called_once()
        _args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.CRITICAL

    @patch("pedre.helpers.logging.basicConfig")
    def test_setup_logging_lowercase_level(self, mock_basic_config: MagicMock) -> None:
        """Test setup_logging converts lowercase to uppercase."""
        setup_logging("info")

        mock_basic_config.assert_called_once()
        _args, kwargs = mock_basic_config.call_args
        assert kwargs["level"] == logging.INFO


class TestGetAppDataDir(unittest.TestCase):
    """Test Suite for get_app_data_dir function."""

    @patch("pedre.helpers.Path.cwd")
    @patch.object(sys, "frozen", new=False, create=True)
    def test_get_app_data_dir_not_frozen(self, mock_cwd: MagicMock) -> None:
        """Test get_app_data_dir when not running from PyInstaller bundle."""
        mock_cwd.return_value = Path("/path/to/project")

        result = get_app_data_dir()

        assert result == Path("/path/to/project")
        mock_cwd.assert_called_once()

    @patch("pedre.helpers.Path.cwd")
    @patch.object(sys, "frozen", new=False, create=True)
    def test_get_app_data_dir_not_frozen_with_subdir(self, mock_cwd: MagicMock) -> None:
        """Test get_app_data_dir with subdirectory when not frozen."""
        mock_cwd.return_value = Path("/path/to/project")

        result = get_app_data_dir("saves")

        assert result == Path("/path/to/project/saves")

    @patch("pedre.helpers.user_data_dir")
    @patch("pedre.helpers.settings")
    @patch.object(sys, "frozen", new=True, create=True)
    def test_get_app_data_dir_frozen(self, mock_settings: MagicMock, mock_user_data_dir: MagicMock) -> None:
        """Test get_app_data_dir when running from PyInstaller bundle."""
        mock_settings.WINDOW_TITLE = "My Game"
        mock_user_data_dir.return_value = "/Users/username/Library/Application Support/MyGame"

        result = get_app_data_dir()

        assert result == Path("/Users/username/Library/Application Support/MyGame")
        mock_user_data_dir.assert_called_once_with("MyGame", appauthor=False)

    @patch("pedre.helpers.user_data_dir")
    @patch("pedre.helpers.settings")
    @patch.object(sys, "frozen", new=True, create=True)
    def test_get_app_data_dir_frozen_with_subdir(self, mock_settings: MagicMock, mock_user_data_dir: MagicMock) -> None:
        """Test get_app_data_dir with subdirectory when frozen."""
        mock_settings.WINDOW_TITLE = "My Game"
        mock_user_data_dir.return_value = "/Users/username/Library/Application Support/MyGame"

        result = get_app_data_dir("saves")

        assert result == Path("/Users/username/Library/Application Support/MyGame/saves")

    @patch("pedre.helpers.user_data_dir")
    @patch("pedre.helpers.settings")
    @patch.object(sys, "frozen", new=True, create=True)
    def test_get_app_data_dir_sanitizes_title_with_spaces(
        self, mock_settings: MagicMock, mock_user_data_dir: MagicMock
    ) -> None:
        """Test that WINDOW_TITLE with spaces is sanitized."""
        mock_settings.WINDOW_TITLE = "My Cool Game"
        mock_user_data_dir.return_value = "/data/MyCoolGame"

        get_app_data_dir()

        mock_user_data_dir.assert_called_once_with("MyCoolGame", appauthor=False)

    @patch("pedre.helpers.user_data_dir")
    @patch("pedre.helpers.settings")
    @patch.object(sys, "frozen", new=True, create=True)
    def test_get_app_data_dir_sanitizes_title_with_slashes(
        self, mock_settings: MagicMock, mock_user_data_dir: MagicMock
    ) -> None:
        """Test that WINDOW_TITLE with slashes is sanitized."""
        mock_settings.WINDOW_TITLE = "Game/Version"
        mock_user_data_dir.return_value = "/data/Game-Version"

        get_app_data_dir()

        mock_user_data_dir.assert_called_once_with("Game-Version", appauthor=False)


class TestSetupResources(unittest.TestCase):
    """Test Suite for setup_resources function."""

    @patch("pedre.helpers.arcade.resources.add_resource_handle")
    @patch("pedre.helpers.Path.cwd")
    @patch("pedre.helpers.settings")
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

        setup_resources("game_assets")

        expected_path = Path("/path/to/project/assets").resolve()
        mock_add_resource_handle.assert_called_once_with("game_assets", expected_path)

    @patch("pedre.helpers.arcade.resources.add_resource_handle")
    @patch("pedre.helpers.settings")
    @patch.object(sys, "_MEIPASS", new="/var/app/_MEI12345", create=True)
    @patch.object(sys, "frozen", new=True, create=True)
    def test_setup_resources_frozen(self, mock_settings: MagicMock, mock_add_resource_handle: MagicMock) -> None:
        """Test setup_resources when running from PyInstaller bundle."""
        mock_settings.ASSETS_DIRECTORY = "assets"

        setup_resources("game_assets")

        expected_path = Path("/var/app/_MEI12345/assets").resolve()
        mock_add_resource_handle.assert_called_once_with("game_assets", expected_path)


class TestCreateGame(unittest.TestCase):
    """Test Suite for create_game function."""

    @patch("pedre.helpers.Game")
    @patch("pedre.helpers.arcade.Window")
    @patch("pedre.helpers.setup_resources")
    @patch("pedre.helpers.setup_logging")
    @patch("pedre.helpers.settings")
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
        mock_settings.ASSETS_HANDLE = "game_assets"

        mock_window = MagicMock()
        mock_window_class.return_value = mock_window

        mock_game = MagicMock()
        mock_game_class.return_value = mock_game

        result = create_game()

        # Verify setup functions were called
        mock_setup_logging.assert_called_once()
        mock_setup_resources.assert_called_once_with("game_assets")

        # Verify window was created with correct settings
        mock_window_class.assert_called_once_with(1920, 1080, "Test Game")

        # Verify game was created with window
        mock_game_class.assert_called_once_with(mock_window)

        # Verify game was attached to window
        assert mock_window.game == mock_game

        # Verify window is returned
        assert result == mock_window


class TestMatchesKey(unittest.TestCase):
    """Test Suite for matches_key function."""

    def test_matches_key_single_letter_match(self) -> None:
        """Test matches_key with matching single letter key."""
        assert matches_key(arcade.key.V, "V") is True

    def test_matches_key_single_letter_no_match(self) -> None:
        """Test matches_key with non-matching single letter key."""
        assert matches_key(arcade.key.C, "V") is False

    def test_matches_key_space(self) -> None:
        """Test matches_key with SPACE key."""
        assert matches_key(arcade.key.SPACE, "SPACE") is True

    def test_matches_key_lowercase_input(self) -> None:
        """Test matches_key converts lowercase to uppercase."""
        assert matches_key(arcade.key.V, "v") is True

    def test_matches_key_empty_string(self) -> None:
        """Test matches_key with empty string returns False."""
        assert matches_key(arcade.key.V, "") is False

    def test_matches_key_nonexistent_key(self) -> None:
        """Test matches_key with non-existent key name returns False."""
        assert matches_key(arcade.key.V, "NONEXISTENT") is False

    def test_matches_key_enter(self) -> None:
        """Test matches_key with ENTER key."""
        assert matches_key(arcade.key.ENTER, "ENTER") is True

    def test_matches_key_escape(self) -> None:
        """Test matches_key with ESCAPE key."""
        assert matches_key(arcade.key.ESCAPE, "ESCAPE") is True

    def test_matches_key_number(self) -> None:
        """Test matches_key with number key."""
        assert matches_key(arcade.key.NUM_1, "NUM_1") is True


class TestCalculateResponsiveValue(unittest.TestCase):
    """Test Suite for calculate_responsive_value function."""

    def test_calculate_responsive_value_in_range(self) -> None:
        """Test calculation within min/max bounds."""
        # 720 * 0.022 = 15.84, int() = 15, within [12, 32]
        result = calculate_responsive_value(720, 0.022, 12, 32)
        assert result == 15

    def test_calculate_responsive_value_hits_minimum(self) -> None:
        """Test calculation hits minimum bound."""
        # 100 * 0.022 = 2.2, int() = 2, clamped to min 12
        result = calculate_responsive_value(100, 0.022, 12, 32)
        assert result == 12

    def test_calculate_responsive_value_hits_maximum(self) -> None:
        """Test calculation hits maximum bound."""
        # 2160 * 0.022 = 47.52, int() = 47, clamped to max 32
        result = calculate_responsive_value(2160, 0.022, 12, 32)
        assert result == 32

    def test_calculate_responsive_value_exact_dimension(self) -> None:
        """Test with exact dimension calculations."""
        # 1000 * 0.05 = 50, within [10, 100]
        result = calculate_responsive_value(1000, 0.05, 10, 100)
        assert result == 50

    def test_calculate_responsive_value_zero_percent(self) -> None:
        """Test with zero percent."""
        result = calculate_responsive_value(720, 0.0, 12, 32)
        assert result == 12

    def test_calculate_responsive_value_100_percent(self) -> None:
        """Test with 100 percent."""
        result = calculate_responsive_value(100, 1.0, 12, 32)
        assert result == 32


class TestComputeUIScale(unittest.TestCase):
    """Test Suite for compute_ui_scale function."""

    def test_compute_ui_scale_same_as_reference(self) -> None:
        """Test when window size matches reference resolution."""
        result = compute_ui_scale(1280, 720, 1280, 720)
        assert result == 1.0

    def test_compute_ui_scale_double_reference(self) -> None:
        """Test when window is exactly double the reference."""
        result = compute_ui_scale(2560, 1440, 1280, 720)
        assert result == 2.0

    def test_compute_ui_scale_half_reference(self) -> None:
        """Test when window is exactly half the reference."""
        result = compute_ui_scale(640, 360, 1280, 720)
        assert result == 0.5

    def test_compute_ui_scale_uses_smaller_ratio(self) -> None:
        """Test that it uses the smaller of width/height ratios."""
        # Width ratio: 1920/1280 = 1.5
        # Height ratio: 1080/720 = 1.5
        result = compute_ui_scale(1920, 1080, 1280, 720)
        assert result == 1.5

    def test_compute_ui_scale_clamped_to_max(self) -> None:
        """Test that scale is clamped to maximum."""
        # 3840/1280 = 3.0, but max_scale=2.0
        result = compute_ui_scale(3840, 2160, 1280, 720, min_scale=0.5, max_scale=2.0)
        assert result == 2.0

    def test_compute_ui_scale_clamped_to_min(self) -> None:
        """Test that scale is clamped to minimum."""
        # 320/1280 = 0.25, but min_scale=0.5
        result = compute_ui_scale(320, 180, 1280, 720, min_scale=0.5, max_scale=2.0)
        assert result == 0.5

    @patch("pedre.helpers.settings")
    def test_compute_ui_scale_uses_settings_defaults(self, mock_settings: MagicMock) -> None:
        """Test that it uses settings for default reference resolution."""
        mock_settings.SCREEN_WIDTH = 1280
        mock_settings.SCREEN_HEIGHT = 720

        result = compute_ui_scale(1920, 1080)

        assert result == 1.5

    def test_compute_ui_scale_different_aspect_ratio(self) -> None:
        """Test with different aspect ratios."""
        # Width ratio: 1920/1280 = 1.5
        # Height ratio: 800/720 = 1.111
        # Should use smaller ratio (1.111)
        result = compute_ui_scale(1920, 800, 1280, 720)
        assert abs(result - 1.111) < 0.01


class TestScaleFont(unittest.TestCase):
    """Test Suite for scale_font function."""

    def test_scale_font_at_reference(self) -> None:
        """Test font scaling at reference scale (1.0)."""
        result = scale_font((8, 12, 16), 1.0)
        assert result == 12

    def test_scale_font_at_min_scale(self) -> None:
        """Test font scaling at minimum scale."""
        result = scale_font((8, 12, 16), 0.5)
        assert result == 8

    def test_scale_font_at_max_scale(self) -> None:
        """Test font scaling at maximum scale."""
        result = scale_font((8, 12, 16), 2.0)
        assert result == 16

    def test_scale_font_between_min_and_ref(self) -> None:
        """Test font scaling between min and reference."""
        # ui_scale = 0.75, halfway between 0.5 and 1.0
        # t = (0.75 - 0.5) / (1.0 - 0.5) = 0.5
        # result = 8 + (12 - 8) * 0.5 = 10
        result = scale_font((8, 12, 16), 0.75)
        assert result == 10

    def test_scale_font_between_ref_and_max(self) -> None:
        """Test font scaling between reference and max."""
        # ui_scale = 1.5, halfway between 1.0 and 2.0
        # t = (1.5 - 1.0) / (2.0 - 1.0) = 0.5
        # result = 12 + (16 - 12) * 0.5 = 14
        result = scale_font((8, 12, 16), 1.5)
        assert result == 14

    def test_scale_font_below_min_scale(self) -> None:
        """Test font scaling below minimum scale."""
        result = scale_font((8, 12, 16), 0.3)
        assert result == 8

    def test_scale_font_above_max_scale(self) -> None:
        """Test font scaling above maximum scale."""
        result = scale_font((8, 12, 16), 2.5)
        assert result == 16

    def test_scale_font_minimum_floor(self) -> None:
        """Test that font size is at least 1."""
        result = scale_font((0, 0, 0), 1.0)
        assert result == 1

    def test_scale_font_custom_min_max(self) -> None:
        """Test with custom min/max scale values."""
        # ui_scale = 1.5, min_scale = 1.0, max_scale = 3.0
        # Between ref and max: t = (1.5 - 1.0) / (3.0 - 1.0) = 0.25
        # result = 12 + (16 - 12) * 0.25 = 13
        result = scale_font((8, 12, 16), 1.5, min_scale=1.0, max_scale=3.0)
        assert result == 13


class TestRunGame(unittest.TestCase):
    """Test Suite for run_game function."""

    @patch("pedre.helpers.arcade.run")
    @patch("pedre.helpers.create_game")
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


class TestScale(unittest.TestCase):
    """Test Suite for scale function."""

    def test_scale_basic(self) -> None:
        """Test basic scaling."""
        result = scale(10, 1.5)
        assert result == 15

    def test_scale_with_floor(self) -> None:
        """Test scaling respects floor value."""
        result = scale(2, 0.3, floor=1)
        # 2 * 0.3 = 0.6, int() = 0, but floor is 1
        assert result == 1

    def test_scale_default_floor(self) -> None:
        """Test default floor is 1."""
        result = scale(1, 0.5)
        # 1 * 0.5 = 0.5, int() = 0, floor to 1
        assert result == 1

    def test_scale_custom_floor(self) -> None:
        """Test with custom floor value."""
        result = scale(10, 0.5, floor=10)
        # 10 * 0.5 = 5, int() = 5, but floor is 10
        assert result == 10

    def test_scale_no_floor_needed(self) -> None:
        """Test when result is above floor."""
        result = scale(100, 2.0, floor=10)
        assert result == 200

    def test_scale_exact_integer(self) -> None:
        """Test when scale results in exact integer."""
        result = scale(10, 2.0)
        assert result == 20

    def test_scale_truncates_decimal(self) -> None:
        """Test that decimal values are truncated."""
        result = scale(10, 1.99, floor=1)
        # 10 * 1.99 = 19.9, int() = 19
        assert result == 19


if __name__ == "__main__":
    unittest.main()
