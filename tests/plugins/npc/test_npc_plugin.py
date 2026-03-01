"""Unit tests for NPCPlugin in src/pedre/plugins/npc/plugin.py."""

import json
from collections import deque
from pathlib import Path
from unittest.mock import MagicMock, patch

import arcade
import pytest

from pedre.actions.registry import ActionParseError
from pedre.conditions.registry import ConditionParseError
from pedre.plugins.npc.base import NPCDialogConfig
from pedre.plugins.npc.plugin import NPCPlugin
from pedre.sprites import AnimatedSprite


@pytest.fixture
def npc_plugin_ctx() -> tuple[NPCPlugin, MagicMock]:
    """Create a fresh NPCPlugin with a mock context."""
    plugin = NPCPlugin()
    context = MagicMock()
    plugin.setup(context)
    return plugin, context


class TestNPCPlugin:
    """Test Suite for NPCPlugin."""

    def test_initialization(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test proper initialization of the plugin."""
        plugin, context = npc_plugin_ctx
        assert plugin.name == "npc"
        assert plugin.npcs == {}
        assert plugin.dialogs == {}
        assert plugin.interacted_npcs == {}
        assert plugin.context == context

    def test_register_npc(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test registering an NPC."""
        plugin, _ = npc_plugin_ctx
        mock_sprite = MagicMock()
        npc_name = "guard"

        plugin.register_npc(mock_sprite, npc_name)

        assert npc_name in plugin.npcs
        npc_state = plugin.npcs[npc_name]
        assert npc_state.sprite == mock_sprite
        assert npc_state.name == npc_name
        assert npc_state.dialog_level == 0
        assert not npc_state.is_moving
        assert len(npc_state.path) == 0

    def test_get_nearby_npc(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test finding nearby NPCs."""
        plugin, _ = npc_plugin_ctx

        player_sprite = MagicMock()
        player_sprite.center_x = 100
        player_sprite.center_y = 100

        npc1_sprite = MagicMock()
        npc1_sprite.center_x = 110
        npc1_sprite.center_y = 100
        npc1_sprite.visible = True
        plugin.register_npc(npc1_sprite, "npc1")

        npc2_sprite = MagicMock()
        npc2_sprite.center_x = 500
        npc2_sprite.center_y = 500
        npc2_sprite.visible = True
        plugin.register_npc(npc2_sprite, "npc2")

        npc3_sprite = MagicMock()
        npc3_sprite.center_x = 105
        npc3_sprite.center_y = 100
        npc3_sprite.visible = False
        plugin.register_npc(npc3_sprite, "npc3")

        with patch("pedre.plugins.npc.plugin.arcade.get_distance_between_sprites") as mock_dist:

            def get_dist(_s1: MagicMock, s2: MagicMock) -> float:
                if s2 == npc1_sprite:
                    return 10.0
                if s2 == npc2_sprite:
                    return 400.0
                if s2 == npc3_sprite:
                    return 5.0
                return 1000.0

            mock_dist.side_effect = get_dist

            result = plugin.get_nearby_npc(player_sprite)
            assert result is not None
            sprite, name, _level = result
            assert name == "npc1"
            assert sprite == npc1_sprite

    def test_interact_with_npc_success(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test successful interaction with an NPC."""
        plugin, context = npc_plugin_ctx
        context.scene_plugin.get_current_scene.return_value = "village"

        mock_sprite = MagicMock()
        plugin.register_npc(mock_sprite, "elder")

        dialog_config = NPCDialogConfig(text=["Hello there"], name="Elder One")
        plugin.dialogs = {"village": {"elder": {0: dialog_config}}}

        result = plugin.interact_with_npc("elder")

        assert result is True
        context.dialog_plugin.show_dialog.assert_called_once()
        assert "elder" in plugin.interacted_npcs.get("village", set())

    def test_interact_with_npc_no_dialog(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test interaction when no dialog is available."""
        plugin, context = npc_plugin_ctx
        context.scene_plugin.get_current_scene.return_value = "village"

        mock_sprite = MagicMock()
        plugin.register_npc(mock_sprite, "mime")

        result = plugin.interact_with_npc("mime")

        assert result is False
        context.dialog_plugin.show_dialog.assert_not_called()

    def test_advance_dialog(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test advancing dialog level."""
        plugin, _ = npc_plugin_ctx
        mock_sprite = MagicMock()
        plugin.register_npc(mock_sprite, "quest_giver")

        assert plugin.npcs["quest_giver"].dialog_level == 0

        new_level = plugin.advance_dialog("quest_giver")

        assert new_level == 1
        assert plugin.npcs["quest_giver"].dialog_level == 1

    def test_move_npc_to_tile(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test initiating NPC movement."""
        plugin, context = npc_plugin_ctx
        mock_sprite = MagicMock()
        mock_sprite.center_x = 100
        mock_sprite.center_y = 100
        plugin.register_npc(mock_sprite, "walker")

        path = [(132, 100), (164, 100)]
        context.pathfinding_plugin.find_path.return_value = path

        plugin.move_npc_to_position("walker", 160.0, 160.0)

        assert plugin.npcs["walker"].path == path
        assert plugin.npcs["walker"].is_moving is True
        context.pathfinding_plugin.find_path.assert_called_once()

    def test_cache_scene_state(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test caching scene state."""
        plugin, _ = npc_plugin_ctx
        mock_sprite = MagicMock(spec=AnimatedSprite)
        mock_sprite.center_x = 200.0
        mock_sprite.center_y = 300.0
        mock_sprite.visible = True
        mock_sprite.is_state_complete.side_effect = lambda name: name == "appear"

        plugin.register_npc(mock_sprite, "guard")
        plugin.npcs["guard"].dialog_level = 2

        state = plugin.cache_scene_state("current_scene")

        assert "guard" in state
        guard_state = state["guard"]
        assert guard_state["x"] == 200.0
        assert guard_state["y"] == 300.0
        assert guard_state["visible"] is True
        assert guard_state["dialog_level"] == 2
        assert guard_state["appear_complete"] is True

    def test_restore_scene_state(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test restoring scene state."""
        plugin, _ = npc_plugin_ctx
        mock_sprite = MagicMock(spec=AnimatedSprite)
        plugin.register_npc(mock_sprite, "guard")

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

        plugin.restore_scene_state("scene_name_is_unused_here", state)

        npc = plugin.npcs["guard"]
        assert npc.sprite.center_x == 500.0
        assert npc.sprite.center_y == 600.0
        assert npc.sprite.visible is False
        assert npc.dialog_level == 5

        mock_sprite.mark_state_complete.assert_any_call("appear")
        mock_sprite.mark_state_complete.assert_any_call("disappear")

    def test_get_save_state_includes_history(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test that get_save_state includes global interaction history."""
        plugin, _ = npc_plugin_ctx
        plugin.interacted_npcs = {"village": {"bob", "alice"}, "castle": {"king"}}

        save_data = plugin.get_save_state()

        assert "interacted_npcs" in save_data
        history = save_data["interacted_npcs"]
        assert set(history["village"]) == {"bob", "alice"}
        assert set(history["castle"]) == {"king"}

    def test_apply_entity_state(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test applying entity state (restoring from save)."""
        plugin, _ = npc_plugin_ctx
        mock_sprite = MagicMock(spec=AnimatedSprite)
        plugin.register_npc(mock_sprite, "alice")

        save_data = {
            "npcs": {"alice": {"x": 10.0, "y": 20.0, "visible": True, "dialog_level": 1}},
            "interacted_npcs": {"dungeon": ["goblin"]},
        }

        plugin.apply_entity_state(save_data)

        assert plugin.npcs["alice"].sprite.center_x == 10.0
        assert "goblin" in plugin.interacted_npcs["dungeon"]

    def test_load_from_tiled_no_layer(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_from_tiled when no NPCs layer exists."""
        plugin, _ = npc_plugin_ctx
        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {}
        mock_scene = MagicMock()

        plugin.load_from_tiled(mock_tile_map, mock_scene)

        assert len(plugin.npcs) == 0

    def test_load_from_tiled_with_layer(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_from_tiled when NPCs layer exists."""
        plugin, _ = npc_plugin_ctx
        mock_tile_map = MagicMock()
        mock_npc_obj = MagicMock()
        mock_npc_obj.properties = {"name": "guard", "sprite_sheet": "sprites/guard.png"}
        mock_npc_obj.shape = [100.0, 200.0]
        mock_tile_map.object_lists = {"NPCs": [mock_npc_obj]}
        mock_scene = MagicMock()

        with patch.object(plugin, "load_npcs_from_objects") as mock_load:
            plugin.load_from_tiled(mock_tile_map, mock_scene)
            mock_load.assert_called_once_with([mock_npc_obj], mock_scene)

    def test_cleanup(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test cleanup clears all NPCs and dialogs."""
        plugin, _ = npc_plugin_ctx
        mock_sprite = MagicMock()
        plugin.register_npc(mock_sprite, "test_npc")
        plugin.dialogs = {"scene": {"npc": {0: NPCDialogConfig(text=["test"])}}}

        plugin.cleanup()

        assert len(plugin.npcs) == 0
        assert len(plugin.dialogs) == 0

    def test_reset(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test reset clears all plugin state."""
        plugin, _ = npc_plugin_ctx
        mock_sprite = MagicMock()
        plugin.register_npc(mock_sprite, "test_npc")
        plugin.dialogs = {"scene": {"npc": {0: NPCDialogConfig(text=["test"])}}}
        plugin.interacted_npcs = {"scene": {"npc1"}}

        plugin.reset()

        assert len(plugin.npcs) == 0
        assert len(plugin.dialogs) == 0
        assert len(plugin.interacted_npcs) == 0

    def test_get_npcs(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test get_npcs returns NPC dictionary."""
        plugin, _ = npc_plugin_ctx
        mock_sprite = MagicMock()
        plugin.register_npc(mock_sprite, "npc1")

        npcs = plugin.get_npcs()

        assert "npc1" in npcs
        assert npcs["npc1"].name == "npc1"

    def test_load_dialogs(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_dialogs sets dialog dictionary."""
        plugin, _ = npc_plugin_ctx
        dialogs = {"scene1": {"npc1": {0: NPCDialogConfig(text=["Hello"])}}}

        plugin.load_dialogs(dialogs)

        assert plugin.dialogs == dialogs

    def test_load_scene_dialogs_cached(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_scene_dialogs returns cached dialogs."""
        plugin, _ = npc_plugin_ctx
        dialog_config = NPCDialogConfig(text=["Cached dialog"])
        NPCPlugin._dialog_cache["test_scene"] = {"npc1": {0: dialog_config}}

        result = plugin.load_scene_dialogs("test_scene")

        assert "npc1" in result
        assert result["npc1"][0] == dialog_config
        assert "test_scene" in plugin.dialogs

    def test_load_scene_dialogs_from_file(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_scene_dialogs loads from JSON file."""
        plugin, _ = npc_plugin_ctx
        NPCPlugin._dialog_cache.clear()

        with (
            patch.object(plugin, "load_dialogs_from_json") as mock_load,
            patch("pedre.plugins.npc.plugin.asset_path", return_value=Path("/assets/dialogs/new_scene_dialogs.json")),
        ):

            def side_effect(_path: Path) -> bool:
                plugin.dialogs["new_scene"] = {"npc1": {0: NPCDialogConfig(text=["Test"])}}
                return True

            mock_load.side_effect = side_effect

            plugin.load_scene_dialogs("new_scene")

            assert mock_load.called
            assert "new_scene" in NPCPlugin._dialog_cache

    def test_load_scene_dialogs_file_not_found(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_scene_dialogs when file doesn't exist."""
        plugin, _ = npc_plugin_ctx
        NPCPlugin._dialog_cache.clear()

        with patch.object(plugin, "load_dialogs_from_json") as mock_load:
            mock_load.return_value = False

            result = plugin.load_scene_dialogs("nonexistent")

            assert result == {}

    def test_load_dialogs_from_json_single_file(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test loading dialogs from a single JSON file."""
        plugin, _ = npc_plugin_ctx
        mock_path = MagicMock(spec=Path)
        mock_path.is_file.return_value = True
        mock_path.is_dir.return_value = False
        mock_path.stem = "test_dialogs"
        mock_path.name = "test_dialogs.json"

        with (
            patch("pedre.plugins.npc.plugin.Path", return_value=mock_path),
            patch.object(plugin, "_load_dialog_file", return_value=True) as mock_load_file,
        ):
            result = plugin.load_dialogs_from_json("/fake/test_dialogs.json")

            assert result is True
            mock_load_file.assert_called_once_with(mock_path)

    def test_load_dialogs_from_json_directory(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test loading dialogs from a directory."""
        plugin, _ = npc_plugin_ctx
        with (
            patch("pathlib.Path.is_dir", return_value=True),
            patch("pathlib.Path.glob", return_value=[Path("file1.json"), Path("file2.json")]),
            patch.object(plugin, "_load_dialog_file", return_value=True) as mock_load,
        ):
            result = plugin.load_dialogs_from_json(Path("/fake/dialogs/"))

            assert result is True
            assert mock_load.call_count == 2

    def test_load_dialogs_from_json_empty_directory(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test loading dialogs from empty directory."""
        plugin, _ = npc_plugin_ctx
        with patch("pathlib.Path.is_dir", return_value=True), patch("pathlib.Path.glob", return_value=[]):
            result = plugin.load_dialogs_from_json(Path("/fake/empty/"))

            assert result is False

    def test_load_dialogs_from_json_path_not_found(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test loading dialogs from non-existent path."""
        plugin, _ = npc_plugin_ctx
        with patch("pathlib.Path.is_file", return_value=False), patch("pathlib.Path.is_dir", return_value=False):
            result = plugin.load_dialogs_from_json(Path("/fake/nonexistent"))

            assert result is False

    def test_load_dialog_file_with_conditions(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test loading dialog file with conditions and on_condition_fail actions."""
        plugin, _ = npc_plugin_ctx
        dialog_data = {
            "npc1": {
                "0": {
                    "text": ["Conditional dialog"],
                    "conditions": [{"name": "has_item", "item": "key"}],
                    "on_condition_fail": [{"name": "dialog", "speaker": "Guard", "text": ["You need a key"]}],
                }
            }
        }

        mock_path = MagicMock(spec=Path)
        mock_path.stem = "scene_dialogs"
        mock_path.name = "scene_dialogs.json"

        mock_condition = MagicMock()
        mock_action = MagicMock()
        with (
            patch("json.load", return_value=dialog_data),
            patch("pedre.plugins.npc.plugin.ConditionRegistry.create", return_value=mock_condition),
            patch("pedre.plugins.npc.plugin.ActionRegistry.create", return_value=mock_action),
        ):
            result = plugin._load_dialog_file(mock_path)

            assert result is True
            assert "scene" in plugin.dialogs
            assert "npc1" in plugin.dialogs["scene"]
            config = plugin.dialogs["scene"]["npc1"][0]
            assert config.conditions == [mock_condition]
            assert config.on_condition_fail == [mock_action]

    def test_load_dialog_file_condition_parse_error_skips_condition(
        self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]
    ) -> None:
        """Test that a ConditionParseError during condition parsing is logged and skipped."""
        plugin, _ = npc_plugin_ctx
        dialog_data = {
            "npc1": {
                "0": {
                    "text": ["Hello"],
                    "conditions": [{"name": "bad_condition"}],
                }
            }
        }

        mock_path = MagicMock(spec=Path)
        mock_path.stem = "scene_dialogs"
        mock_path.name = "scene_dialogs.json"

        with (
            patch("json.load", return_value=dialog_data),
            patch(
                "pedre.plugins.npc.plugin.ConditionRegistry.create",
                side_effect=ConditionParseError("unknown condition"),
            ),
        ):
            result = plugin._load_dialog_file(mock_path)

            assert result is True
            config = plugin.dialogs["scene"]["npc1"][0]
            assert config.conditions == []

    def test_load_dialog_file_on_condition_fail_parse_error_skips_action(
        self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]
    ) -> None:
        """Test that an ActionParseError during on_condition_fail parsing is logged and skipped."""
        plugin, _ = npc_plugin_ctx
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
            result = plugin._load_dialog_file(mock_path)

            assert result is True
            config = plugin.dialogs["scene"]["npc1"][0]
            assert config.on_condition_fail == []

    def test_load_dialog_file_json_decode_error(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test loading dialog file with invalid JSON."""
        plugin, _ = npc_plugin_ctx
        mock_path = MagicMock(spec=Path)
        mock_path.stem = "bad"
        mock_path.name = "bad.json"

        with patch("json.load", side_effect=json.JSONDecodeError("msg", "doc", 0)):
            result = plugin._load_dialog_file(mock_path)

            assert result is False

    def test_load_dialog_file_file_not_found(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test loading dialog file that doesn't exist."""
        plugin, _ = npc_plugin_ctx
        mock_path = MagicMock(spec=Path)
        mock_path.stem = "missing"
        mock_path.name = "missing.json"
        mock_path.open.side_effect = FileNotFoundError

        result = plugin._load_dialog_file(mock_path)

        assert result is False

    def test_load_dialog_file_os_error(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test loading dialog file with OS error."""
        plugin, _ = npc_plugin_ctx
        mock_path = MagicMock(spec=Path)
        mock_path.stem = "error"
        mock_path.name = "error.json"
        mock_path.open.side_effect = OSError

        result = plugin._load_dialog_file(mock_path)

        assert result is False

    def test_load_dialog_file_unexpected_error(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test loading dialog file with unexpected error."""
        plugin, _ = npc_plugin_ctx
        mock_path = MagicMock(spec=Path)
        mock_path.stem = "error"
        mock_path.name = "error.json"
        mock_path.open.side_effect = RuntimeError("Unexpected")

        result = plugin._load_dialog_file(mock_path)

        assert result is False

    def test_get_npc_by_name_found(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test getting NPC by name when it exists."""
        plugin, _ = npc_plugin_ctx
        mock_sprite = MagicMock()
        plugin.register_npc(mock_sprite, "alice")

        result = plugin.get_npc_by_name("alice")

        assert result is not None
        assert result.name == "alice"

    def test_get_npc_by_name_not_found(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test getting NPC by name when it doesn't exist."""
        plugin, _ = npc_plugin_ctx
        result = plugin.get_npc_by_name("nonexistent")

        assert result is None

    def test_get_nearby_npc_moving_npc_ignored(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test that moving NPCs are ignored in get_nearby_npc."""
        plugin, _ = npc_plugin_ctx
        player_sprite = MagicMock()
        player_sprite.center_x = 100
        player_sprite.center_y = 100

        npc_sprite = MagicMock()
        npc_sprite.center_x = 105
        npc_sprite.center_y = 100
        npc_sprite.visible = True
        plugin.register_npc(npc_sprite, "moving_npc")
        plugin.npcs["moving_npc"].is_moving = True

        with patch("pedre.plugins.npc.plugin.arcade.get_distance_between_sprites", return_value=5.0):
            result = plugin.get_nearby_npc(player_sprite)

            assert result is None

    def test_on_key_press_interaction_key(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test on_key_press with interaction key."""
        plugin, context = npc_plugin_ctx
        player_sprite = MagicMock()
        player_sprite.center_x = 100
        player_sprite.center_y = 100
        context.player_plugin.get_player_sprite.return_value = player_sprite

        npc_sprite = MagicMock()
        npc_sprite.center_x = 110
        npc_sprite.center_y = 100
        npc_sprite.visible = True
        plugin.register_npc(npc_sprite, "nearby_npc")

        with (
            patch("pedre.plugins.npc.plugin.matches_key", return_value=True),
            patch("pedre.plugins.npc.plugin.arcade.get_distance_between_sprites", return_value=10.0),
            patch.object(plugin, "interact_with_npc", return_value=True) as mock_interact,
        ):
            result = plugin.on_key_press(123, 0)

            assert result is True
            mock_interact.assert_called_once_with("nearby_npc")

    def test_on_key_press_no_player(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test on_key_press when player doesn't exist."""
        plugin, context = npc_plugin_ctx
        context.player_plugin.get_player_sprite.return_value = None

        with patch("pedre.plugins.npc.plugin.matches_key", return_value=True):
            result = plugin.on_key_press(123, 0)

            assert result is False

    def test_on_key_press_no_nearby_npc(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test on_key_press when no NPC is nearby."""
        plugin, context = npc_plugin_ctx
        player_sprite = MagicMock()
        context.player_plugin.get_player_sprite.return_value = player_sprite

        with (
            patch("pedre.plugins.npc.plugin.matches_key", return_value=True),
            patch.object(plugin, "get_nearby_npc", return_value=None),
        ):
            result = plugin.on_key_press(123, 0)

            assert result is False

    def test_on_key_press_wrong_key(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test on_key_press with wrong key."""
        plugin, _ = npc_plugin_ctx
        with patch("pedre.plugins.npc.plugin.matches_key", return_value=False):
            result = plugin.on_key_press(456, 0)

            assert result is False

    def test_interact_with_npc_no_npc(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test interaction with non-existent NPC."""
        plugin, _ = npc_plugin_ctx
        result = plugin.interact_with_npc("nonexistent")

        assert result is False

    def test_interact_with_npc_condition_fail_delegates_to_script_plugin(
        self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]
    ) -> None:
        """Test interaction when conditions fail delegates on_condition_fail to ScriptPlugin."""
        plugin, context = npc_plugin_ctx
        context.scene_plugin.get_current_scene.return_value = "dungeon"

        mock_sprite = MagicMock()
        plugin.register_npc(mock_sprite, "guard")

        mock_action = MagicMock()
        dialog_config = NPCDialogConfig(
            text=["You shall pass"],
            conditions=[MagicMock()],
            on_condition_fail=[mock_action],
        )
        plugin.dialogs = {"dungeon": {"guard": {0: dialog_config}}}

        with patch.object(plugin, "_check_dialog_conditions", return_value=False):
            result = plugin.interact_with_npc("guard")

            assert result is True
            context.script_plugin.run_actions.assert_called_once_with("npc_guard_condition_fail", [mock_action])
            context.dialog_plugin.show_dialog.assert_not_called()

    def test_mark_npc_as_interacted_with_scene(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test marking NPC as interacted with specific scene."""
        plugin, _ = npc_plugin_ctx
        plugin.mark_npc_as_interacted("alice", "village")

        assert "alice" in plugin.interacted_npcs["village"]

    def test_mark_npc_as_interacted_default_scene(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test marking NPC as interacted using current scene."""
        plugin, context = npc_plugin_ctx
        context.scene_plugin.get_current_scene.return_value = "castle"

        plugin.mark_npc_as_interacted("bob")

        assert "bob" in plugin.interacted_npcs["castle"]

    def test_has_npc_been_interacted_with_true(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test checking if NPC has been interacted with."""
        plugin, _ = npc_plugin_ctx
        plugin.interacted_npcs = {"forest": {"npc1"}}

        result = plugin.has_npc_been_interacted_with("npc1", "forest")

        assert result is True

    def test_has_npc_been_interacted_with_false(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test checking if NPC has not been interacted with."""
        plugin, _ = npc_plugin_ctx
        plugin.interacted_npcs = {"forest": {"npc1"}}

        result = plugin.has_npc_been_interacted_with("npc2", "forest")

        assert result is False

    def test_has_npc_been_interacted_with_default_scene(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test checking interaction with default scene."""
        plugin, context = npc_plugin_ctx
        context.scene_plugin.get_current_scene.return_value = "desert"
        plugin.interacted_npcs = {"desert": {"npc1"}}

        result = plugin.has_npc_been_interacted_with("npc1")

        assert result is True

    def test_check_dialog_conditions_returns_false_when_condition_fails(
        self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]
    ) -> None:
        """Test returns False when a condition check fails."""
        plugin, context = npc_plugin_ctx
        mock_condition = MagicMock()
        mock_condition.check.return_value = False

        result = plugin._check_dialog_conditions([mock_condition])

        assert result is False
        mock_condition.check.assert_called_once_with(context)

    def test_get_dialog_with_scene_fallback(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test get_dialog falls back to default scene."""
        plugin, _ = npc_plugin_ctx
        dialog_config = NPCDialogConfig(text=["Default dialog"])
        plugin.dialogs = {"default": {"npc1": {0: dialog_config}}}

        result, fail_actions = plugin.get_dialog("npc1", 0, "nonexistent_scene")

        assert result == dialog_config
        assert fail_actions is None

    def test_get_dialog_npc_not_found(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test get_dialog with non-existent NPC."""
        plugin, _ = npc_plugin_ctx
        plugin.dialogs = {"scene1": {}}

        result, fail_actions = plugin.get_dialog("nonexistent", 0, "scene1")

        assert result is None
        assert fail_actions is None

    def test_get_dialog_condition_failed_returns_actions(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test get_dialog returns on_condition_fail actions (pre-parsed Action objects)."""
        plugin, _ = npc_plugin_ctx
        mock_action = MagicMock()
        fail_actions = [mock_action]
        dialog_config = NPCDialogConfig(text=["Success"], conditions=[MagicMock()], on_condition_fail=fail_actions)
        plugin.dialogs = {"scene1": {"npc1": {0: dialog_config}}}

        with patch.object(plugin, "_check_dialog_conditions", return_value=False):
            result, returned_actions = plugin.get_dialog("npc1", 0, "scene1")

            assert result is None
            assert returned_actions == fail_actions

    def test_get_dialog_fallback_to_string_key(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test get_dialog fallback prefers string keys."""
        plugin, _ = npc_plugin_ctx
        string_dialog = NPCDialogConfig(text=["String key dialog"])
        numeric_dialog = NPCDialogConfig(text=["Numeric dialog"])
        plugin.dialogs = {"scene1": {"npc1": {"1_special": string_dialog, 0: numeric_dialog}}}

        result, _ = plugin.get_dialog("npc1", 5, "scene1")

        assert result == string_dialog

    def test_get_dialog_fallback_to_numeric_progression(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test get_dialog fallback to numeric progression."""
        plugin, _ = npc_plugin_ctx
        dialog_level_1 = NPCDialogConfig(text=["Level 1"])
        dialog_level_3 = NPCDialogConfig(text=["Level 3"])
        plugin.dialogs = {"scene1": {"npc1": {1: dialog_level_1, 3: dialog_level_3}}}

        result, _ = plugin.get_dialog("npc1", 5, "scene1")

        assert result == dialog_level_3

    def test_get_dialog_no_candidates(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test get_dialog when no candidates with met conditions."""
        plugin, _ = npc_plugin_ctx
        dialog_config = NPCDialogConfig(text=["Conditional"], conditions=[MagicMock()])
        plugin.dialogs = {"scene1": {"npc1": {0: dialog_config}}}

        with patch.object(plugin, "_check_dialog_conditions", return_value=False):
            result, _ = plugin.get_dialog("npc1", 5, "scene1")

            assert result is None

    def test_advance_dialog_unknown_npc(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test advancing dialog for unknown NPC."""
        plugin, _ = npc_plugin_ctx
        result = plugin.advance_dialog("nonexistent")

        assert result == 0

    def test_move_npc_to_position_unknown_npc(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test moving unknown NPC."""
        plugin, _ = npc_plugin_ctx
        plugin.move_npc_to_position("nonexistent", 100.0, 100.0)

    def test_move_npc_to_position_no_pathfinding(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test moving NPC when pathfinding is unavailable."""
        plugin, context = npc_plugin_ctx
        mock_sprite = MagicMock()
        plugin.register_npc(mock_sprite, "npc1")
        context.pathfinding_plugin = None

        plugin.move_npc_to_position("npc1", 100.0, 100.0)

    def test_move_npc_to_position_excludes_moving_npcs(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test move_npc_to_position excludes other moving NPCs."""
        plugin, context = npc_plugin_ctx

        npc1_sprite = MagicMock()
        npc1_sprite.center_x = 100
        npc1_sprite.center_y = 100
        plugin.register_npc(npc1_sprite, "npc1")

        npc2_sprite = MagicMock()
        plugin.register_npc(npc2_sprite, "npc2")
        plugin.npcs["npc2"].is_moving = True

        context.pathfinding_plugin.find_path.return_value = [(120, 100)]

        plugin.move_npc_to_position("npc1", 120.0, 100.0)

        call_args = context.pathfinding_plugin.find_path.call_args
        assert npc2_sprite in call_args.kwargs["exclude_sprites"]

    def test_show_npcs_makes_visible(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test show_npcs makes hidden NPCs visible."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock()
        npc_sprite.visible = False
        plugin.register_npc(npc_sprite, "hidden_npc")

        plugin.show_npcs(["hidden_npc"])

        assert npc_sprite.visible is True

    def test_show_npcs_starts_animation(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test show_npcs starts appear animation for AnimatedNPC."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock(spec=AnimatedSprite)
        npc_sprite.visible = False
        npc_sprite.has_state.return_value = True
        plugin.register_npc(npc_sprite, "animated_npc")

        plugin.show_npcs(["animated_npc"])

        assert npc_sprite.visible is True
        npc_sprite.request_state.assert_called_once_with("appear")

    def test_show_npcs_adds_to_wall_list(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test show_npcs adds NPC to wall list."""
        plugin, context = npc_plugin_ctx
        npc_sprite = MagicMock(spec=AnimatedSprite)
        npc_sprite.visible = False
        plugin.register_npc(npc_sprite, "npc1")

        plugin.show_npcs(["npc1"])

        context.scene_plugin.add_to_wall_list.assert_called_once_with(npc_sprite)

    def test_show_npcs_already_visible(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test show_npcs skips already visible NPCs."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock(spec=AnimatedSprite)
        npc_sprite.visible = True
        plugin.register_npc(npc_sprite, "visible_npc")

        plugin.show_npcs(["visible_npc"])

        npc_sprite.request_state.assert_not_called()

    def test_show_npcs_unknown_npc(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test show_npcs with unknown NPC."""
        plugin, _ = npc_plugin_ctx
        plugin.show_npcs(["nonexistent"])

    def test_update_npc_movement_reaches_waypoint(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test update when NPC reaches a waypoint."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock()
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        plugin.register_npc(npc_sprite, "walker")

        plugin.npcs["walker"].path = deque([(101.0, 100.0), (120.0, 100.0)])
        plugin.npcs["walker"].is_moving = True

        plugin.update(1.0)

        assert len(plugin.npcs["walker"].path) == 1
        assert plugin.npcs["walker"].is_moving is True

    def test_update_npc_movement_completes(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test update when NPC completes movement."""
        plugin, context = npc_plugin_ctx
        npc_sprite = MagicMock()
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        plugin.register_npc(npc_sprite, "walker")

        plugin.npcs["walker"].path = deque([(100.5, 100.0)])
        plugin.npcs["walker"].is_moving = True

        plugin.update(1.0)

        assert len(plugin.npcs["walker"].path) == 0
        assert plugin.npcs["walker"].is_moving is False
        context.event_bus.publish.assert_called_once()

    def test_update_animated_npc_direction(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test update changes animated NPC direction based on movement."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock(spec=AnimatedSprite)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        npc_sprite.current_direction = "down"
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = False
        plugin.register_npc(npc_sprite, "animated")

        plugin.npcs["animated"].path = deque([(120.0, 100.0)])
        plugin.npcs["animated"].is_moving = True

        plugin.update(0.1)

        npc_sprite.set_direction.assert_called_with("right")

    def test_update_animated_npc_appear_event(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test update emits appear complete event."""
        plugin, context = npc_plugin_ctx
        npc_sprite = MagicMock(spec=AnimatedSprite)
        npc_sprite.appear_complete = True
        npc_sprite.disappear_complete = False
        plugin.register_npc(npc_sprite, "appearing")
        plugin.npcs["appearing"].appear_event_emitted = False

        plugin.update(0.1)

        assert any("NPCAppearCompleteEvent" in str(call) for call in context.event_bus.publish.call_args_list)
        assert plugin.npcs["appearing"].appear_event_emitted is True

    def test_update_animated_npc_disappear_event(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test update emits disappear complete event."""
        plugin, context = npc_plugin_ctx
        npc_sprite = MagicMock(spec=AnimatedSprite)
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = True
        plugin.register_npc(npc_sprite, "disappearing")
        plugin.npcs["disappearing"].disappear_event_emitted = False

        plugin.update(0.1)

        assert any("NPCDisappearCompleteEvent" in str(call) for call in context.event_bus.publish.call_args_list)
        assert plugin.npcs["disappearing"].disappear_event_emitted is True

    def test_get_npc_positions(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test get_npc_positions returns all NPC positions."""
        plugin, _ = npc_plugin_ctx
        npc1_sprite = MagicMock()
        npc1_sprite.center_x = 100.0
        npc1_sprite.center_y = 200.0
        npc1_sprite.visible = True
        plugin.register_npc(npc1_sprite, "npc1")

        npc2_sprite = MagicMock()
        npc2_sprite.center_x = 300.0
        npc2_sprite.center_y = 400.0
        npc2_sprite.visible = False
        plugin.register_npc(npc2_sprite, "npc2")

        positions = plugin.get_npc_positions()

        assert positions["npc1"]["x"] == 100.0
        assert positions["npc1"]["y"] == 200.0
        assert positions["npc1"]["visible"] is True
        assert positions["npc2"]["visible"] is False

    def test_restore_positions(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test _restore_positions updates NPC sprites."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock()
        plugin.register_npc(npc_sprite, "npc1")

        positions = {"npc1": {"x": 500.0, "y": 600.0, "visible": False}}

        plugin._restore_positions(positions)

        assert npc_sprite.center_x == 500.0
        assert npc_sprite.center_y == 600.0
        assert npc_sprite.visible is False

    def test_restore_positions_unknown_npc(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test _restore_positions with unknown NPC."""
        plugin, _ = npc_plugin_ctx
        positions = {"nonexistent": {"x": 100.0, "y": 200.0, "visible": True}}

        plugin._restore_positions(positions)

    def test_has_moving_npcs_true(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test has_moving_npcs returns True when NPCs are moving."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock()
        plugin.register_npc(npc_sprite, "walker")
        plugin.npcs["walker"].is_moving = True

        result = plugin.has_moving_npcs()

        assert result is True

    def test_has_moving_npcs_false(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test has_moving_npcs returns False when no NPCs are moving."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock()
        plugin.register_npc(npc_sprite, "static")
        plugin.npcs["static"].is_moving = False

        result = plugin.has_moving_npcs()

        assert result is False

    def test_load_npcs_from_objects_creates_npcs(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_npcs_from_objects creates NPC sprites."""
        plugin, _ = npc_plugin_ctx
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {
            "name": "Guard",
            "sprite_sheet": "sprites/guard.png",
            "tile_size": 32,
            "scale": 2.0,
        }
        mock_obj.shape = [100.0, 200.0]

        mock_npc_instance = MagicMock()
        mock_npc_instance.visible = True
        with patch.object(plugin, "_create_npc_sprite", return_value=mock_npc_instance):
            plugin.load_npcs_from_objects([mock_obj], mock_scene)

            assert "guard" in plugin.npcs

    def test_load_npcs_from_objects_no_properties(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_npcs_from_objects skips objects without properties."""
        plugin, _ = npc_plugin_ctx
        mock_scene = MagicMock()
        mock_obj = MagicMock()
        mock_obj.properties = None

        plugin.load_npcs_from_objects([mock_obj], mock_scene)

        assert len(plugin.npcs) == 0

    def test_load_npcs_from_objects_no_name(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_npcs_from_objects skips objects without name."""
        plugin, _ = npc_plugin_ctx
        mock_scene = MagicMock()
        mock_obj = MagicMock()
        mock_obj.properties = {"sprite_sheet": "test.png"}

        plugin.load_npcs_from_objects([mock_obj], mock_scene)

        assert len(plugin.npcs) == 0

    def test_load_npcs_from_objects_no_sprite_sheet(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_npcs_from_objects skips objects without sprite_sheet."""
        plugin, _ = npc_plugin_ctx
        mock_scene = MagicMock()
        mock_obj = MagicMock()
        mock_obj.properties = {"name": "Guard"}
        mock_obj.shape = [100.0, 200.0]

        plugin.load_npcs_from_objects([mock_obj], mock_scene)

        assert len(plugin.npcs) == 0

    def test_load_npcs_from_objects_initially_hidden(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_npcs_from_objects handles initially_hidden flag."""
        plugin, _ = npc_plugin_ctx
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {
            "name": "HiddenGuard",
            "sprite_sheet": "sprites/guard.png",
            "initially_hidden": True,
        }
        mock_obj.shape = [100.0, 200.0]

        mock_npc_instance = MagicMock()
        with patch.object(plugin, "_create_npc_sprite", return_value=mock_npc_instance):
            plugin.load_npcs_from_objects([mock_obj], mock_scene)

            assert mock_npc_instance.visible is False

    def test_load_npcs_from_objects_adds_to_wall_list(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_npcs_from_objects adds visible NPCs to wall list."""
        plugin, context = npc_plugin_ctx
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {"name": "Guard", "sprite_sheet": "sprites/guard.png"}
        mock_obj.shape = [100.0, 200.0]

        mock_npc_instance = MagicMock()
        mock_npc_instance.visible = True
        with patch.object(plugin, "_create_npc_sprite", return_value=mock_npc_instance):
            plugin.load_npcs_from_objects([mock_obj], mock_scene)

            context.scene_plugin.add_to_wall_list.assert_called_once_with(mock_npc_instance)

    def test_load_npcs_from_objects_invalid_tile_size(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_npcs_from_objects handles invalid tile_size and passes None to _create_npc_sprite."""
        plugin, _ = npc_plugin_ctx
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {
            "name": "Guard",
            "sprite_sheet": "sprites/guard.png",
            "tile_size": "invalid",
        }
        mock_obj.shape = [100.0, 200.0]

        mock_npc_instance = MagicMock()
        mock_npc_instance.visible = True
        with patch.object(plugin, "_create_npc_sprite", return_value=mock_npc_instance) as mock_create:
            plugin.load_npcs_from_objects([mock_obj], mock_scene)

            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs.get("tile_size") is None

    def test_load_npcs_from_objects_invalid_scale(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_npcs_from_objects handles invalid scale and passes None to _create_npc_sprite."""
        plugin, _ = npc_plugin_ctx
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {
            "name": "Guard",
            "sprite_sheet": "sprites/guard.png",
            "scale": "invalid",
        }
        mock_obj.shape = [100.0, 200.0]

        mock_npc_instance = MagicMock()
        mock_npc_instance.visible = True
        with patch.object(plugin, "_create_npc_sprite", return_value=mock_npc_instance) as mock_create:
            plugin.load_npcs_from_objects([mock_obj], mock_scene)

            call_kwargs = mock_create.call_args.kwargs
            assert call_kwargs.get("scale") is None

    def test_load_npcs_from_objects_animation_properties(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_npcs_from_objects passes animation properties to _create_npc_sprite."""
        plugin, _ = npc_plugin_ctx
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {
            "name": "Guard",
            "sprite_sheet": "sprites/guard.png",
            "idle_up_frames": 4,
            "walk_down_frames": 8,
        }
        mock_obj.shape = [100.0, 200.0]

        mock_npc_instance = MagicMock()
        mock_npc_instance.visible = True
        with patch.object(plugin, "_create_npc_sprite", return_value=mock_npc_instance) as mock_create:
            plugin.load_npcs_from_objects([mock_obj], mock_scene)

            mock_create.assert_called_once()

    def test_load_npcs_from_objects_invalid_animation_property(
        self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]
    ) -> None:
        """Test load_npcs_from_objects skips invalid animation properties."""
        plugin, _ = npc_plugin_ctx
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {
            "name": "Guard",
            "sprite_sheet": "sprites/guard.png",
            "idle_up_frames": "invalid",
        }
        mock_obj.shape = [100.0, 200.0]

        mock_npc_instance = MagicMock()
        mock_npc_instance.visible = True
        with patch.object(plugin, "_create_npc_sprite", return_value=mock_npc_instance) as mock_create:
            plugin.load_npcs_from_objects([mock_obj], mock_scene)

            mock_create.assert_called_once()

    def test_load_npcs_from_objects_creation_failure(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_npcs_from_objects handles sprite creation failure."""
        plugin, _ = npc_plugin_ctx
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {"name": "BrokenGuard", "sprite_sheet": "sprites/guard.png"}
        mock_obj.shape = [100.0, 200.0]

        with patch.object(plugin, "_create_npc_sprite", side_effect=Exception("Creation failed")):
            plugin.load_npcs_from_objects([mock_obj], mock_scene)

            assert "brokenguard" not in plugin.npcs

    def test_get_save_state_with_animated_npcs(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test get_save_state includes animation flags for AnimatedNPC."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock(spec=AnimatedSprite)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 200.0
        npc_sprite.visible = True
        npc_sprite.is_state_complete.side_effect = lambda name: name in ("appear", "interact")
        plugin.register_npc(npc_sprite, "animated")

        save_state = plugin.get_save_state()

        npc_state = save_state["npcs"]["animated"]
        assert npc_state["appear_complete"] is True
        assert npc_state["disappear_complete"] is False
        assert npc_state["interact_complete"] is True

    def test_restore_save_state(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test restore_save_state (phase 1 - should do nothing)."""
        plugin, _ = npc_plugin_ctx
        state = {"npcs": {}, "interacted_npcs": {}}

        plugin.restore_save_state(state)

    def test_apply_entity_state_restores_animation_flags(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test apply_entity_state restores animation flags for AnimatedNPC."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock(spec=AnimatedSprite)
        plugin.register_npc(npc_sprite, "animated")

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

        plugin.apply_entity_state(save_data)

        npc_sprite.mark_state_complete.assert_any_call("appear")
        npc_sprite.mark_state_complete.assert_any_call("disappear")
        # interact_complete is False so mark_state_complete should not be called for it
        assert not any(
            call.args == ("interact",) for call in npc_sprite.mark_state_complete.call_args_list
        )

    def test_load_scene_dialogs_exception_handling(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_scene_dialogs handles exceptions during load."""
        plugin, _ = npc_plugin_ctx
        NPCPlugin._dialog_cache.clear()

        with (
            patch.object(plugin, "load_dialogs_from_json", side_effect=RuntimeError("Unexpected error")),
            patch("pedre.plugins.npc.plugin.asset_path", return_value=Path("/assets/dialogs/error_scene_dialogs.json")),
        ):
            result = plugin.load_scene_dialogs("error_scene")

            assert result == {}

    def test_load_dialog_file_filename_with_dialog_suffix(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test _load_dialog_file with '_dialog' (singular) in filename."""
        plugin, _ = npc_plugin_ctx
        dialog_data = {"npc1": {"0": {"text": ["Hello"]}}}

        mock_path = MagicMock(spec=Path)
        mock_path.stem = "scene_dialog"
        mock_path.name = "scene_dialog.json"

        with patch("json.load", return_value=dialog_data):
            result = plugin._load_dialog_file(mock_path)

            assert result is True
            assert "scene" in plugin.dialogs

    def test_load_dialog_file_filename_without_suffix(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test _load_dialog_file with filename without '_dialog(s)' suffix."""
        plugin, _ = npc_plugin_ctx
        dialog_data = {"npc1": {"0": {"text": ["Hello"]}}}

        mock_path = MagicMock(spec=Path)
        mock_path.stem = "custom_name"
        mock_path.name = "custom_name.json"

        with patch("json.load", return_value=dialog_data):
            result = plugin._load_dialog_file(mock_path)

            assert result is True
            assert "default" in plugin.dialogs

    def test_load_dialog_file_string_level_key_not_convertible(
        self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]
    ) -> None:
        """Test _load_dialog_file with string level keys that are not numbers."""
        plugin, _ = npc_plugin_ctx
        dialog_data = {"npc1": {"special_state": {"text": ["Special dialog"]}}}

        mock_path = MagicMock(spec=Path)
        mock_path.stem = "scene_dialogs"
        mock_path.name = "scene_dialogs.json"

        with patch("json.load", return_value=dialog_data):
            result = plugin._load_dialog_file(mock_path)

            assert result is True
            assert "scene" in plugin.dialogs
            assert "npc1" in plugin.dialogs["scene"]
            assert "special_state" in plugin.dialogs["scene"]["npc1"]

    def test_interact_with_npc_no_dialog_config_returned(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test interact_with_npc when get_dialog returns (None, None)."""
        plugin, context = npc_plugin_ctx
        context.scene_plugin.get_current_scene.return_value = "empty_scene"

        mock_sprite = MagicMock()
        plugin.register_npc(mock_sprite, "silent_npc")
        plugin.dialogs = {}

        result = plugin.interact_with_npc("silent_npc")

        assert result is False
        context.dialog_plugin.show_dialog.assert_not_called()

    def test_get_dialog_exact_match_with_conditions_met_returns_dialog(
        self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]
    ) -> None:
        """Test get_dialog returns dialog when exact match has conditions that are met."""
        plugin, _ = npc_plugin_ctx
        dialog_config = NPCDialogConfig(text=["Conditional success"], conditions=[MagicMock()])
        plugin.dialogs = {"scene1": {"npc1": {5: dialog_config}}}

        with patch.object(plugin, "_check_dialog_conditions", return_value=True):
            result, fail_actions = plugin.get_dialog("npc1", 5, "scene1")

            assert result == dialog_config
            assert fail_actions is None

    def test_get_dialog_fallback_with_conditions_appends_candidates(
        self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]
    ) -> None:
        """Test get_dialog fallback includes dialogs with met conditions."""
        plugin, _ = npc_plugin_ctx
        dialog_no_cond = NPCDialogConfig(text=["No conditions"])
        dialog_with_cond = NPCDialogConfig(text=["With met conditions"], conditions=[MagicMock()])
        plugin.dialogs = {"scene1": {"npc1": {1: dialog_no_cond, 2: dialog_with_cond}}}

        with patch.object(plugin, "_check_dialog_conditions", return_value=True):
            result, _ = plugin.get_dialog("npc1", 10, "scene1")

            assert result is not None

    def test_get_dialog_fallback_last_resort_first_candidate(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test get_dialog returns first candidate as last resort."""
        plugin, _ = npc_plugin_ctx
        dialog_high = NPCDialogConfig(text=["High level"])
        plugin.dialogs = {"scene1": {"npc1": {10: dialog_high}}}

        result, _ = plugin.get_dialog("npc1", 5, "scene1")

        assert result == dialog_high

    def test_update_animated_npc_direction_left(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test update sets direction to left for animated NPC."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock(spec=AnimatedSprite)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        npc_sprite.current_direction = "right"
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = False
        plugin.register_npc(npc_sprite, "walker")

        plugin.npcs["walker"].path = deque([(80.0, 100.0)])
        plugin.npcs["walker"].is_moving = True

        plugin.update(0.1)

        npc_sprite.set_direction.assert_called_with("left")

    def test_update_animated_npc_direction_up(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test update sets direction to up for animated NPC."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock(spec=AnimatedSprite)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        npc_sprite.current_direction = "down"
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = False
        plugin.register_npc(npc_sprite, "walker")

        plugin.npcs["walker"].path = deque([(100.0, 120.0)])
        plugin.npcs["walker"].is_moving = True

        plugin.update(0.1)

        npc_sprite.set_direction.assert_called_with("up")

    def test_update_animated_npc_direction_down(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test update sets direction to down for animated NPC."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock(spec=AnimatedSprite)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        npc_sprite.current_direction = "up"
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = False
        plugin.register_npc(npc_sprite, "walker")

        plugin.npcs["walker"].path = deque([(100.0, 80.0)])
        plugin.npcs["walker"].is_moving = True

        plugin.update(0.1)

        npc_sprite.set_direction.assert_called_with("down")

    def test_update_animated_npc_direction_unchanged_when_same(
        self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]
    ) -> None:
        """Test update doesn't change direction if it's already correct."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock(spec=AnimatedSprite)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        npc_sprite.current_direction = "right"
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = False
        plugin.register_npc(npc_sprite, "walker")

        plugin.npcs["walker"].path = deque([(120.0, 100.0)])
        plugin.npcs["walker"].is_moving = True

        plugin.update(0.1)

        npc_sprite.set_direction.assert_not_called()

    def test_load_npcs_from_objects_removes_existing_layer(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_npcs_from_objects removes existing NPCs layer from scene."""
        plugin, _ = npc_plugin_ctx
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_scene.__contains__ = MagicMock(return_value=True)
        mock_obj = MagicMock()
        mock_obj.properties = {"name": "Guard", "sprite_sheet": "sprites/guard.png"}
        mock_obj.shape = [100.0, 200.0]

        mock_npc_instance = MagicMock()
        mock_npc_instance.visible = True
        with patch.object(plugin, "_create_npc_sprite", return_value=mock_npc_instance):
            plugin.load_npcs_from_objects([mock_obj], mock_scene)

            mock_scene.remove_sprite_list_by_name.assert_called_once_with("NPCs")

    def test_apply_npc_state_skips_unknown_npc(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test _apply_npc_state continues when NPC doesn't exist."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock()
        plugin.register_npc(npc_sprite, "known_npc")

        state = {
            "known_npc": {"x": 100.0, "y": 200.0, "visible": True, "dialog_level": 1},
            "unknown_npc": {"x": 300.0, "y": 400.0, "visible": False, "dialog_level": 2},
        }

        plugin._apply_npc_state(state)

        assert npc_sprite.center_x == 100.0

    def test_load_scene_dialogs_load_returns_false(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_scene_dialogs when load_dialogs_from_json returns False."""
        plugin, _ = npc_plugin_ctx
        NPCPlugin._dialog_cache.clear()

        with (
            patch.object(plugin, "load_dialogs_from_json", return_value=False),
            patch("pedre.plugins.npc.plugin.asset_path", return_value=Path("/assets/dialogs/missing_dialogs.json")),
        ):
            result = plugin.load_scene_dialogs("missing_scene")

            assert result == {}

    def test_load_dialog_file_scene_already_exists(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test _load_dialog_file when scene already exists in dialogs."""
        plugin, _ = npc_plugin_ctx
        plugin.dialogs["existing_scene"] = {}

        dialog_data = {"npc1": {"0": {"text": ["Hello"]}}}
        mock_path = MagicMock(spec=Path)
        mock_path.stem = "existing_scene_dialogs"
        mock_path.name = "existing_scene_dialogs.json"

        with patch("json.load", return_value=dialog_data):
            result = plugin._load_dialog_file(mock_path)

            assert result is True
            assert "npc1" in plugin.dialogs["existing_scene"]

    def test_load_dialog_file_npc_already_exists_in_scene(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test _load_dialog_file when NPC already exists in scene."""
        plugin, _ = npc_plugin_ctx
        plugin.dialogs["scene"] = {"npc1": {}}

        dialog_data = {"npc1": {"0": {"text": ["Hello"]}}}
        mock_path = MagicMock(spec=Path)
        mock_path.stem = "scene_dialogs"
        mock_path.name = "scene_dialogs.json"

        with patch("json.load", return_value=dialog_data):
            result = plugin._load_dialog_file(mock_path)

            assert result is True
            assert 0 in plugin.dialogs["scene"]["npc1"]

    def test_interact_with_npc_with_on_condition_fail_but_no_dialog_plugin(
        self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]
    ) -> None:
        """Test interact_with_npc when on_condition_fail exists but no dialog plugin."""
        plugin, context = npc_plugin_ctx
        context.dialog_plugin = None
        context.scene_plugin.get_current_scene.return_value = "test_scene"

        mock_sprite = MagicMock()
        plugin.register_npc(mock_sprite, "test_npc")

        mock_action = MagicMock()
        dialog_config = NPCDialogConfig(
            text=["You shall pass"], conditions=[MagicMock()], on_condition_fail=[mock_action]
        )
        plugin.dialogs = {"test_scene": {"test_npc": {0: dialog_config}}}

        with patch.object(plugin, "_check_dialog_conditions", return_value=False):
            result = plugin.interact_with_npc("test_npc")

            assert result is False

    def test_get_dialog_fallback_skip_exact_level_in_loop(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test get_dialog skips the exact level when building candidates."""
        plugin, _ = npc_plugin_ctx
        dialog_level_3 = NPCDialogConfig(text=["Level 3"])
        dialog_level_5 = NPCDialogConfig(text=["Level 5"])
        dialog_level_7 = NPCDialogConfig(text=["Level 7"])
        plugin.dialogs = {"scene1": {"npc1": {3: dialog_level_3, 5: dialog_level_5, 7: dialog_level_7}}}

        result, _ = plugin.get_dialog("npc1", 6, "scene1")

        assert result == dialog_level_5

    def test_update_animated_npc_no_movement_keeps_direction(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test update when NPC is at exact waypoint position (dx=0, dy=0)."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock(spec=AnimatedSprite)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        npc_sprite.current_direction = "down"
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = False
        plugin.register_npc(npc_sprite, "stationary")

        plugin.npcs["stationary"].path = deque([(100.0, 100.0)])
        plugin.npcs["stationary"].is_moving = True

        plugin.update(0.1)

        assert len(plugin.npcs["stationary"].path) == 0

    def test_interact_with_npc_no_dialog_plugin(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test interact_with_npc when dialog_plugin is None (line 417)."""
        plugin, context = npc_plugin_ctx
        context.dialog_plugin = None
        context.scene_plugin.get_current_scene.return_value = "village"

        mock_sprite = MagicMock()
        plugin.register_npc(mock_sprite, "npc")
        dialog_config = NPCDialogConfig(text=["Hello"])
        plugin.dialogs = {"village": {"npc": {0: dialog_config}}}

        result = plugin.interact_with_npc("npc")

        assert result is False

    def test_get_dialog_exact_level_match_with_failed_conditions(
        self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]
    ) -> None:
        """Test get_dialog when exact level exists but conditions fail (line 413 in interact)."""
        plugin, context = npc_plugin_ctx
        context.scene_plugin.get_current_scene.return_value = "castle"

        mock_sprite = MagicMock()
        plugin.register_npc(mock_sprite, "guard")

        dialog_config = NPCDialogConfig(text=["You shall pass"], conditions=[MagicMock()])
        plugin.dialogs = {"castle": {"guard": {0: dialog_config}}}

        with patch.object(plugin, "_check_dialog_conditions", return_value=False):
            result = plugin.interact_with_npc("guard")

            assert result is False

    def test_get_dialog_candidates_loop_with_exact_level_skipped(
        self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]
    ) -> None:
        """Test get_dialog fallback loop actually skips exact level (line 535)."""
        plugin, _ = npc_plugin_ctx
        dialog_level_2 = NPCDialogConfig(text=["Level 2"])
        dialog_level_4 = NPCDialogConfig(text=["Level 4"])
        dialog_level_6 = NPCDialogConfig(text=["Level 6"])
        plugin.dialogs = {"scene": {"npc": {2: dialog_level_2, 4: dialog_level_4, 6: dialog_level_6}}}

        result, _ = plugin.get_dialog("npc", 5, "scene")

        assert result == dialog_level_4

    def test_mark_npc_as_interacted_creates_new_scene_set(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test mark_npc_as_interacted creates new set for new scene (line 447-448)."""
        plugin, context = npc_plugin_ctx
        context.scene_plugin.get_current_scene.return_value = "new_scene"

        assert "new_scene" not in plugin.interacted_npcs

        plugin.mark_npc_as_interacted("npc1")

        assert "new_scene" in plugin.interacted_npcs
        assert "npc1" in plugin.interacted_npcs["new_scene"]

    def test_move_npc_to_position_with_empty_path(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test move_npc_to_position when pathfinding returns empty path (line 621)."""
        plugin, context = npc_plugin_ctx
        npc_sprite = MagicMock()
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        plugin.register_npc(npc_sprite, "blocked_npc")

        context.pathfinding_plugin.find_path.return_value = []

        plugin.move_npc_to_position("blocked_npc", 200.0, 200.0)

        assert plugin.npcs["blocked_npc"].is_moving is False
        assert len(plugin.npcs["blocked_npc"].path) == 0

    def test_show_npcs_without_scene_plugin(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test show_npcs when scene_plugin is None (line 641-643)."""
        plugin, context = npc_plugin_ctx
        context.scene_plugin = None
        npc_sprite = MagicMock(spec=AnimatedSprite)
        npc_sprite.visible = False
        plugin.register_npc(npc_sprite, "npc1")

        plugin.show_npcs(["npc1"])

        assert npc_sprite.visible is True

    def test_update_movement_complete_without_event_bus(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test update when movement completes but no event bus (line 696)."""
        plugin, context = npc_plugin_ctx
        context.event_bus = None
        npc_sprite = MagicMock()
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        plugin.register_npc(npc_sprite, "walker")

        plugin.npcs["walker"].path = deque([(100.5, 100.0)])
        plugin.npcs["walker"].is_moving = True

        plugin.update(1.0)

        assert plugin.npcs["walker"].is_moving is False

    def test_update_appear_complete_without_event_bus(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test update when appear completes but no event bus (line 717)."""
        plugin, context = npc_plugin_ctx
        context.event_bus = None
        npc_sprite = MagicMock(spec=AnimatedSprite)
        npc_sprite.appear_complete = True
        npc_sprite.disappear_complete = False
        plugin.register_npc(npc_sprite, "appearing")
        plugin.npcs["appearing"].appear_event_emitted = False

        plugin.update(0.1)

        assert plugin.npcs["appearing"].appear_event_emitted is True

    def test_update_disappear_complete_without_event_bus(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test update when disappear completes but no event bus (line 724)."""
        plugin, context = npc_plugin_ctx
        context.event_bus = None
        npc_sprite = MagicMock(spec=AnimatedSprite)
        npc_sprite.appear_complete = False
        npc_sprite.disappear_complete = True
        plugin.register_npc(npc_sprite, "disappearing")
        plugin.npcs["disappearing"].disappear_event_emitted = False

        plugin.update(0.1)

        assert plugin.npcs["disappearing"].disappear_event_emitted is True

    def test_load_npcs_from_objects_without_scene_plugin(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test load_npcs_from_objects when scene_plugin is None."""
        plugin, context = npc_plugin_ctx
        context.scene_plugin = None
        mock_scene = MagicMock(spec=arcade.Scene)
        mock_obj = MagicMock()
        mock_obj.properties = {"name": "Guard", "sprite_sheet": "sprites/guard.png"}
        mock_obj.shape = [100.0, 200.0]

        mock_npc_instance = MagicMock()
        mock_npc_instance.visible = True
        with patch.object(plugin, "_create_npc_sprite", return_value=mock_npc_instance):
            plugin.load_npcs_from_objects([mock_obj], mock_scene)

            assert "guard" in plugin.npcs

    def test_get_save_state_with_regular_sprite(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test get_save_state with non-AnimatedNPC sprite (line 954)."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock(spec=arcade.Sprite)
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 200.0
        npc_sprite.visible = True
        plugin.register_npc(npc_sprite, "regular_npc")

        save_state = plugin.get_save_state()

        npc_state = save_state["npcs"]["regular_npc"]
        assert "appear_complete" not in npc_state
        assert "disappear_complete" not in npc_state
        assert "interact_complete" not in npc_state

    def test_cache_scene_state_with_regular_sprite(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test cache_scene_state with non-AnimatedNPC sprite (line 1023)."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock(spec=arcade.Sprite)
        npc_sprite.center_x = 150.0
        npc_sprite.center_y = 250.0
        npc_sprite.visible = False
        plugin.register_npc(npc_sprite, "regular_npc")

        state = plugin.cache_scene_state("test_scene")

        npc_state = state["regular_npc"]
        assert "appear_complete" not in npc_state
        assert "disappear_complete" not in npc_state

    def test_apply_npc_state_with_regular_sprite(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test _apply_npc_state with non-AnimatedNPC sprite (line 1000)."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock(spec=arcade.Sprite)
        plugin.register_npc(npc_sprite, "regular_npc")

        state = {"regular_npc": {"x": 300.0, "y": 400.0, "visible": True, "dialog_level": 2}}

        plugin._apply_npc_state(state)

        assert npc_sprite.center_x == 300.0
        assert npc_sprite.center_y == 400.0

    def test_on_key_press_nearby_npc_interact_fails(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test on_key_press when nearby NPC exists but interact_with_npc returns False."""
        plugin, context = npc_plugin_ctx
        player_sprite = MagicMock()
        player_sprite.center_x = 100
        player_sprite.center_y = 100
        context.player_plugin.get_player_sprite.return_value = player_sprite

        npc_sprite = MagicMock()
        npc_sprite.center_x = 110
        npc_sprite.center_y = 100
        npc_sprite.visible = True
        plugin.register_npc(npc_sprite, "nearby_npc")

        with (
            patch("pedre.plugins.npc.plugin.matches_key", return_value=True),
            patch("pedre.plugins.npc.plugin.arcade.get_distance_between_sprites", return_value=10.0),
            patch.object(plugin, "interact_with_npc", return_value=False),
        ):
            result = plugin.on_key_press(123, 0)

            assert result is False

    def test_mark_npc_as_interacted_scene_already_exists(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test mark_npc_as_interacted when scene already has an interacted set."""
        plugin, _ = npc_plugin_ctx
        plugin.interacted_npcs["village"] = {"alice"}

        plugin.mark_npc_as_interacted("bob", "village")

        assert plugin.interacted_npcs["village"] == {"alice", "bob"}

    def test_update_npc_movement_distance_exactly_zero(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test update when NPC is moving but distance to waypoint is exactly 0 and above threshold."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock()
        npc_sprite.center_x = 100.0
        npc_sprite.center_y = 100.0
        plugin.register_npc(npc_sprite, "stuck")

        plugin.npcs["stuck"].path = deque([(200.0, 100.0)])
        plugin.npcs["stuck"].is_moving = True

        plugin.update(0.016)

        assert npc_sprite.center_x > 100.0
        assert plugin.npcs["stuck"].is_moving is True

    def test_apply_entity_state_without_interacted_npcs(self, npc_plugin_ctx: tuple[NPCPlugin, MagicMock]) -> None:
        """Test apply_entity_state when state has no interacted_npcs key."""
        plugin, _ = npc_plugin_ctx
        npc_sprite = MagicMock(spec=AnimatedSprite)
        plugin.register_npc(npc_sprite, "npc1")
        plugin.interacted_npcs = {"old_scene": {"old_npc"}}

        save_data = {
            "npcs": {"npc1": {"x": 10.0, "y": 20.0, "visible": True, "dialog_level": 0}},
        }

        plugin.apply_entity_state(save_data)

        assert plugin.interacted_npcs == {"old_scene": {"old_npc"}}


class TestCheckDialogConditions:
    """Test NPCPlugin._check_dialog_conditions."""

    def test_condition_check_returns_false(self) -> None:
        """Test returns False when a condition check fails."""
        plugin = NPCPlugin()
        context = MagicMock()
        plugin.setup(context)

        mock_condition = MagicMock()
        mock_condition.check.return_value = False

        result = plugin._check_dialog_conditions([mock_condition])

        assert result is False
        mock_condition.check.assert_called_once_with(context)

    def test_all_conditions_pass(self) -> None:
        """Test returns True when all conditions pass their checks."""
        plugin = NPCPlugin()
        context = MagicMock()
        plugin.setup(context)

        mock_cond_a = MagicMock()
        mock_cond_a.check.return_value = True
        mock_cond_b = MagicMock()
        mock_cond_b.check.return_value = True

        result = plugin._check_dialog_conditions([mock_cond_a, mock_cond_b])

        assert result is True
        mock_cond_a.check.assert_called_once_with(context)
        mock_cond_b.check.assert_called_once_with(context)
