"""Unit tests for NPCPlugin in src/pedre/plugins/npc/plugin.py."""

import json
import unittest
from collections import deque
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import arcade

from pedre.actions.registry import ActionParseError
from pedre.plugins.npc.base import NPCDialogConfig
from pedre.plugins.npc.plugin import NPCPlugin
from pedre.plugins.npc.sprites import AnimatedNPC


class TestNPCPlugin(unittest.TestCase):
    """Test Suite for NPCPlugin."""

    def setUp(self) -> None:
        """Set up the NPCPlugin and mock context."""
        self.plugin = NPCPlugin()
        self.mock_context = MagicMock()
        self.mock_scene_plugin = MagicMock()
        self.mock_context.scene_plugin = self.mock_scene_plugin
        self.plugin.setup(self.mock_context)

    def test_initialization(self) -> None:
        """Test proper initialization of the plugin."""
        assert self.plugin.name == "npc"
        assert self.plugin.npcs == {}
        assert self.plugin.dialogs == {}
        assert self.plugin.interacted_npcs == {}
        assert self.plugin.context == self.mock_context

    def test_register_npc(self) -> None:
        """Test registering an NPC."""
        mock_sprite = MagicMock()
        npc_name = "guard"

        self.plugin.register_npc(mock_sprite, npc_name)

        assert npc_name in self.plugin.npcs
        npc_state = self.plugin.npcs[npc_name]
        assert npc_state.sprite == mock_sprite
        assert npc_state.name == npc_name
        assert npc_state.dialog_level == 0
        assert not npc_state.is_moving
        assert len(npc_state.path) == 0

    def test_get_nearby_npc(self) -> None:
        """Test finding nearby NPCs."""
        # Setup player
        player_sprite = MagicMock()
        player_sprite.center_x = 100
        player_sprite.center_y = 100

        # Setup NPC close to player
        npc1_sprite = MagicMock()
        npc1_sprite.center_x = 110
        npc1_sprite.center_y = 100
        npc1_sprite.visible = True
        self.plugin.register_npc(npc1_sprite, "npc1")

        # Setup NPC far from player
        npc2_sprite = MagicMock()
        npc2_sprite.center_x = 500
        npc2_sprite.center_y = 500
        npc2_sprite.visible = True
        self.plugin.register_npc(npc2_sprite, "npc2")

        # Setup hidden NPC close to player
        npc3_sprite = MagicMock()
        npc3_sprite.center_x = 105
        npc3_sprite.center_y = 100
        npc3_sprite.visible = False
        self.plugin.register_npc(npc3_sprite, "npc3")

        # Test finding closest
        with patch("pedre.plugins.npc.plugin.arcade.get_distance_between_sprites") as mock_dist:
            # Mock distances: interaction threshold is usually ~64
            # npc1 is dist 10, npc2 is dist 400
            def get_dist(_s1: MagicMock, s2: MagicMock) -> float:
                if s2 == npc1_sprite:
                    return 10.0
                if s2 == npc2_sprite:
                    return 400.0
                if s2 == npc3_sprite:
                    return 5.0
                return 1000.0

            mock_dist.side_effect = get_dist

            result = self.plugin.get_nearby_npc(player_sprite)
            assert result is not None
            sprite, name, _level = result
            assert name == "npc1"
            assert sprite == npc1_sprite

    def test_interact_with_npc_success(self) -> None:
        """Test successful interaction with an NPC."""
        self.mock_context.dialog_plugin = MagicMock()
        self.mock_scene_plugin.get_current_scene.return_value = "village"

        # Register NPC
        mock_sprite = MagicMock()
        self.plugin.register_npc(mock_sprite, "elder")

        # Manually load a dialog
        dialog_config = NPCDialogConfig(text=["Hello there"], name="Elder One")
        self.plugin.dialogs = {"village": {"elder": {0: dialog_config}}}

        result = self.plugin.interact_with_npc("elder")

        assert result is True
        self.mock_context.dialog_plugin.show_dialog.assert_called_once()
        assert "elder" in self.plugin.interacted_npcs.get("village", set())

    def test_interact_with_npc_no_dialog(self) -> None:
        """Test interaction when no dialog is available."""
        self.mock_context.dialog_plugin = MagicMock()
        self.mock_scene_plugin.get_current_scene.return_value = "village"

        # Register NPC but no dialogs loaded
        mock_sprite = MagicMock()
        self.plugin.register_npc(mock_sprite, "mime")

        result = self.plugin.interact_with_npc("mime")

        assert result is False
        self.mock_context.dialog_plugin.show_dialog.assert_not_called()

    def test_advance_dialog(self) -> None:
        """Test advancing dialog level."""
        mock_sprite = MagicMock()
        self.plugin.register_npc(mock_sprite, "quest_giver")

        assert self.plugin.npcs["quest_giver"].dialog_level == 0

        new_level = self.plugin.advance_dialog("quest_giver")

        assert new_level == 1
        assert self.plugin.npcs["quest_giver"].dialog_level == 1

    def test_move_npc_to_tile(self) -> None:
        """Test initiating NPC movement."""
        self.mock_context.pathfinding_plugin = MagicMock()
        mock_sprite = MagicMock()
        mock_sprite.center_x = 100
        mock_sprite.center_y = 100
        self.plugin.register_npc(mock_sprite, "walker")

        # Mock pathfinding result
        path = [(132, 100), (164, 100)]
        self.mock_context.pathfinding_plugin.find_path.return_value = path

        # Now uses pixel coordinates
        self.plugin.move_npc_to_position("walker", 160.0, 160.0)

        assert self.plugin.npcs["walker"].path == path
        assert self.plugin.npcs["walker"].is_moving is True
        self.mock_context.pathfinding_plugin.find_path.assert_called_once()

    def test_cache_scene_state(self) -> None:
        """Test caching scene state."""
        # Setup NPC
        mock_sprite = MagicMock(spec=AnimatedNPC)
        mock_sprite.center_x = 200.0
        mock_sprite.center_y = 300.0
        mock_sprite.visible = True
        mock_sprite.appear_complete = True
        mock_sprite.disappear_complete = False
        mock_sprite.interact_complete = False

        self.plugin.register_npc(mock_sprite, "guard")
        self.plugin.npcs["guard"].dialog_level = 2

        state = self.plugin.cache_scene_state("current_scene")

        assert "guard" in state
        guard_state = state["guard"]
        assert guard_state["x"] == 200.0
        assert guard_state["y"] == 300.0
        assert guard_state["visible"] is True
        assert guard_state["dialog_level"] == 2
        assert guard_state["appear_complete"] is True

    def test_restore_scene_state(self) -> None:
        """Test restoring scene state."""
        # Setup initial NPC
        mock_sprite = MagicMock(spec=AnimatedNPC)
        self.plugin.register_npc(mock_sprite, "guard")

        # State to restore
        state = {
            "guard": {
                "x": 500.0,
                "y": 600.0,
                "visible": False,
                "dialog_level": 5,
                "appear_complete": True,
                "disappear_complete": True,
            }
        }

        self.plugin.restore_scene_state("scene_name_is_unused_here", state)

        npc = self.plugin.npcs["guard"]
        assert npc.sprite.center_x == 500.0
        assert npc.sprite.center_y == 600.0
        assert npc.sprite.visible is False
        assert npc.dialog_level == 5

        # Cast to AnimatedNPC (or Mock) to access specific attributes
        sprite = cast("AnimatedNPC", npc.sprite)
        assert sprite.appear_complete is True
        assert sprite.disappear_complete is True

    def test_get_save_state_includes_history(self) -> None:
        """Test that get_save_state includes global interaction history."""
        self.plugin.interacted_npcs = {"village": {"bob", "alice"}, "castle": {"king"}}

        save_data = self.plugin.get_save_state()

        assert "interacted_npcs" in save_data
        history = save_data["interacted_npcs"]
        # Sets are converted to lists
        assert set(history["village"]) == {"bob", "alice"}
        assert set(history["castle"]) == {"king"}

    def test_apply_entity_state(self) -> None:
        """Test applying entity state (restoring from save)."""
        mock_sprite = MagicMock(spec=AnimatedNPC)
        self.plugin.register_npc(mock_sprite, "alice")

        save_data = {
            "npcs": {"alice": {"x": 10.0, "y": 20.0, "visible": True, "dialog_level": 1}},
            "interacted_npcs": {"dungeon": ["goblin"]},
        }

        self.plugin.apply_entity_state(save_data)

        # Check NPC updated
        assert self.plugin.npcs["alice"].sprite.center_x == 10.0

        # Check history restored
        assert "goblin" in self.plugin.interacted_npcs["dungeon"]

    def test_load_from_tiled_no_layer(self) -> None:
        """Test load_from_tiled when no NPCs layer exists."""
        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {}
        mock_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_scene)

        # Should complete without error and have no NPCs
        assert len(self.plugin.npcs) == 0

    def test_load_from_tiled_with_layer(self) -> None:
        """Test load_from_tiled when NPCs layer exists."""
        mock_tile_map = MagicMock()
        mock_npc_obj = MagicMock()
        mock_npc_obj.properties = {"name": "guard", "sprite_sheet": "sprites/guard.png"}
        mock_npc_obj.shape = [100.0, 200.0]
        mock_tile_map.object_lists = {"NPCs": [mock_npc_obj]}
        mock_scene = MagicMock()

        with patch.object(self.plugin, "load_npcs_from_objects") as mock_load:
            self.plugin.load_from_tiled(mock_tile_map, mock_scene)
            mock_load.assert_called_once_with([mock_npc_obj], mock_scene)

    def test_cleanup(self) -> None:
        """Test cleanup clears all NPCs and dialogs."""
        # Add some data
        mock_sprite = MagicMock()
        self.plugin.register_npc(mock_sprite, "test_npc")
        self.plugin.dialogs = {"scene": {"npc": {0: NPCDialogConfig(text=["test"])}}}

        self.plugin.cleanup()

        assert len(self.plugin.npcs) == 0
        assert len(self.plugin.dialogs) == 0

    def test_reset(self) -> None:
        """Test reset clears all plugin state."""
        # Add some data
        mock_sprite = MagicMock()
        self.plugin.register_npc(mock_sprite, "test_npc")
        self.plugin.dialogs = {"scene": {"npc": {0: NPCDialogConfig(text=["test"])}}}
        self.plugin.interacted_npcs = {"scene": {"npc1"}}

        self.plugin.reset()

        assert len(self.plugin.npcs) == 0
        assert len(self.plugin.dialogs) == 0
        assert len(self.plugin.interacted_npcs) == 0

    def test_get_npcs(self) -> None:
        """Test get_npcs returns NPC dictionary."""
        mock_sprite = MagicMock()
        self.plugin.register_npc(mock_sprite, "npc1")

        npcs = self.plugin.get_npcs()

        assert "npc1" in npcs
        assert npcs["npc1"].name == "npc1"

    def test_load_dialogs(self) -> None:
        """Test load_dialogs sets dialog dictionary."""
        dialogs = {"scene1": {"npc1": {0: NPCDialogConfig(text=["Hello"])}}}

        self.plugin.load_dialogs(dialogs)

        assert self.plugin.dialogs == dialogs

    def test_load_scene_dialogs_cached(self) -> None:
        """Test load_scene_dialogs returns cached dialogs."""
        # Pre-populate cache
        dialog_config = NPCDialogConfig(text=["Cached dialog"])
        NPCPlugin._dialog_cache["test_scene"] = {"npc1": {0: dialog_config}}

        result = self.plugin.load_scene_dialogs("test_scene")

        assert "npc1" in result
        assert result["npc1"][0] == dialog_config
        assert "test_scene" in self.plugin.dialogs

    def test_load_scene_dialogs_from_file(self) -> None:
        """Test load_scene_dialogs loads from JSON file."""
        NPCPlugin._dialog_cache.clear()

        with (
            patch.object(self.plugin, "load_dialogs_from_json") as mock_load,
            patch("pedre.plugins.npc.plugin.asset_path", return_value=Path("/assets/dialogs/new_scene_dialogs.json")),
        ):
            # Simulate successful loading by populating dialogs
            def side_effect(_path: Path) -> bool:
                self.plugin.dialogs["new_scene"] = {"npc1": {0: NPCDialogConfig(text=["Test"])}}
                return True

            mock_load.side_effect = side_effect

            self.plugin.load_scene_dialogs("new_scene")

            assert mock_load.called
            # Should cache the loaded dialogs
            assert "new_scene" in NPCPlugin._dialog_cache

    def test_load_scene_dialogs_file_not_found(self) -> None:
        """Test load_scene_dialogs when file doesn't exist."""
        NPCPlugin._dialog_cache.clear()

        with patch.object(self.plugin, "load_dialogs_from_json") as mock_load:
            mock_load.return_value = False

            result = self.plugin.load_scene_dialogs("nonexistent")

            assert result == {}

    def test_load_dialogs_from_json_single_file(self) -> None:
        """Test loading dialogs from a single JSON file."""
        # Create a mock Path object
        mock_path = MagicMock(spec=Path)
        mock_path.is_file.return_value = True
        mock_path.is_dir.return_value = False
        mock_path.stem = "test_dialogs"
        mock_path.name = "test_dialogs.json"

        # Patch Path constructor to return our mock
        with (
            patch("pedre.plugins.npc.plugin.Path", return_value=mock_path),
            patch.object(self.plugin, "_load_dialog_file", return_value=True) as mock_load_file,
        ):
            result = self.plugin.load_dialogs_from_json("/fake/test_dialogs.json")

            assert result is True
            mock_load_file.assert_called_once_with(mock_path)

    def test_load_dialogs_from_json_directory(self) -> None:
        """Test loading dialogs from a directory."""
        with (
            patch("pathlib.Path.is_dir", return_value=True),
            patch("pathlib.Path.glob", return_value=[Path("file1.json"), Path("file2.json")]),
            patch.object(self.plugin, "_load_dialog_file", return_value=True) as mock_load,
        ):
            result = self.plugin.load_dialogs_from_json(Path("/fake/dialogs/"))

            assert result is True
            assert mock_load.call_count == 2

    def test_load_dialogs_from_json_empty_directory(self) -> None:
        """Test loading dialogs from empty directory."""
        with patch("pathlib.Path.is_dir", return_value=True), patch("pathlib.Path.glob", return_value=[]):
            result = self.plugin.load_dialogs_from_json(Path("/fake/empty/"))

            assert result is False

    def test_load_dialogs_from_json_path_not_found(self) -> None:
        """Test loading dialogs from non-existent path."""
        with patch("pathlib.Path.is_file", return_value=False), patch("pathlib.Path.is_dir", return_value=False):
            result = self.plugin.load_dialogs_from_json(Path("/fake/nonexistent"))

            assert result is False

    def test_load_dialog_file_with_conditions(self) -> None:
        """Test loading dialog file with conditions and on_condition_fail actions."""
        dialog_data = {
            "npc1": {
                "0": {
                    "text": ["Conditional dialog"],
                    "conditions": [{"name": "has_item", "item": "key"}],
                    "on_condition_fail": [{"name": "dialog", "speaker": "Guard", "text": ["You need a key"]}],
                }
            }
        }

        # Create a mock Path object
        mock_path = MagicMock(spec=Path)
        mock_path.stem = "scene_dialogs"
        mock_path.name = "scene_dialogs.json"

        mock_action = MagicMock()
        with (
            patch("json.load", return_value=dialog_data),
            patch("pedre.plugins.npc.plugin.ActionRegistry.create", return_value=mock_action),
        ):
            result = self.plugin._load_dialog_file(mock_path)

            assert result is True
            assert "scene" in self.plugin.dialogs
            assert "npc1" in self.plugin.dialogs["scene"]
            config = self.plugin.dialogs["scene"]["npc1"][0]
            assert config.conditions is not None
            assert config.on_condition_fail == [mock_action]

    def test_load_dialog_file_on_condition_fail_parse_error_skips_action(self) -> None:
        """Test that an ActionParseError during on_condition_fail parsing is logged and skipped."""
        dialog_data = {
            "npc1": {
                "0": {
                    "text": ["Hello"],
                    "on_condition_fail": [{"name": "bad_action"}],
                }
            }
        }

        mock_path = MagicMock(spec=Path)
        mock_path.stem = "scene_dialogs"
        mock_path.name = "scene_dialogs.json"

        with (
            patch("json.load", return_value=dialog_data),
            patch("pedre.plugins.npc.plugin.ActionRegistry.create", side_effect=ActionParseError("unknown action")),
        ):
            result = self.plugin._load_dialog_file(mock_path)

            assert result is True
            config = self.plugin.dialogs["scene"]["npc1"][0]
            assert config.on_condition_fail == []

    def test_load_dialog_file_json_decode_error(self) -> None:
        """Test loading dialog file with invalid JSON."""
        mock_path = MagicMock(spec=Path)
        mock_path.stem = "bad"
        mock_path.name = "bad.json"

        with patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)):
            result = self.plugin._load_dialog_file(mock_path)

            assert result is False

    def test_load_dialog_file_file_not_found(self) -> None:
        """Test loading dialog file that doesn't exist."""
        mock_path = MagicMock(spec=Path)
        mock_path.stem = "missing"
        mock_path.name = "missing.json"
        mock_path.open.side_effect = FileNotFoundError

        result = self.plugin._load_dialog_file(mock_path)

        assert result is False

    def test_load_dialog_file_os_error(self) -> None:
        """Test loading dialog file with OS error."""
        mock_path = MagicMock(spec=Path)
        mock_path.stem = "error"
        mock_path.name = "error.json"
        mock_path.open.side_effect = OSError

        result = self.plugin._load_dialog_file(mock_path)

        assert result is False

    def test_load_dialog_file_unexpected_error(self) -> None:
        """Test loading dialog file with unexpected error."""
        mock_path = MagicMock(spec=Path)
        mock_path.stem = "error"
        mock_path.name = "error.json"
        mock_path.open.side_effect = RuntimeError("Unexpected")

        result = self.plugin._load_dialog_file(mock_path)

        assert result is False

    def test_get_npc_by_name_found(self) -> None:
        """Test getting NPC by name when it exists."""
        mock_sprite = MagicMock()
        self.plugin.register_npc(mock_sprite, "alice")

        result = self.plugin.get_npc_by_name("alice")

        assert result is not None
        assert result.name == "alice"

    def test_get_npc_by_name_not_found(self) -> None:
        """Test getting NPC by name when it doesn't exist."""
        result = self.plugin.get_npc_by_name("nonexistent")

        assert result is None

    def test_get_nearby_npc_moving_npc_ignored(self) -> None:
        """Test that moving NPCs are ignored in get_nearby_npc."""
        player_sprite = MagicMock()
        player_sprite.center_x = 100
        player_sprite.center_y = 100

        # Setup moving NPC close to player
        npc_sprite = MagicMock()
        npc_sprite.center_x = 105
        npc_sprite.center_y = 100
        npc_sprite.visible = True
        self.plugin.register_npc(npc_sprite, "moving_npc")
        self.plugin.npcs["moving_npc"].is_moving = True

        with patch("pedre.plugins.npc.plugin.arcade.get_distance_between_sprites", return_value=5.0):
            result = self.plugin.get_nearby_npc(player_sprite)

            # Should return None because NPC is moving
            assert result is None

    def test_on_key_press_interaction_key(self) -> None:
        """Test on_key_press with interaction key."""
        self.mock_context.player_plugin = MagicMock()
        player_sprite = MagicMock()
        player_sprite.center_x = 100
        player_sprite.center_y = 100
        self.mock_context.player_plugin.get_player_sprite.return_value = player_sprite

        # Setup nearby NPC
        npc_sprite = MagicMock()
        npc_sprite.center_x = 110
        npc_sprite.center_y = 100
        npc_sprite.visible = True
        self.plugin.register_npc(npc_sprite, "nearby_npc")

        with (
            patch("pedre.plugins.npc.plugin.matches_key", return_value=True),
            patch("pedre.plugins.npc.plugin.arcade.get_distance_between_sprites", return_value=10.0),
            patch.object(self.plugin, "interact_with_npc", return_value=True) as mock_interact,
        ):
            result = self.plugin.on_key_press(123, 0)

            assert result is True
            mock_interact.assert_called_once_with("nearby_npc")

    def test_on_key_press_no_player(self) -> None:
        """Test on_key_press when player doesn't exist."""
        self.mock_context.player_plugin = MagicMock()
        self.mock_context.player_plugin.get_player_sprite.return_value = None

        with patch("pedre.plugins.npc.plugin.matches_key", return_value=True):
            result = self.plugin.on_key_press(123, 0)

            assert result is False

    def test_on_key_press_no_nearby_npc(self) -> None:
        """Test on_key_press when no NPC is nearby."""
        self.mock_context.player_plugin = MagicMock()
        player_sprite = MagicMock()
        self.mock_context.player_plugin.get_player_sprite.return_value = player_sprite

        with (
            patch("pedre.plugins.npc.plugin.matches_key", return_value=True),
            patch.object(self.plugin, "get_nearby_npc", return_value=None),
        ):
            result = self.plugin.on_key_press(123, 0)

            assert result is False

    def test_on_key_press_wrong_key(self) -> None:
        """Test on_key_press with wrong key."""
        with patch("pedre.plugins.npc.plugin.matches_key", return_value=False):
            result = self.plugin.on_key_press(456, 0)

            assert result is False

    def test_interact_with_npc_no_npc(self) -> None:
        """Test interaction with non-existent NPC."""
        result = self.plugin.interact_with_npc("nonexistent")

        assert result is False

    def test_interact_with_npc_condition_fail_delegates_to_script_plugin(self) -> None:
        """Test interaction when conditions fail delegates on_condition_fail to ScriptPlugin."""
        self.mock_context.dialog_plugin = MagicMock()
        self.mock_context.script_plugin = MagicMock()
        self.mock_scene_plugin.get_current_scene.return_value = "dungeon"

        # Register NPC
        mock_sprite = MagicMock()
        self.plugin.register_npc(mock_sprite, "guard")

        # Setup dialog with failing conditions and pre-parsed actions
        mock_action = MagicMock()
        dialog_config = NPCDialogConfig(
            text=["You shall pass"],
            conditions=[{"name": "has_item", "item": "pass"}],
            on_condition_fail=[mock_action],
        )
        self.plugin.dialogs = {"dungeon": {"guard": {0: dialog_config}}}

        with patch.object(self.plugin, "_check_dialog_conditions", return_value=False):
            result = self.plugin.interact_with_npc("guard")

            assert result is True
            self.mock_context.script_plugin.run_actions.assert_called_once_with(
                "npc_guard_condition_fail", [mock_action]
            )
            self.mock_context.dialog_plugin.show_dialog.assert_not_called()

    def test_mark_npc_as_interacted_with_scene(self) -> None:
        """Test marking NPC as interacted with specific scene."""
        self.plugin.mark_npc_as_interacted("alice", "village")

        assert "alice" in self.plugin.interacted_npcs["village"]

    def test_mark_npc_as_interacted_default_scene(self) -> None:
        """Test marking NPC as interacted using current scene."""
        self.mock_scene_plugin.get_current_scene.return_value = "castle"

        self.plugin.mark_npc_as_interacted("bob")

        assert "bob" in self.plugin.interacted_npcs["castle"]

    def test_has_npc_been_interacted_with_true(self) -> None:
        """Test checking if NPC has been interacted with."""
        self.plugin.interacted_npcs = {"forest": {"npc1"}}

        result = self.plugin.has_npc_been_interacted_with("npc1", "forest")

        assert result is True

    def test_has_npc_been_interacted_with_false(self) -> None:
        """Test checking if NPC has not been interacted with."""
        self.plugin.interacted_npcs = {"forest": {"npc1"}}

        result = self.plugin.has_npc_been_interacted_with("npc2", "forest")

        assert result is False

    def test_has_npc_been_interacted_with_default_scene(self) -> None:
        """Test checking interaction with default scene."""
        self.mock_scene_plugin.get_current_scene.return_value = "desert"
        self.plugin.interacted_npcs = {"desert": {"npc1"}}

        result = self.plugin.has_npc_been_interacted_with("npc1")

        assert result is True

    def test_check_dialog_conditions_missing_check_field(self) -> None:
        """Test dialog conditions with missing check field."""
        conditions = [{"item": "key"}]  # Missing 'check' field

        result = self.plugin._check_dialog_conditions(conditions)

        assert result is False

    def test_get_dialog_with_scene_fallback(self) -> None:
        """Test get_dialog falls back to default scene."""
        dialog_config = NPCDialogConfig(text=["Default dialog"])
        self.plugin.dialogs = {"default": {"npc1": {0: dialog_config}}}

        result, fail_actions = self.plugin.get_dialog("npc1", 0, "nonexistent_scene")

        assert result == dialog_config
        assert fail_actions is None

    def test_get_dialog_npc_not_found(self) -> None:
        """Test get_dialog with non-existent NPC."""
        self.plugin.dialogs = {"scene1": {}}

        result, fail_actions = self.plugin.get_dialog("nonexistent", 0, "scene1")

        assert result is None
        assert fail_actions is None

    def test_get_dialog_condition_failed_returns_actions(self) -> None:
        """Test get_dialog returns on_condition_fail actions (pre-parsed Action objects)."""
        mock_action = MagicMock()
        fail_actions = [mock_action]
        dialog_config = NPCDialogConfig(
            text=["Success"], conditions=[{"name": "has_item"}], on_condition_fail=fail_actions
        )
        self.plugin.dialogs = {"scene1": {"npc1": {0: dialog_config}}}

        with patch.object(self.plugin, "_check_dialog_conditions", return_value=False):
            result, returned_actions = self.plugin.get_dialog("npc1", 0, "scene1")

            assert result is None
            assert returned_actions == fail_actions

    def test_get_dialog_fallback_to_string_key(self) -> None:
        """Test get_dialog fallback prefers string keys."""
        string_dialog = NPCDialogConfig(text=["String key dialog"])
        numeric_dialog = NPCDialogConfig(text=["Numeric dialog"])
        self.plugin.dialogs = {"scene1": {"npc1": {"1_special": string_dialog, 0: numeric_dialog}}}

        result, _ = self.plugin.get_dialog("npc1", 5, "scene1")

        assert result == string_dialog

    def test_get_dialog_fallback_to_numeric_progression(self) -> None:
        """Test get_dialog fallback to numeric progression."""
        dialog_level_1 = NPCDialogConfig(text=["Level 1"])
        dialog_level_3 = NPCDialogConfig(text=["Level 3"])
        self.plugin.dialogs = {"scene1": {"npc1": {1: dialog_level_1, 3: dialog_level_3}}}

        # Asking for level 5 should return level 3 (highest <= 5)
        result, _ = self.plugin.get_dialog("npc1", 5, "scene1")

        assert result == dialog_level_3

    def test_get_dialog_no_candidates(self) -> None:
        """Test get_dialog when no candidates with met conditions."""
        dialog_config = NPCDialogConfig(text=["Conditional"], conditions=[{"name": "impossible"}])
        self.plugin.dialogs = {"scene1": {"npc1": {0: dialog_config}}}

        with patch.object(self.plugin, "_check_dialog_conditions", return_value=False):
            result, _ = self.plugin.get_dialog("npc1", 5, "scene1")

            assert result is None

    def test_advance_dialog_unknown_npc(self) -> None:
        """Test advancing dialog for unknown NPC."""
        result = self.plugin.advance_dialog("nonexistent")

        assert result == 0

    def test_move_npc_to_position_unknown_npc(self) -> None:
        """Test moving unknown NPC."""
        self.plugin.move_npc_to_position("nonexistent", 100.0, 100.0)

        # Should complete without error

    def test_move_npc_to_position_no_pathfinding(self) -> None:
        """Test moving NPC when pathfinding is unavailable."""
        mock_sprite = MagicMock()
        self.plugin.register_npc(mock_sprite, "npc1")
        self.mock_context.pathfinding_plugin = None

        self.plugin.move_npc_to_position("npc1", 100.0, 100.0)

        # Should complete without error

    def test_move_npc_to_position_excludes_moving_npcs(self) -> None:
        """Test move_npc_to_position excludes other moving NPCs."""
        self.mock_context.pathfinding_plugin = MagicMock()

        # Create main NPC
        npc1_sprite = MagicMock()
        npc1_sprite.center_x = 100
        npc1_sprite.center_y = 100
        self.plugin.register_npc(npc1_sprite, "npc1")

        # Create moving NPC
        npc2_sprite = MagicMock()
        self.plugin.register_npc(npc2_sprite, "npc2")
        self.plugin.npcs["npc2"].is_moving = True

        self.mock_context.pathfinding_plugin.find_path.return_value = [(120, 100)]

        self.plugin.move_npc_to_position("npc1", 120.0, 100.0)

        # Check that npc2_sprite was passed to exclude_sprites
        call_args = self.mock_context.pathfinding_plugin.find_path.call_args
        assert npc2_sprite in call_args.kwargs["exclude_sprites"]

    def test_show_npcs_makes_visible(self) -> None:
        """Test show_npcs makes hidden NPCs visible."""
        npc_sprite = MagicMock()
        npc_sprite.visible = False
        self.plugin.register_npc(npc_sprite, "hidden_npc")

        self.plugin.show_npcs(["hidden_npc"])

        assert npc_sprite.visible is True

    def test_show_npcs_starts_animation(self) -> None:
        """Test show_npcs starts appear animation for AnimatedNPC."""
        npc_sprite = MagicMock(spec=AnimatedNPC)
        npc_sprite.visible = False
        self.plugin.register_npc(npc_sprite, "animated_npc")

        self.plugin.show_npcs(["animated_npc"])

        assert npc_sprite.visible is True
        npc_sprite.start_appear_animation.assert_called_once()

    def test_show_npcs_adds_to_wall_list(self) -> None:
        """Test show_npcs adds NPC to wall list."""
        npc_sprite = MagicMock(spec=AnimatedNPC)
        npc_sprite.visible = False
        self.plugin.register_npc(npc_sprite, "npc1")

        self.plugin.show_npcs(["npc1"])

        self.mock_scene_plugin.add_to_wall_list.assert_called_once_with(npc_sprite)

    def test_show_npcs_already_visible(self) -> None:
        """Test show_npcs skips already visible NPCs."""
        npc_sprite = MagicMock(spec=AnimatedNPC)
        npc_sprite.visible = True
        self.plugin.register_npc(npc_sprite, "visible_npc")

        self.plugin.show_npcs(["visible_npc"])

        # Should not call start_appear_animation for already visible NPC
        npc_sprite.start_appear_animation.assert_not_called()

    def test_show_npcs_unknown_npc(self) -> None:
        """Test show_npcs with unknown NPC."""
        self.plugin.show_npcs(["nonexistent"])

        # Should complete without error

    def test_update_npc_movement_reaches_waypoint(self) -> None:
        """Test update when NPC reaches a waypoint."""
        npc_sprite = MagicMock()
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        self.plugin.register_npc(npc_sprite, "walker")

        # Setup path with multiple waypoints
        self.plugin.npcs["walker"].path = deque([(101.0, 100.0), (120.0, 100.0)])
        self.plugin.npcs["walker"].is_moving = True

        self.plugin.update(1.0)

        # First waypoint should be reached and removed
        assert len(self.plugin.npcs["walker"].path) == 1
        assert self.plugin.npcs["walker"].is_moving is True

    def test_update_npc_movement_completes(self) -> None:
        """Test update when NPC completes movement."""
        self.mock_context.event_bus = MagicMock()
        npc_sprite = MagicMock()
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        self.plugin.register_npc(npc_sprite, "walker")

        # Setup path with one close waypoint
        self.plugin.npcs["walker"].path = deque([(100.5, 100.0)])
        self.plugin.npcs["walker"].is_moving = True

        self.plugin.update(1.0)

        # Movement should be complete
        assert len(self.plugin.npcs["walker"].path) == 0
        assert self.plugin.npcs["walker"].is_moving is False
        # Event should be published
        self.mock_context.event_bus.publish.assert_called_once()

    def test_update_animated_npc_direction(self) -> None:
        """Test update changes animated NPC direction based on movement."""
        npc_sprite = MagicMock(spec=AnimatedNPC)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        npc_sprite.current_direction = "down"
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = False
        self.plugin.register_npc(npc_sprite, "animated")

        # Setup path moving right
        self.plugin.npcs["animated"].path = deque([(120.0, 100.0)])
        self.plugin.npcs["animated"].is_moving = True

        self.plugin.update(0.1)

        # Direction should change to right
        npc_sprite.set_direction.assert_called_with("right")

    def test_update_animated_npc_appear_event(self) -> None:
        """Test update emits appear complete event."""
        self.mock_context.event_bus = MagicMock()
        npc_sprite = MagicMock(spec=AnimatedNPC)
        npc_sprite.appear_complete = True
        npc_sprite.disappear_complete = False
        self.plugin.register_npc(npc_sprite, "appearing")
        self.plugin.npcs["appearing"].appear_event_emitted = False

        self.plugin.update(0.1)

        # Event should be published
        assert any("NPCAppearCompleteEvent" in str(call) for call in self.mock_context.event_bus.publish.call_args_list)
        assert self.plugin.npcs["appearing"].appear_event_emitted is True

    def test_update_animated_npc_disappear_event(self) -> None:
        """Test update emits disappear complete event."""
        self.mock_context.event_bus = MagicMock()
        npc_sprite = MagicMock(spec=AnimatedNPC)
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = True
        self.plugin.register_npc(npc_sprite, "disappearing")
        self.plugin.npcs["disappearing"].disappear_event_emitted = False

        self.plugin.update(0.1)

        # Event should be published
        assert any(
            "NPCDisappearCompleteEvent" in str(call) for call in self.mock_context.event_bus.publish.call_args_list
        )
        assert self.plugin.npcs["disappearing"].disappear_event_emitted is True

    def test_get_npc_positions(self) -> None:
        """Test get_npc_positions returns all NPC positions."""
        npc1_sprite = MagicMock()
        npc1_sprite.center_x = 100.0
        npc1_sprite.center_y = 200.0
        npc1_sprite.visible = True
        self.plugin.register_npc(npc1_sprite, "npc1")

        npc2_sprite = MagicMock()
        npc2_sprite.center_x = 300.0
        npc2_sprite.center_y = 400.0
        npc2_sprite.visible = False
        self.plugin.register_npc(npc2_sprite, "npc2")

        positions = self.plugin.get_npc_positions()

        assert positions["npc1"]["x"] == 100.0
        assert positions["npc1"]["y"] == 200.0
        assert positions["npc1"]["visible"] is True
        assert positions["npc2"]["visible"] is False

    def test_restore_positions(self) -> None:
        """Test _restore_positions updates NPC sprites."""
        npc_sprite = MagicMock()
        self.plugin.register_npc(npc_sprite, "npc1")

        positions = {"npc1": {"x": 500.0, "y": 600.0, "visible": False}}

        self.plugin._restore_positions(positions)

        assert npc_sprite.center_x == 500.0
        assert npc_sprite.center_y == 600.0
        assert npc_sprite.visible is False

    def test_restore_positions_unknown_npc(self) -> None:
        """Test _restore_positions with unknown NPC."""
        positions = {"nonexistent": {"x": 100.0, "y": 200.0, "visible": True}}

        self.plugin._restore_positions(positions)

        # Should complete without error

    def test_has_moving_npcs_true(self) -> None:
        """Test has_moving_npcs returns True when NPCs are moving."""
        npc_sprite = MagicMock()
        self.plugin.register_npc(npc_sprite, "walker")
        self.plugin.npcs["walker"].is_moving = True

        result = self.plugin.has_moving_npcs()

        assert result is True

    def test_has_moving_npcs_false(self) -> None:
        """Test has_moving_npcs returns False when no NPCs are moving."""
        npc_sprite = MagicMock()
        self.plugin.register_npc(npc_sprite, "static")
        self.plugin.npcs["static"].is_moving = False

        result = self.plugin.has_moving_npcs()

        assert result is False

    def test_load_npcs_from_objects_creates_npcs(self) -> None:
        """Test load_npcs_from_objects creates NPC sprites."""
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {
            "name": "Guard",
            "sprite_sheet": "sprites/guard.png",
            "tile_size": 32,
            "scale": 2.0,
        }
        mock_obj.shape = [100.0, 200.0]

        with (
            patch("pedre.plugins.npc.plugin.AnimatedNPC") as mock_anim_npc_class,
            patch("pedre.plugins.npc.plugin.asset_path", return_value="/assets/sprites/guard.png"),
        ):
            mock_npc_instance = MagicMock()
            mock_npc_instance.visible = True
            mock_anim_npc_class.return_value = mock_npc_instance

            self.plugin.load_npcs_from_objects([mock_obj], mock_scene)

            # Should create AnimatedNPC
            mock_anim_npc_class.assert_called_once()
            # Should register NPC
            assert "guard" in self.plugin.npcs

    def test_load_npcs_from_objects_no_properties(self) -> None:
        """Test load_npcs_from_objects skips objects without properties."""
        mock_scene = MagicMock()
        mock_obj = MagicMock()
        mock_obj.properties = None

        self.plugin.load_npcs_from_objects([mock_obj], mock_scene)

        assert len(self.plugin.npcs) == 0

    def test_load_npcs_from_objects_no_name(self) -> None:
        """Test load_npcs_from_objects skips objects without name."""
        mock_scene = MagicMock()
        mock_obj = MagicMock()
        mock_obj.properties = {"sprite_sheet": "test.png"}

        self.plugin.load_npcs_from_objects([mock_obj], mock_scene)

        assert len(self.plugin.npcs) == 0

    def test_load_npcs_from_objects_no_sprite_sheet(self) -> None:
        """Test load_npcs_from_objects skips objects without sprite_sheet."""
        mock_scene = MagicMock()
        mock_obj = MagicMock()
        mock_obj.properties = {"name": "Guard"}
        mock_obj.shape = [100.0, 200.0]

        self.plugin.load_npcs_from_objects([mock_obj], mock_scene)

        assert len(self.plugin.npcs) == 0

    def test_load_npcs_from_objects_initially_hidden(self) -> None:
        """Test load_npcs_from_objects handles initially_hidden flag."""
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {
            "name": "HiddenGuard",
            "sprite_sheet": "sprites/guard.png",
            "initially_hidden": True,
        }
        mock_obj.shape = [100.0, 200.0]

        with (
            patch("pedre.plugins.npc.plugin.AnimatedNPC") as mock_anim_npc_class,
            patch("pedre.plugins.npc.plugin.asset_path", return_value="/assets/sprites/guard.png"),
        ):
            mock_npc_instance = MagicMock()
            mock_anim_npc_class.return_value = mock_npc_instance

            self.plugin.load_npcs_from_objects([mock_obj], mock_scene)

            assert mock_npc_instance.visible is False

    def test_load_npcs_from_objects_adds_to_wall_list(self) -> None:
        """Test load_npcs_from_objects adds visible NPCs to wall list."""
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {"name": "Guard", "sprite_sheet": "sprites/guard.png"}
        mock_obj.shape = [100.0, 200.0]

        with (
            patch("pedre.plugins.npc.plugin.AnimatedNPC") as mock_anim_npc_class,
            patch("pedre.plugins.npc.plugin.asset_path", return_value="/assets/sprites/guard.png"),
        ):
            mock_npc_instance = MagicMock()
            mock_npc_instance.visible = True
            mock_anim_npc_class.return_value = mock_npc_instance

            self.plugin.load_npcs_from_objects([mock_obj], mock_scene)

            self.mock_scene_plugin.add_to_wall_list.assert_called_once_with(mock_npc_instance)

    def test_load_npcs_from_objects_invalid_tile_size(self) -> None:
        """Test load_npcs_from_objects handles invalid tile_size."""
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {
            "name": "Guard",
            "sprite_sheet": "sprites/guard.png",
            "tile_size": "invalid",  # Should be int
        }
        mock_obj.shape = [100.0, 200.0]

        with (
            patch("pedre.plugins.npc.plugin.AnimatedNPC") as mock_anim_npc_class,
            patch("pedre.plugins.npc.plugin.asset_path", return_value="/assets/sprites/guard.png"),
        ):
            mock_npc_instance = MagicMock()
            mock_npc_instance.visible = True
            mock_anim_npc_class.return_value = mock_npc_instance

            self.plugin.load_npcs_from_objects([mock_obj], mock_scene)

            # Should still create NPC, but without tile_size
            call_kwargs = mock_anim_npc_class.call_args.kwargs
            assert "tile_size" not in call_kwargs

    def test_load_npcs_from_objects_invalid_scale(self) -> None:
        """Test load_npcs_from_objects handles invalid scale."""
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {
            "name": "Guard",
            "sprite_sheet": "sprites/guard.png",
            "scale": "invalid",  # Should be float
        }
        mock_obj.shape = [100.0, 200.0]

        with (
            patch("pedre.plugins.npc.plugin.AnimatedNPC") as mock_anim_npc_class,
            patch("pedre.plugins.npc.plugin.asset_path", return_value="/assets/sprites/guard.png"),
        ):
            mock_npc_instance = MagicMock()
            mock_npc_instance.visible = True
            mock_anim_npc_class.return_value = mock_npc_instance

            self.plugin.load_npcs_from_objects([mock_obj], mock_scene)

            # Should still create NPC, but without scale
            call_kwargs = mock_anim_npc_class.call_args.kwargs
            assert "scale" not in call_kwargs

    def test_load_npcs_from_objects_animation_properties(self) -> None:
        """Test load_npcs_from_objects extracts animation properties."""
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {
            "name": "Guard",
            "sprite_sheet": "sprites/guard.png",
            "idle_up_frames": 4,
            "walk_down_frames": 8,
        }
        mock_obj.shape = [100.0, 200.0]

        with (
            patch("pedre.plugins.npc.plugin.AnimatedNPC") as mock_anim_npc_class,
            patch("pedre.plugins.npc.plugin.asset_path", return_value="/assets/sprites/guard.png"),
        ):
            mock_npc_instance = MagicMock()
            mock_npc_instance.visible = True
            mock_anim_npc_class.return_value = mock_npc_instance

            self.plugin.load_npcs_from_objects([mock_obj], mock_scene)

            # Should pass animation properties as keyword args
            # AnimatedNPC is called with: AnimatedNPC(path, **kwargs, **anim_props)
            mock_anim_npc_class.assert_called_once()
            call_kwargs = mock_anim_npc_class.call_args.kwargs
            # The animation properties should be in the kwargs
            assert "idle_up_frames" in call_kwargs
            assert "walk_down_frames" in call_kwargs
            assert call_kwargs["idle_up_frames"] == 4
            assert call_kwargs["walk_down_frames"] == 8

    def test_load_npcs_from_objects_invalid_animation_property(self) -> None:
        """Test load_npcs_from_objects skips invalid animation properties."""
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {
            "name": "Guard",
            "sprite_sheet": "sprites/guard.png",
            "idle_up_frames": "invalid",  # Should be int
        }
        mock_obj.shape = [100.0, 200.0]

        with (
            patch("pedre.plugins.npc.plugin.AnimatedNPC") as mock_anim_npc_class,
            patch("pedre.plugins.npc.plugin.asset_path", return_value="/assets/sprites/guard.png"),
        ):
            mock_npc_instance = MagicMock()
            mock_npc_instance.visible = True
            mock_anim_npc_class.return_value = mock_npc_instance

            self.plugin.load_npcs_from_objects([mock_obj], mock_scene)

            # Should skip invalid animation property
            call_kwargs = mock_anim_npc_class.call_args.kwargs
            assert "idle_up_frames" not in call_kwargs

    def test_load_npcs_from_objects_creation_failure(self) -> None:
        """Test load_npcs_from_objects handles AnimatedNPC creation failure."""
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {"name": "BrokenGuard", "sprite_sheet": "sprites/guard.png"}
        mock_obj.shape = [100.0, 200.0]

        with (
            patch("pedre.plugins.npc.plugin.AnimatedNPC", side_effect=Exception("Creation failed")),
            patch("pedre.plugins.npc.plugin.asset_path", return_value="/assets/sprites/guard.png"),
        ):
            self.plugin.load_npcs_from_objects([mock_obj], mock_scene)

            # Should not register the NPC
            assert "brokenguard" not in self.plugin.npcs

    def test_get_save_state_with_animated_npcs(self) -> None:
        """Test get_save_state includes animation flags for AnimatedNPC."""
        npc_sprite = MagicMock(spec=AnimatedNPC)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 200.0
        npc_sprite.visible = True
        npc_sprite.appear_complete = True
        npc_sprite.disappear_complete = False
        npc_sprite.interact_complete = True
        self.plugin.register_npc(npc_sprite, "animated")

        save_state = self.plugin.get_save_state()

        npc_state = save_state["npcs"]["animated"]
        assert npc_state["appear_complete"] is True
        assert npc_state["disappear_complete"] is False
        assert npc_state["interact_complete"] is True

    def test_restore_save_state(self) -> None:
        """Test restore_save_state (phase 1 - should do nothing)."""
        state = {"npcs": {}, "interacted_npcs": {}}

        # Should complete without error (this is phase 1, no-op)
        self.plugin.restore_save_state(state)

    def test_apply_entity_state_restores_animation_flags(self) -> None:
        """Test apply_entity_state restores animation flags for AnimatedNPC."""
        npc_sprite = MagicMock(spec=AnimatedNPC)
        self.plugin.register_npc(npc_sprite, "animated")

        save_data = {
            "npcs": {
                "animated": {
                    "x": 100.0,
                    "y": 200.0,
                    "visible": True,
                    "dialog_level": 1,
                    "appear_complete": True,
                    "disappear_complete": True,
                    "interact_complete": False,
                }
            },
            "interacted_npcs": {},
        }

        self.plugin.apply_entity_state(save_data)

        assert npc_sprite.appear_complete is True
        assert npc_sprite.disappear_complete is True
        assert npc_sprite.interact_complete is False

    def test_load_scene_dialogs_exception_handling(self) -> None:
        """Test load_scene_dialogs handles exceptions during load."""
        NPCPlugin._dialog_cache.clear()

        with (
            patch.object(self.plugin, "load_dialogs_from_json", side_effect=RuntimeError("Unexpected error")),
            patch("pedre.plugins.npc.plugin.asset_path", return_value=Path("/assets/dialogs/error_scene_dialogs.json")),
        ):
            result = self.plugin.load_scene_dialogs("error_scene")

            # Should handle exception and return empty dict
            assert result == {}

    def test_load_dialog_file_filename_with_dialog_suffix(self) -> None:
        """Test _load_dialog_file with '_dialog' (singular) in filename."""
        dialog_data = {"npc1": {"0": {"text": ["Hello"]}}}

        mock_path = MagicMock(spec=Path)
        mock_path.stem = "scene_dialog"  # singular, not plural
        mock_path.name = "scene_dialog.json"

        with patch("json.load", return_value=dialog_data):
            result = self.plugin._load_dialog_file(mock_path)

            assert result is True
            assert "scene" in self.plugin.dialogs

    def test_load_dialog_file_filename_without_suffix(self) -> None:
        """Test _load_dialog_file with filename without '_dialog(s)' suffix."""
        dialog_data = {"npc1": {"0": {"text": ["Hello"]}}}

        mock_path = MagicMock(spec=Path)
        mock_path.stem = "custom_name"  # No _dialog or _dialogs
        mock_path.name = "custom_name.json"

        with patch("json.load", return_value=dialog_data):
            result = self.plugin._load_dialog_file(mock_path)

            assert result is True
            assert "default" in self.plugin.dialogs

    def test_load_dialog_file_string_level_key_not_convertible(self) -> None:
        """Test _load_dialog_file with string level keys that are not numbers."""
        dialog_data = {"npc1": {"special_state": {"text": ["Special dialog"]}}}

        mock_path = MagicMock(spec=Path)
        mock_path.stem = "scene_dialogs"
        mock_path.name = "scene_dialogs.json"

        with patch("json.load", return_value=dialog_data):
            result = self.plugin._load_dialog_file(mock_path)

            assert result is True
            assert "scene" in self.plugin.dialogs
            assert "npc1" in self.plugin.dialogs["scene"]
            assert "special_state" in self.plugin.dialogs["scene"]["npc1"]

    def test_interact_with_npc_no_dialog_config_returned(self) -> None:
        """Test interact_with_npc when get_dialog returns (None, None)."""
        self.mock_context.dialog_plugin = MagicMock()
        self.mock_scene_plugin.get_current_scene.return_value = "empty_scene"

        mock_sprite = MagicMock()
        self.plugin.register_npc(mock_sprite, "silent_npc")

        # Empty dialogs - get_dialog will return (None, None)
        self.plugin.dialogs = {}

        result = self.plugin.interact_with_npc("silent_npc")

        assert result is False
        self.mock_context.dialog_plugin.show_dialog.assert_not_called()

    def test_get_dialog_exact_match_with_conditions_met_returns_dialog(self) -> None:
        """Test get_dialog returns dialog when exact match has conditions that are met."""
        dialog_config = NPCDialogConfig(text=["Conditional success"], conditions=[{"name": "test"}])
        self.plugin.dialogs = {"scene1": {"npc1": {5: dialog_config}}}

        with patch.object(self.plugin, "_check_dialog_conditions", return_value=True):
            result, fail_actions = self.plugin.get_dialog("npc1", 5, "scene1")

            assert result == dialog_config
            assert fail_actions is None

    def test_get_dialog_fallback_with_conditions_appends_candidates(self) -> None:
        """Test get_dialog fallback includes dialogs with met conditions."""
        dialog_no_cond = NPCDialogConfig(text=["No conditions"])
        dialog_with_cond = NPCDialogConfig(text=["With met conditions"], conditions=[{"name": "test"}])
        self.plugin.dialogs = {"scene1": {"npc1": {1: dialog_no_cond, 2: dialog_with_cond}}}

        with patch.object(self.plugin, "_check_dialog_conditions", return_value=True):
            result, _ = self.plugin.get_dialog("npc1", 10, "scene1")

            # Should find a candidate
            assert result is not None

    def test_get_dialog_fallback_last_resort_first_candidate(self) -> None:
        """Test get_dialog returns first candidate as last resort."""
        # Create numeric dialogs that are all > requested level
        dialog_high = NPCDialogConfig(text=["High level"])
        self.plugin.dialogs = {"scene1": {"npc1": {10: dialog_high}}}

        # Request level 5, but only level 10 exists and is > 5
        result, _ = self.plugin.get_dialog("npc1", 5, "scene1")

        # Should return the only available dialog as last resort
        assert result == dialog_high

    def test_update_animated_npc_direction_left(self) -> None:
        """Test update sets direction to left for animated NPC."""
        npc_sprite = MagicMock(spec=AnimatedNPC)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        npc_sprite.current_direction = "right"
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = False
        self.plugin.register_npc(npc_sprite, "walker")

        # Setup path moving left
        self.plugin.npcs["walker"].path = deque([(80.0, 100.0)])
        self.plugin.npcs["walker"].is_moving = True

        self.plugin.update(0.1)

        npc_sprite.set_direction.assert_called_with("left")

    def test_update_animated_npc_direction_up(self) -> None:
        """Test update sets direction to up for animated NPC."""
        npc_sprite = MagicMock(spec=AnimatedNPC)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        npc_sprite.current_direction = "down"
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = False
        self.plugin.register_npc(npc_sprite, "walker")

        # Setup path moving up (no horizontal movement)
        self.plugin.npcs["walker"].path = deque([(100.0, 120.0)])
        self.plugin.npcs["walker"].is_moving = True

        self.plugin.update(0.1)

        npc_sprite.set_direction.assert_called_with("up")

    def test_update_animated_npc_direction_down(self) -> None:
        """Test update sets direction to down for animated NPC."""
        npc_sprite = MagicMock(spec=AnimatedNPC)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        npc_sprite.current_direction = "up"
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = False
        self.plugin.register_npc(npc_sprite, "walker")

        # Setup path moving down (no horizontal movement)
        self.plugin.npcs["walker"].path = deque([(100.0, 80.0)])
        self.plugin.npcs["walker"].is_moving = True

        self.plugin.update(0.1)

        npc_sprite.set_direction.assert_called_with("down")

    def test_update_animated_npc_direction_unchanged_when_same(self) -> None:
        """Test update doesn't change direction if it's already correct."""
        npc_sprite = MagicMock(spec=AnimatedNPC)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        npc_sprite.current_direction = "right"
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = False
        self.plugin.register_npc(npc_sprite, "walker")

        # Setup path moving right (same as current direction)
        self.plugin.npcs["walker"].path = deque([(120.0, 100.0)])
        self.plugin.npcs["walker"].is_moving = True

        self.plugin.update(0.1)

        # Should not call set_direction since direction didn't change
        npc_sprite.set_direction.assert_not_called()

    def test_load_npcs_from_objects_removes_existing_layer(self) -> None:
        """Test load_npcs_from_objects removes existing NPCs layer from scene."""
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_scene.__contains__ = MagicMock(return_value=True)  # Scene already has NPCs layer
        mock_obj = MagicMock()
        mock_obj.properties = {"name": "Guard", "sprite_sheet": "sprites/guard.png"}
        mock_obj.shape = [100.0, 200.0]

        with (
            patch("pedre.plugins.npc.plugin.AnimatedNPC") as mock_anim_npc_class,
            patch("pedre.plugins.npc.plugin.asset_path", return_value="/assets/sprites/guard.png"),
        ):
            mock_npc_instance = MagicMock()
            mock_npc_instance.visible = True
            mock_anim_npc_class.return_value = mock_npc_instance

            self.plugin.load_npcs_from_objects([mock_obj], mock_scene)

            # Should remove existing NPCs layer before adding new one
            mock_scene.remove_sprite_list_by_name.assert_called_once_with("NPCs")

    def test_apply_npc_state_skips_unknown_npc(self) -> None:
        """Test _apply_npc_state continues when NPC doesn't exist."""
        # Register one NPC
        npc_sprite = MagicMock()
        self.plugin.register_npc(npc_sprite, "known_npc")

        # State includes unknown NPC
        state = {
            "known_npc": {"x": 100.0, "y": 200.0, "visible": True, "dialog_level": 1},
            "unknown_npc": {"x": 300.0, "y": 400.0, "visible": False, "dialog_level": 2},
        }

        self.plugin._apply_npc_state(state)

        # Should apply state to known NPC
        assert npc_sprite.center_x == 100.0
        # Should continue without error for unknown NPC

    def test_load_scene_dialogs_load_returns_false(self) -> None:
        """Test load_scene_dialogs when load_dialogs_from_json returns False."""
        NPCPlugin._dialog_cache.clear()

        with (
            patch.object(self.plugin, "load_dialogs_from_json", return_value=False),
            patch("pedre.plugins.npc.plugin.asset_path", return_value=Path("/assets/dialogs/missing_dialogs.json")),
        ):
            result = self.plugin.load_scene_dialogs("missing_scene")

            # Should return empty dict when load fails
            assert result == {}

    def test_load_dialog_file_scene_already_exists(self) -> None:
        """Test _load_dialog_file when scene already exists in dialogs."""
        # Pre-populate scene
        self.plugin.dialogs["existing_scene"] = {}

        dialog_data = {"npc1": {"0": {"text": ["Hello"]}}}
        mock_path = MagicMock(spec=Path)
        mock_path.stem = "existing_scene_dialogs"
        mock_path.name = "existing_scene_dialogs.json"

        with patch("json.load", return_value=dialog_data):
            result = self.plugin._load_dialog_file(mock_path)

            assert result is True
            # Should add to existing scene
            assert "npc1" in self.plugin.dialogs["existing_scene"]

    def test_load_dialog_file_npc_already_exists_in_scene(self) -> None:
        """Test _load_dialog_file when NPC already exists in scene."""
        # Pre-populate scene and NPC
        self.plugin.dialogs["scene"] = {"npc1": {}}

        dialog_data = {"npc1": {"0": {"text": ["Hello"]}}}
        mock_path = MagicMock(spec=Path)
        mock_path.stem = "scene_dialogs"
        mock_path.name = "scene_dialogs.json"

        with patch("json.load", return_value=dialog_data):
            result = self.plugin._load_dialog_file(mock_path)

            assert result is True
            # Should add to existing NPC
            assert 0 in self.plugin.dialogs["scene"]["npc1"]

    def test_interact_with_npc_with_on_condition_fail_but_no_dialog_plugin(self) -> None:
        """Test interact_with_npc when on_condition_fail exists but no dialog plugin."""
        self.mock_context.dialog_plugin = None
        self.mock_scene_plugin.get_current_scene.return_value = "test_scene"

        mock_sprite = MagicMock()
        self.plugin.register_npc(mock_sprite, "test_npc")

        # Dialog with failing conditions and pre-parsed on_condition_fail action
        mock_action = MagicMock()
        dialog_config = NPCDialogConfig(
            text=["You shall pass"], conditions=[{"name": "has_item"}], on_condition_fail=[mock_action]
        )
        self.plugin.dialogs = {"test_scene": {"test_npc": {0: dialog_config}}}

        with patch.object(self.plugin, "_check_dialog_conditions", return_value=False):
            result = self.plugin.interact_with_npc("test_npc")

            # Should return False when no dialog plugin available (on_condition_fail branch
            # is only reached inside the `if dialog_plugin:` block)
            assert result is False

    def test_get_dialog_fallback_skip_exact_level_in_loop(self) -> None:
        """Test get_dialog skips the exact level when building candidates."""
        # Create multiple dialogs - exact level doesn't exist, so we'll search for candidates
        # This tests the "continue" line when state == dialog_level in the loop
        dialog_level_3 = NPCDialogConfig(text=["Level 3"])
        dialog_level_5 = NPCDialogConfig(text=["Level 5"])
        dialog_level_7 = NPCDialogConfig(text=["Level 7"])
        # All three levels are available, but we request level 5
        self.plugin.dialogs = {"scene1": {"npc1": {3: dialog_level_3, 5: dialog_level_5, 7: dialog_level_7}}}

        # Request level 5 - should find level 5 (no conditions)
        # But let's test when we ask for level 6 - then the loop will skip level 6 (not exists)
        # and consider levels 3, 5, 7
        result, _ = self.plugin.get_dialog("npc1", 6, "scene1")

        # Should find level 5 (highest <= 6)
        assert result == dialog_level_5

    def test_update_animated_npc_no_movement_keeps_direction(self) -> None:
        """Test update when NPC is at exact waypoint position (dx=0, dy=0)."""
        npc_sprite = MagicMock(spec=AnimatedNPC)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        npc_sprite.current_direction = "down"
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = False
        self.plugin.register_npc(npc_sprite, "stationary")

        # Setup path at exact current position (will trigger else branch for direction)
        self.plugin.npcs["stationary"].path = deque([(100.0, 100.0)])
        self.plugin.npcs["stationary"].is_moving = True

        self.plugin.update(0.1)

        # Direction should remain unchanged when dx=0 and dy=0
        # The NPC sprite's current_direction is checked in the else branch
        # Since we're at the exact position, the waypoint will be popped
        assert len(self.plugin.npcs["stationary"].path) == 0

    def test_interact_with_npc_no_dialog_plugin(self) -> None:
        """Test interact_with_npc when dialog_plugin is None (line 417)."""
        self.mock_context.dialog_plugin = None
        self.mock_scene_plugin.get_current_scene.return_value = "village"

        mock_sprite = MagicMock()
        self.plugin.register_npc(mock_sprite, "npc")
        dialog_config = NPCDialogConfig(text=["Hello"])
        self.plugin.dialogs = {"village": {"npc": {0: dialog_config}}}

        result = self.plugin.interact_with_npc("npc")

        # Should return False when no dialog plugin
        assert result is False

    def test_get_dialog_exact_level_match_with_failed_conditions(self) -> None:
        """Test get_dialog when exact level exists but conditions fail (line 413 in interact)."""
        self.mock_context.dialog_plugin = MagicMock()
        self.mock_scene_plugin.get_current_scene.return_value = "castle"

        mock_sprite = MagicMock()
        self.plugin.register_npc(mock_sprite, "guard")

        # Dialog with conditions that will fail, and no on_condition_fail
        dialog_config = NPCDialogConfig(text=["You shall pass"], conditions=[{"name": "has_key"}])
        self.plugin.dialogs = {"castle": {"guard": {0: dialog_config}}}

        with patch.object(self.plugin, "_check_dialog_conditions", return_value=False):
            result = self.plugin.interact_with_npc("guard")

            # Should return False because dialog_data is (None, None) since no on_condition_fail
            assert result is False

    def test_get_dialog_candidates_loop_with_exact_level_skipped(self) -> None:
        """Test get_dialog fallback loop actually skips exact level (line 535)."""
        # This specifically tests the continue statement in the fallback loop
        # Create scenario where exact level has no conditions but we still search candidates
        dialog_level_2 = NPCDialogConfig(text=["Level 2"])
        dialog_level_4 = NPCDialogConfig(text=["Level 4"])
        dialog_level_6 = NPCDialogConfig(text=["Level 6"])
        # Request level 4 which exists - should return it immediately (no fallback)
        # But let's make it request level 5 to trigger fallback that needs to skip exact matches
        self.plugin.dialogs = {"scene": {"npc": {2: dialog_level_2, 4: dialog_level_4, 6: dialog_level_6}}}

        # Request level 5, which doesn't exist - will search candidates and should skip 5 in loop
        result, _ = self.plugin.get_dialog("npc", 5, "scene")

        # Should return level 4 (highest <= 5)
        assert result == dialog_level_4

    def test_mark_npc_as_interacted_creates_new_scene_set(self) -> None:
        """Test mark_npc_as_interacted creates new set for new scene (line 447-448)."""
        self.mock_scene_plugin.get_current_scene.return_value = "new_scene"

        # Initially no scenes in interacted_npcs
        assert "new_scene" not in self.plugin.interacted_npcs

        self.plugin.mark_npc_as_interacted("npc1")

        # Should create new set for scene
        assert "new_scene" in self.plugin.interacted_npcs
        assert "npc1" in self.plugin.interacted_npcs["new_scene"]

    def test_move_npc_to_position_with_empty_path(self) -> None:
        """Test move_npc_to_position when pathfinding returns empty path (line 621)."""
        self.mock_context.pathfinding_plugin = MagicMock()
        npc_sprite = MagicMock()
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        self.plugin.register_npc(npc_sprite, "blocked_npc")

        # Pathfinding returns empty path (unreachable destination)
        self.mock_context.pathfinding_plugin.find_path.return_value = []

        self.plugin.move_npc_to_position("blocked_npc", 200.0, 200.0)

        # NPC should not be moving with empty path
        assert self.plugin.npcs["blocked_npc"].is_moving is False
        assert len(self.plugin.npcs["blocked_npc"].path) == 0

    def test_show_npcs_without_scene_plugin(self) -> None:
        """Test show_npcs when scene_plugin is None (line 641-643)."""
        self.mock_context.scene_plugin = None
        npc_sprite = MagicMock(spec=AnimatedNPC)
        npc_sprite.visible = False
        self.plugin.register_npc(npc_sprite, "npc1")

        # Should not crash when scene_plugin is None
        self.plugin.show_npcs(["npc1"])

        assert npc_sprite.visible is True

    def test_update_movement_complete_without_event_bus(self) -> None:
        """Test update when movement completes but no event bus (line 696)."""
        self.mock_context.event_bus = None
        npc_sprite = MagicMock()
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        self.plugin.register_npc(npc_sprite, "walker")

        # Setup close waypoint
        self.plugin.npcs["walker"].path = deque([(100.5, 100.0)])
        self.plugin.npcs["walker"].is_moving = True

        # Should not crash without event bus
        self.plugin.update(1.0)

        assert self.plugin.npcs["walker"].is_moving is False

    def test_update_appear_complete_without_event_bus(self) -> None:
        """Test update when appear completes but no event bus (line 717)."""
        self.mock_context.event_bus = None
        npc_sprite = MagicMock(spec=AnimatedNPC)
        npc_sprite.appear_complete = True
        npc_sprite.disappear_complete = False
        self.plugin.register_npc(npc_sprite, "appearing")
        self.plugin.npcs["appearing"].appear_event_emitted = False

        # Should not crash without event bus
        self.plugin.update(0.1)

        # Event flag should still be set even without event bus
        assert self.plugin.npcs["appearing"].appear_event_emitted is True

    def test_update_disappear_complete_without_event_bus(self) -> None:
        """Test update when disappear completes but no event bus (line 724)."""
        self.mock_context.event_bus = None
        npc_sprite = MagicMock(spec=AnimatedNPC)
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = True
        self.plugin.register_npc(npc_sprite, "disappearing")
        self.plugin.npcs["disappearing"].disappear_event_emitted = False

        # Should not crash without event bus
        self.plugin.update(0.1)

        # Event flag should still be set even without event bus
        assert self.plugin.npcs["disappearing"].disappear_event_emitted is True

    def test_load_npcs_from_objects_without_scene_plugin(self) -> None:
        """Test load_npcs_from_objects when scene_plugin is None (line 920)."""
        self.mock_context.scene_plugin = None
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {"name": "Guard", "sprite_sheet": "sprites/guard.png"}
        mock_obj.shape = [100.0, 200.0]

        with (
            patch("pedre.plugins.npc.plugin.AnimatedNPC") as mock_anim_npc_class,
            patch("pedre.plugins.npc.plugin.asset_path", return_value="/assets/sprites/guard.png"),
        ):
            mock_npc_instance = MagicMock()
            mock_npc_instance.visible = True
            mock_anim_npc_class.return_value = mock_npc_instance

            # Should not crash without scene_plugin
            self.plugin.load_npcs_from_objects([mock_obj], mock_scene)

            assert "guard" in self.plugin.npcs

    def test_get_save_state_with_regular_sprite(self) -> None:
        """Test get_save_state with non-AnimatedNPC sprite (line 954)."""
        # Regular sprite (not AnimatedNPC)
        npc_sprite = MagicMock(spec=arcade.Sprite)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 200.0
        npc_sprite.visible = True
        self.plugin.register_npc(npc_sprite, "regular_npc")

        save_state = self.plugin.get_save_state()

        # Should not have animation flags for regular sprite
        npc_state = save_state["npcs"]["regular_npc"]
        assert "appear_complete" not in npc_state
        assert "disappear_complete" not in npc_state
        assert "interact_complete" not in npc_state

    def test_cache_scene_state_with_regular_sprite(self) -> None:
        """Test cache_scene_state with non-AnimatedNPC sprite (line 1023)."""
        # Regular sprite (not AnimatedNPC)
        npc_sprite = MagicMock(spec=arcade.Sprite)
        npc_sprite.center_x = 150.0
        npc_sprite.center_y = 250.0
        npc_sprite.visible = False
        self.plugin.register_npc(npc_sprite, "regular_npc")

        state = self.plugin.cache_scene_state("test_scene")

        # Should not have animation flags for regular sprite
        npc_state = state["regular_npc"]
        assert "appear_complete" not in npc_state
        assert "disappear_complete" not in npc_state

    def test_apply_npc_state_with_regular_sprite(self) -> None:
        """Test _apply_npc_state with non-AnimatedNPC sprite (line 1000)."""
        # Regular sprite (not AnimatedNPC)
        npc_sprite = MagicMock(spec=arcade.Sprite)
        self.plugin.register_npc(npc_sprite, "regular_npc")

        state = {"regular_npc": {"x": 300.0, "y": 400.0, "visible": True, "dialog_level": 2}}

        self.plugin._apply_npc_state(state)

        # Should apply state without animation flags
        assert npc_sprite.center_x == 300.0
        assert npc_sprite.center_y == 400.0

    def test_on_key_press_nearby_npc_interact_fails(self) -> None:
        """Test on_key_press when nearby NPC exists but interact_with_npc returns False."""
        self.mock_context.player_plugin = MagicMock()
        player_sprite = MagicMock()
        player_sprite.center_x = 100
        player_sprite.center_y = 100
        self.mock_context.player_plugin.get_player_sprite.return_value = player_sprite

        npc_sprite = MagicMock()
        npc_sprite.center_x = 110
        npc_sprite.center_y = 100
        npc_sprite.visible = True
        self.plugin.register_npc(npc_sprite, "nearby_npc")

        with (
            patch("pedre.plugins.npc.plugin.matches_key", return_value=True),
            patch("pedre.plugins.npc.plugin.arcade.get_distance_between_sprites", return_value=10.0),
            patch.object(self.plugin, "interact_with_npc", return_value=False),
        ):
            result = self.plugin.on_key_press(123, 0)

            assert result is False

    def test_mark_npc_as_interacted_scene_already_exists(self) -> None:
        """Test mark_npc_as_interacted when scene already has an interacted set."""
        self.plugin.interacted_npcs["village"] = {"alice"}

        self.plugin.mark_npc_as_interacted("bob", "village")

        assert self.plugin.interacted_npcs["village"] == {"alice", "bob"}

    def test_update_npc_movement_distance_exactly_zero(self) -> None:
        """Test update when NPC is moving but distance to waypoint is exactly 0 and above threshold."""
        npc_sprite = MagicMock()
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        self.plugin.register_npc(npc_sprite, "stuck")

        self.mock_context.event_bus = MagicMock()
        self.plugin.npcs["stuck"].path = deque([(200.0, 100.0)])
        self.plugin.npcs["stuck"].is_moving = True

        self.plugin.update(0.016)

        # NPC should be actively moving towards the waypoint
        assert npc_sprite.center_x > 100.0
        assert self.plugin.npcs["stuck"].is_moving is True

    def test_apply_entity_state_without_interacted_npcs(self) -> None:
        """Test apply_entity_state when state has no interacted_npcs key."""
        npc_sprite = MagicMock(spec=AnimatedNPC)
        self.plugin.register_npc(npc_sprite, "npc1")
        self.plugin.interacted_npcs = {"old_scene": {"old_npc"}}

        save_data = {
            "npcs": {"npc1": {"x": 10.0, "y": 20.0, "visible": True, "dialog_level": 0}},
        }

        self.plugin.apply_entity_state(save_data)

        # interacted_npcs should remain unchanged since key was missing
        assert self.plugin.interacted_npcs == {"old_scene": {"old_npc"}}


class TestCheckDialogConditions(unittest.TestCase):
    """Test NPCPlugin._check_dialog_conditions."""

    def setUp(self) -> None:
        """Set up the NPCPlugin and mock context."""
        self.plugin = NPCPlugin()
        self.mock_context = MagicMock()
        self.plugin.setup(self.mock_context)

    @patch("pedre.plugins.npc.plugin.ConditionRegistry")
    def test_condition_check_returns_false(self, mock_registry: MagicMock) -> None:
        """Test returns False when a condition parses but its check fails."""
        mock_condition = MagicMock()
        mock_condition.check.return_value = False
        mock_registry.create.return_value = mock_condition

        result = self.plugin._check_dialog_conditions([{"name": "some_condition"}])

        assert result is False
        mock_condition.check.assert_called_once_with(self.mock_context)

    @patch("pedre.plugins.npc.plugin.ConditionRegistry")
    def test_all_conditions_pass(self, mock_registry: MagicMock) -> None:
        """Test returns True when all conditions pass their checks."""
        mock_condition = MagicMock()
        mock_condition.check.return_value = True
        mock_registry.create.return_value = mock_condition

        result = self.plugin._check_dialog_conditions([{"name": "cond_a"}, {"name": "cond_b"}])

        assert result is True
        assert mock_condition.check.call_count == 2


if __name__ == "__main__":
    unittest.main()
