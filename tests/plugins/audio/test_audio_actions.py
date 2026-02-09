"""Unit tests for audio action classes."""

import unittest
from unittest.mock import MagicMock

from pedre.plugins.audio.actions import PlayMusicAction, PlaySFXAction


class TestPlaySFXAction(unittest.TestCase):
    """Unit test class for PlaySFXAction."""

    def test_init(self) -> None:
        """Test PlaySFXAction initialization."""
        action = PlaySFXAction("test.wav")

        assert action.sfx_file == "test.wav"
        assert action.executed is False

    def test_execute_plays_sfx(self) -> None:
        """Test that execute plays the sound effect."""
        action = PlaySFXAction("door_open.wav")

        # Create mock context with audio plugin
        mock_context = MagicMock()
        mock_audio_plugin = MagicMock()
        mock_context.audio_plugin = mock_audio_plugin

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_audio_plugin.play_sfx.assert_called_once_with("door_open.wav")
        assert action.executed is True

    def test_execute_only_once(self) -> None:
        """Test that execute only plays SFX once."""
        action = PlaySFXAction("test.wav")

        # Create mock context
        mock_context = MagicMock()
        mock_audio_plugin = MagicMock()
        mock_context.audio_plugin = mock_audio_plugin

        # Execute multiple times
        action.execute(mock_context)
        action.execute(mock_context)
        action.execute(mock_context)

        # Should only play once
        mock_audio_plugin.play_sfx.assert_called_once()

    def test_reset(self) -> None:
        """Test that reset allows re-execution."""
        action = PlaySFXAction("test.wav")

        # Create mock context
        mock_context = MagicMock()
        mock_audio_plugin = MagicMock()
        mock_context.audio_plugin = mock_audio_plugin

        # Execute, reset, execute again
        action.execute(mock_context)
        assert action.executed is True

        action.reset()
        assert action.executed is False

        action.execute(mock_context)

        # Should have been called twice (once before reset, once after)
        assert mock_audio_plugin.play_sfx.call_count == 2

    def test_from_dict(self) -> None:
        """Test creating PlaySFXAction from dictionary."""
        data = {"file": "footstep.mp3"}

        action = PlaySFXAction.from_dict(data)

        assert isinstance(action, PlaySFXAction)
        assert action.sfx_file == "footstep.mp3"

    def test_from_dict_missing_file(self) -> None:
        """Test creating PlaySFXAction with missing file key."""
        data = {}

        action = PlaySFXAction.from_dict(data)

        assert isinstance(action, PlaySFXAction)
        assert action.sfx_file == ""

    def test_from_dict_with_extra_keys(self) -> None:
        """Test that from_dict ignores extra keys."""
        data = {"file": "test.wav", "volume": 0.5, "extra_key": "ignored"}

        action = PlaySFXAction.from_dict(data)

        assert action.sfx_file == "test.wav"


class TestPlayMusicAction(unittest.TestCase):
    """Unit test class for PlayMusicAction."""

    def test_init_defaults(self) -> None:
        """Test PlayMusicAction initialization with defaults."""
        action = PlayMusicAction("theme.ogg")

        assert action.music_file == "theme.ogg"
        assert action.loop is True
        assert action.volume is None
        assert action.executed is False

    def test_init_with_parameters(self) -> None:
        """Test PlayMusicAction initialization with custom parameters."""
        action = PlayMusicAction("victory.ogg", loop=False, volume=0.8)

        assert action.music_file == "victory.ogg"
        assert action.loop is False
        assert action.volume == 0.8
        assert action.executed is False

    def test_execute_plays_music(self) -> None:
        """Test that execute plays the music."""
        action = PlayMusicAction("town_theme.ogg")

        # Create mock context with audio plugin
        mock_context = MagicMock()
        mock_audio_plugin = MagicMock()
        mock_context.audio_plugin = mock_audio_plugin

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_audio_plugin.play_music.assert_called_once_with("town_theme.ogg", loop=True, volume=None)
        assert action.executed is True

    def test_execute_with_custom_parameters(self) -> None:
        """Test execute with custom loop and volume parameters."""
        action = PlayMusicAction("fanfare.ogg", loop=False, volume=0.7)

        # Create mock context
        mock_context = MagicMock()
        mock_audio_plugin = MagicMock()
        mock_context.audio_plugin = mock_audio_plugin

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_audio_plugin.play_music.assert_called_once_with("fanfare.ogg", loop=False, volume=0.7)

    def test_execute_only_once(self) -> None:
        """Test that execute only plays music once."""
        action = PlayMusicAction("test.ogg")

        # Create mock context
        mock_context = MagicMock()
        mock_audio_plugin = MagicMock()
        mock_context.audio_plugin = mock_audio_plugin

        # Execute multiple times
        action.execute(mock_context)
        action.execute(mock_context)
        action.execute(mock_context)

        # Should only play once
        mock_audio_plugin.play_music.assert_called_once()

    def test_reset(self) -> None:
        """Test that reset allows re-execution."""
        action = PlayMusicAction("test.ogg")

        # Create mock context
        mock_context = MagicMock()
        mock_audio_plugin = MagicMock()
        mock_context.audio_plugin = mock_audio_plugin

        # Execute, reset, execute again
        action.execute(mock_context)
        assert action.executed is True

        action.reset()
        assert action.executed is False

        action.execute(mock_context)

        # Should have been called twice (once before reset, once after)
        assert mock_audio_plugin.play_music.call_count == 2

    def test_from_dict_defaults(self) -> None:
        """Test creating PlayMusicAction from dictionary with defaults."""
        data = {"file": "background.ogg"}

        action = PlayMusicAction.from_dict(data)

        assert isinstance(action, PlayMusicAction)
        assert action.music_file == "background.ogg"
        assert action.loop is True
        assert action.volume is None

    def test_from_dict_with_all_parameters(self) -> None:
        """Test creating PlayMusicAction with all parameters."""
        data = {"file": "battle.ogg", "loop": False, "volume": 0.5}

        action = PlayMusicAction.from_dict(data)

        assert isinstance(action, PlayMusicAction)
        assert action.music_file == "battle.ogg"
        assert action.loop is False
        assert action.volume == 0.5

    def test_from_dict_missing_file(self) -> None:
        """Test creating PlayMusicAction with missing file key."""
        data = {"loop": True}

        action = PlayMusicAction.from_dict(data)

        assert isinstance(action, PlayMusicAction)
        assert action.music_file == ""
        assert action.loop is True

    def test_from_dict_with_extra_keys(self) -> None:
        """Test that from_dict ignores extra keys."""
        data = {
            "file": "test.ogg",
            "loop": False,
            "volume": 0.8,
            "extra_key": "ignored",
        }

        action = PlayMusicAction.from_dict(data)

        assert action.music_file == "test.ogg"
        assert action.loop is False
        assert action.volume == 0.8

    def test_from_dict_with_explicit_loop_false(self) -> None:
        """Test that loop=false is properly handled."""
        data = {"file": "oneshot.ogg", "loop": False}

        action = PlayMusicAction.from_dict(data)

        assert action.loop is False

    def test_from_dict_with_explicit_loop_true(self) -> None:
        """Test that loop=true is properly handled."""
        data = {"file": "ambient.ogg", "loop": True}

        action = PlayMusicAction.from_dict(data)

        assert action.loop is True

    def test_volume_can_be_zero(self) -> None:
        """Test that volume of 0.0 is valid."""
        action = PlayMusicAction("silent.ogg", volume=0.0)

        assert action.volume == 0.0

        # Test from_dict as well
        data = {"file": "silent.ogg", "volume": 0.0}
        action2 = PlayMusicAction.from_dict(data)

        assert action2.volume == 0.0

    def test_volume_can_be_one(self) -> None:
        """Test that volume of 1.0 is valid."""
        action = PlayMusicAction("loud.ogg", volume=1.0)

        assert action.volume == 1.0


class TestPlaySFXActionValidation(unittest.TestCase):
    """Test PlaySFXAction validation."""

    def test_validate_params_success(self) -> None:
        """Test validate_params with valid data."""
        data = {"file": "sound.wav"}
        errors = PlaySFXAction.validate_params(data)
        assert errors == []

    def test_validate_params_missing_file(self) -> None:
        """Test validate_params detects missing file field."""
        data = {}
        errors = PlaySFXAction.validate_params(data)
        assert len(errors) == 1
        assert "missing required 'file' field" in errors[0]

    def test_validate_params_empty_file(self) -> None:
        """Test validate_params detects empty file field."""
        data = {"file": ""}
        errors = PlaySFXAction.validate_params(data)
        assert len(errors) == 1
        assert "missing required 'file' field" in errors[0]


class TestPlayMusicActionValidation(unittest.TestCase):
    """Test PlayMusicAction validation."""

    def test_validate_params_success(self) -> None:
        """Test validate_params with valid data."""
        data = {"file": "music.ogg"}
        errors = PlayMusicAction.validate_params(data)
        assert errors == []

    def test_validate_params_missing_file(self) -> None:
        """Test validate_params detects missing file field."""
        data = {}
        errors = PlayMusicAction.validate_params(data)
        assert len(errors) == 1
        assert "missing required 'file' field" in errors[0]

    def test_validate_params_empty_file(self) -> None:
        """Test validate_params detects empty file field."""
        data = {"file": ""}
        errors = PlayMusicAction.validate_params(data)
        assert len(errors) == 1
        assert "missing required 'file' field" in errors[0]


if __name__ == "__main__":
    unittest.main()
