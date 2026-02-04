"""Unit tests for SavePlugin in src/pedre/plugins/save/plugin.py."""

import json
import unittest
from datetime import UTC
from unittest.mock import MagicMock, mock_open, patch

from pedre.plugins.save.base import GameSaveData
from pedre.plugins.save.plugin import SavePlugin


class TestSavePlugin(unittest.TestCase):
    """Test Suite for SavePlugin."""

    def setUp(self) -> None:
        """Set up the SavePlugin and mock context."""
        with patch("pedre.plugins.save.plugin.Path.mkdir"):
            self.plugin = SavePlugin()
        self.mock_context = MagicMock()

        # Mock dependent plugins
        self.mock_player_plugin = MagicMock()
        self.mock_scene_plugin = MagicMock()
        self.mock_audio_plugin = MagicMock()
        self.mock_cache_plugin = MagicMock()

        self.mock_context.player_plugin = self.mock_player_plugin
        self.mock_context.scene_plugin = self.mock_scene_plugin
        self.mock_context.audio_plugin = self.mock_audio_plugin
        self.mock_context.cache_plugin = self.mock_cache_plugin

        # Mock get_plugins to return a dictionary of plugins
        mock_plugin1 = MagicMock()
        mock_plugin1.name = "plugin1"
        mock_plugin1.get_save_state.return_value = {"key1": "value1"}

        mock_plugin2 = MagicMock()
        mock_plugin2.name = "plugin2"
        mock_plugin2.get_save_state.return_value = {"key2": "value2"}

        self.mock_context.get_plugins.return_value = {
            "plugin1": mock_plugin1,
            "plugin2": mock_plugin2,
        }

        self.plugin.setup(self.mock_context)

    def test_initialization(self) -> None:
        """Test proper initialization of the plugin."""
        with patch("pedre.plugins.save.plugin.Path.mkdir") as mock_mkdir:
            plugin = SavePlugin()
            assert plugin.name == "save"
            assert plugin.current_slot is None
            mock_mkdir.assert_called_once_with(exist_ok=True)

    def test_setup(self) -> None:
        """Test setup assigns context."""
        plugin = SavePlugin()
        mock_context = MagicMock()
        plugin.setup(mock_context)
        assert plugin.context == mock_context

    def test_cleanup(self) -> None:
        """Test cleanup does nothing gracefully."""
        self.plugin.cleanup()
        # Should not raise any exceptions

    @patch("pedre.plugins.save.plugin.matches_key")
    @patch("pedre.plugins.save.plugin.settings")
    def test_on_key_press_quick_save(self, mock_settings: MagicMock, mock_matches_key: MagicMock) -> None:
        """Test quick save key handling."""
        mock_settings.SAVE_QUICK_SAVE_KEY = "F5"
        mock_matches_key.side_effect = lambda _sym, key: key == "F5"

        with patch.object(self.plugin, "_handle_quick_save") as mock_handle:
            result = self.plugin.on_key_press(1, 0)
            mock_handle.assert_called_once()
            assert result is True

    @patch("pedre.plugins.save.plugin.matches_key")
    @patch("pedre.plugins.save.plugin.settings")
    def test_on_key_press_quick_load(self, mock_settings: MagicMock, mock_matches_key: MagicMock) -> None:
        """Test quick load key handling."""
        mock_settings.SAVE_QUICK_SAVE_KEY = "F5"
        mock_settings.SAVE_QUICK_LOAD_KEY = "F9"
        mock_matches_key.side_effect = lambda _sym, key: key == "F9"

        with patch.object(self.plugin, "_handle_quick_load") as mock_handle:
            result = self.plugin.on_key_press(1, 0)
            mock_handle.assert_called_once()
            assert result is True

    @patch("pedre.plugins.save.plugin.matches_key")
    def test_on_key_press_no_match(self, mock_matches_key: MagicMock) -> None:
        """Test key press returns False when no hotkey matches."""
        mock_matches_key.return_value = False
        result = self.plugin.on_key_press(1, 0)
        assert result is False

    @patch("pedre.plugins.save.plugin.settings")
    def test_handle_quick_save_success(self, mock_settings: MagicMock) -> None:
        """Test quick save handles success case."""
        mock_settings.SAVE_SFX_FILE = "save.wav"

        with patch.object(self.plugin, "auto_save", return_value=True):
            self.plugin._handle_quick_save()
            self.mock_audio_plugin.play_sfx.assert_called_once_with("save.wav")

    def test_handle_quick_save_failure(self) -> None:
        """Test quick save handles failure case."""
        with patch.object(self.plugin, "auto_save", return_value=False):
            self.plugin._handle_quick_save()
            self.mock_audio_plugin.play_sfx.assert_not_called()

    @patch("pedre.plugins.save.plugin.settings")
    def test_handle_quick_load_success(self, mock_settings: MagicMock) -> None:
        """Test quick load handles success case."""
        mock_settings.SAVE_SFX_FILE = "save.wav"
        mock_save_data = GameSaveData(save_states={"test": "data"})

        with (
            patch.object(self.plugin, "load_auto_save", return_value=mock_save_data),
            patch.object(self.plugin, "restore_game_data"),
        ):
            self.plugin._handle_quick_load()
            self.mock_audio_plugin.play_sfx.assert_called_once_with("save.wav")

    def test_handle_quick_load_no_save(self) -> None:
        """Test quick load handles missing save."""
        with patch.object(self.plugin, "load_auto_save", return_value=None):
            self.plugin._handle_quick_load()
            self.mock_audio_plugin.play_sfx.assert_not_called()

    @patch("pedre.plugins.save.plugin.datetime")
    def test_save_game_success(self, mock_datetime: MagicMock) -> None:
        """Test saving game successfully."""
        # Setup mock timestamp
        mock_now = MagicMock()
        mock_now.timestamp.return_value = 1234567890.0
        mock_datetime.now.return_value = mock_now
        mock_datetime.UTC = UTC

        # Mock player sprite
        mock_player = MagicMock()
        mock_player.center_x = 100.0
        mock_player.center_y = 200.0
        self.mock_player_plugin.get_player_sprite.return_value = mock_player

        # Mock current scene
        mock_scene = MagicMock()
        self.mock_scene_plugin.get_current_scene.return_value = mock_scene

        # Mock file operations
        m_open = mock_open()
        with patch("pedre.plugins.save.plugin.Path.open", m_open):
            result = self.plugin.save_game(slot=1)

        assert result is True
        assert self.plugin.current_slot == 1
        m_open.assert_called_once()
        self.mock_cache_plugin.cache_scene.assert_called_once_with(mock_scene)

        # Verify JSON was written with correct structure
        handle = m_open()
        written_calls = list(handle.write.call_args_list)
        assert len(written_calls) > 0

    def test_save_game_no_player_sprite(self) -> None:
        """Test save game handles missing player sprite."""
        self.mock_player_plugin.get_player_sprite.return_value = None

        result = self.plugin.save_game(slot=1)
        assert result is True

    def test_save_game_exception(self) -> None:
        """Test save game handles exceptions."""
        self.mock_player_plugin.get_player_sprite.side_effect = Exception("Test error")

        result = self.plugin.save_game(slot=1)
        assert result is False

    def test_load_game_success(self) -> None:
        """Test loading game successfully."""
        save_data = {
            "save_states": {"plugin1": {"key": "value"}},
            "save_timestamp": 1234567890.0,
            "save_version": "2.0",
        }

        m_open = mock_open(read_data=json.dumps(save_data))
        with (
            patch("pedre.plugins.save.plugin.Path.exists", return_value=True),
            patch("pedre.plugins.save.plugin.Path.open", m_open),
        ):
            result = self.plugin.load_game(slot=1)

        assert result is not None
        assert isinstance(result, GameSaveData)
        assert result.save_states == {"plugin1": {"key": "value"}}
        assert result.save_timestamp == 1234567890.0
        assert self.plugin.current_slot == 1

    def test_load_game_no_file(self) -> None:
        """Test loading game when file doesn't exist."""
        with patch("pedre.plugins.save.plugin.Path.exists", return_value=False):
            result = self.plugin.load_game(slot=1)

        assert result is None

    def test_load_game_exception(self) -> None:
        """Test load game handles exceptions."""
        with patch("pedre.plugins.save.plugin.Path.exists", side_effect=Exception("Test error")):
            result = self.plugin.load_game(slot=1)

        assert result is None

    def test_restore_game_data(self) -> None:
        """Test restoring game data to plugins."""
        save_data = GameSaveData(
            save_states={
                "plugin1": {"key1": "value1"},
                "plugin2": {"key2": "value2"},
            }
        )

        self.plugin.restore_game_data(save_data)

        # Verify pending save data was set
        self.mock_context.set_pending_save_data.assert_called_once_with(save_data)

        # Verify each plugin's restore_save_state was called
        plugins = self.mock_context.get_plugins()
        plugins["plugin1"].restore_save_state.assert_called_once_with({"key1": "value1"})
        plugins["plugin2"].restore_save_state.assert_called_once_with({"key2": "value2"})

    def test_apply_entity_states(self) -> None:
        """Test applying entity states after sprites exist."""
        save_data = GameSaveData(
            save_states={
                "plugin1": {"entity_data": "test1"},
                "plugin2": {"entity_data": "test2"},
            }
        )

        self.mock_context.get_pending_save_data.return_value = save_data

        self.plugin.apply_entity_states()

        # Verify each plugin's apply_entity_state was called
        plugins = self.mock_context.get_plugins()
        plugins["plugin1"].apply_entity_state.assert_called_once_with({"entity_data": "test1"})
        plugins["plugin2"].apply_entity_state.assert_called_once_with({"entity_data": "test2"})

        # Verify pending save data was cleared
        self.mock_context.clear_pending_save_data.assert_called_once()

    def test_apply_entity_states_no_pending_data(self) -> None:
        """Test apply entity states when no pending data exists."""
        self.mock_context.get_pending_save_data.return_value = None

        self.plugin.apply_entity_states()

        # Should return early without processing
        plugins = self.mock_context.get_plugins()
        plugins["plugin1"].apply_entity_state.assert_not_called()
        self.mock_context.clear_pending_save_data.assert_not_called()

    def test_delete_save_success(self) -> None:
        """Test deleting save file successfully."""
        with (
            patch("pedre.plugins.save.plugin.Path.exists", return_value=True),
            patch("pedre.plugins.save.plugin.Path.unlink") as mock_unlink,
        ):
            result = self.plugin.delete_save(slot=1)

        assert result is True
        mock_unlink.assert_called_once()

    def test_delete_save_no_file(self) -> None:
        """Test deleting save when file doesn't exist."""
        with patch("pedre.plugins.save.plugin.Path.exists", return_value=False):
            result = self.plugin.delete_save(slot=1)

        assert result is False

    def test_delete_save_exception(self) -> None:
        """Test delete save handles exceptions."""
        with (
            patch("pedre.plugins.save.plugin.Path.exists", return_value=True),
            patch("pedre.plugins.save.plugin.Path.unlink", side_effect=Exception("Test error")),
        ):
            result = self.plugin.delete_save(slot=1)

        assert result is False

    def test_save_exists(self) -> None:
        """Test checking if save exists."""
        with patch("pedre.plugins.save.plugin.Path.exists", return_value=True):
            result = self.plugin.save_exists(slot=1)
        assert result is True

        with patch("pedre.plugins.save.plugin.Path.exists", return_value=False):
            result = self.plugin.save_exists(slot=1)
        assert result is False

    @patch("pedre.plugins.save.plugin.datetime")
    def test_get_save_info_success(self, mock_datetime_cls: MagicMock) -> None:
        """Test getting save info successfully."""
        # Create a mock datetime instance
        mock_dt = MagicMock()
        mock_dt.strftime.return_value = "2024-01-15 10:30"
        mock_datetime_cls.fromtimestamp.return_value = mock_dt
        mock_datetime_cls.UTC = UTC

        save_data = {
            "save_states": {"scene": {"current_map": "test_map.tmx"}},
            "save_timestamp": 1234567890.0,
            "save_version": "2.0",
        }

        m_open = mock_open(read_data=json.dumps(save_data))
        with (
            patch("pedre.plugins.save.plugin.Path.exists", return_value=True),
            patch("pedre.plugins.save.plugin.Path.open", m_open),
        ):
            result = self.plugin.get_save_info(slot=1)

        assert result is not None
        assert result["slot"] == 1
        assert result["map"] == "test_map.tmx"
        assert result["timestamp"] == 1234567890.0
        assert result["date_string"] == "2024-01-15 10:30"
        assert result["version"] == "2.0"

    def test_get_save_info_no_file(self) -> None:
        """Test get save info when file doesn't exist."""
        with patch("pedre.plugins.save.plugin.Path.exists", return_value=False):
            result = self.plugin.get_save_info(slot=1)

        assert result is None

    def test_get_save_info_exception(self) -> None:
        """Test get save info handles exceptions."""
        with patch("pedre.plugins.save.plugin.Path.exists", side_effect=Exception("Test error")):
            result = self.plugin.get_save_info(slot=1)

        assert result is None

    def test_auto_save(self) -> None:
        """Test auto save delegates to save_game with slot 0."""
        with patch.object(self.plugin, "save_game", return_value=True) as mock_save:
            result = self.plugin.auto_save()

        assert result is True
        mock_save.assert_called_once_with(0)

    def test_load_auto_save(self) -> None:
        """Test load auto save delegates to load_game with slot 0."""
        mock_save_data = GameSaveData(save_states={"test": "data"})

        with patch.object(self.plugin, "load_game", return_value=mock_save_data) as mock_load:
            result = self.plugin.load_auto_save()

        assert result == mock_save_data
        mock_load.assert_called_once_with(0)

    def test_get_save_path_auto_save(self) -> None:
        """Test get save path for auto save slot."""
        path = self.plugin._get_save_path(0)
        assert path.name == "autosave.json"

    def test_get_save_path_manual_slot(self) -> None:
        """Test get save path for manual save slot."""
        path = self.plugin._get_save_path(1)
        assert path.name == "save_slot_1.json"

        path = self.plugin._get_save_path(3)
        assert path.name == "save_slot_3.json"


class TestGameSaveData(unittest.TestCase):
    """Test Suite for GameSaveData."""

    def test_initialization_defaults(self) -> None:
        """Test GameSaveData initializes with defaults."""
        save_data = GameSaveData()
        assert save_data.save_states == {}
        assert save_data.save_timestamp == 0.0
        assert save_data.save_version == "2.0"

    def test_initialization_with_values(self) -> None:
        """Test GameSaveData initializes with provided values."""
        save_states = {"plugin1": {"key": "value"}}
        timestamp = 1234567890.0

        save_data = GameSaveData(
            save_states=save_states,
            save_timestamp=timestamp,
            save_version="1.0",
        )

        assert save_data.save_states == save_states
        assert save_data.save_timestamp == timestamp
        assert save_data.save_version == "1.0"

    def test_to_dict(self) -> None:
        """Test converting GameSaveData to dictionary."""
        save_data = GameSaveData(
            save_states={"plugin1": {"key": "value"}},
            save_timestamp=1234567890.0,
            save_version="2.0",
        )

        result = save_data.to_dict()

        assert result["save_states"] == {"plugin1": {"key": "value"}}
        assert result["save_timestamp"] == 1234567890.0
        assert result["save_version"] == "2.0"

    def test_from_dict(self) -> None:
        """Test creating GameSaveData from dictionary."""
        data = {
            "save_states": {"plugin1": {"key": "value"}},
            "save_timestamp": 1234567890.0,
            "save_version": "2.0",
        }

        save_data = GameSaveData.from_dict(data)

        assert save_data.save_states == {"plugin1": {"key": "value"}}
        assert save_data.save_timestamp == 1234567890.0
        assert save_data.save_version == "2.0"

    def test_from_dict_missing_fields(self) -> None:
        """Test creating GameSaveData from dict with missing fields uses defaults."""
        data: dict[str, object] = {}

        save_data = GameSaveData.from_dict(data)

        assert save_data.save_states == {}
        assert save_data.save_timestamp == 0.0
        assert save_data.save_version == "2.0"

    def test_round_trip_serialization(self) -> None:
        """Test that to_dict/from_dict round trip preserves data."""
        original = GameSaveData(
            save_states={"plugin1": {"key": "value"}, "plugin2": {"num": 42}},
            save_timestamp=9876543210.0,
            save_version="1.5",
        )

        # Serialize and deserialize
        data_dict = original.to_dict()
        restored = GameSaveData.from_dict(data_dict)

        assert restored.save_states == original.save_states
        assert restored.save_timestamp == original.save_timestamp
        assert restored.save_version == original.save_version


if __name__ == "__main__":
    unittest.main()
