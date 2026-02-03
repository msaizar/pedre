"""Unit tests for NPCPlugin in src/pedre/plugins/npc/plugin.py."""

import unittest
from unittest.mock import MagicMock, patch

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
            def get_dist(s1, s2):
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
            sprite, name, level = result
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

        self.plugin.move_npc_to_tile("walker", 5, 5)

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
        assert npc.sprite.appear_complete is True
        assert npc.sprite.disappear_complete is True

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


if __name__ == "__main__":
    unittest.main()
