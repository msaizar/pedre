"""Unit tests for particle action classes."""

import unittest
from unittest.mock import MagicMock

from pedre.plugins.particle.actions import EmitParticlesAction


class TestEmitParticlesAction(unittest.TestCase):
    """Unit test class for EmitParticlesAction."""

    def test_init(self) -> None:
        """Test EmitParticlesAction initialization."""
        action = EmitParticlesAction("hearts", npc_name="yema")

        assert action.particle_type == "hearts"
        assert action.npc_name == "yema"
        assert action.player is False
        assert action.interactive_object is None
        assert action.color is None
        assert action.executed is False

    def test_init_with_player(self) -> None:
        """Test initialization with player location."""
        action = EmitParticlesAction("sparkles", player=True)

        assert action.particle_type == "sparkles"
        assert action.player is True
        assert action.npc_name is None
        assert action.interactive_object is None

    def test_init_with_interactive_object(self) -> None:
        """Test initialization with interactive object location."""
        action = EmitParticlesAction("burst", interactive_object="chest")

        assert action.particle_type == "burst"
        assert action.interactive_object == "chest"
        assert action.npc_name is None
        assert action.player is False

    def test_init_with_color(self) -> None:
        """Test initialization with custom color."""
        action = EmitParticlesAction("hearts", npc_name="yema", color=(255, 0, 0))

        assert action.color == (255, 0, 0)

    def test_execute_hearts_at_npc(self) -> None:
        """Test emitting hearts at NPC location."""
        action = EmitParticlesAction("hearts", npc_name="yema")

        # Create mock context
        mock_context = MagicMock()
        mock_npc_plugin = MagicMock()
        mock_particle_plugin = MagicMock()
        mock_npc_sprite = MagicMock()
        mock_npc_sprite.center_x = 100.0
        mock_npc_sprite.center_y = 200.0
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_npc_sprite

        mock_context.npc_plugin = mock_npc_plugin
        mock_context.particle_plugin = mock_particle_plugin
        mock_npc_plugin.get_npcs.return_value = {"yema": mock_npc_state}

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_particle_plugin.emit_hearts.assert_called_once_with(100.0, 200.0)
        assert action.executed is True

    def test_execute_hearts_at_npc_with_color(self) -> None:
        """Test emitting hearts at NPC location with custom color."""
        action = EmitParticlesAction("hearts", npc_name="yema", color=(255, 0, 0))

        # Create mock context
        mock_context = MagicMock()
        mock_npc_plugin = MagicMock()
        mock_particle_plugin = MagicMock()
        mock_npc_sprite = MagicMock()
        mock_npc_sprite.center_x = 100.0
        mock_npc_sprite.center_y = 200.0
        mock_npc_state = MagicMock()
        mock_npc_state.sprite = mock_npc_sprite

        mock_context.npc_plugin = mock_npc_plugin
        mock_context.particle_plugin = mock_particle_plugin
        mock_npc_plugin.get_npcs.return_value = {"yema": mock_npc_state}

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_particle_plugin.emit_hearts.assert_called_once_with(100.0, 200.0, color=(255, 0, 0))
        assert action.executed is True

    def test_execute_sparkles_at_player(self) -> None:
        """Test emitting sparkles at player location."""
        action = EmitParticlesAction("sparkles", player=True)

        # Create mock context
        mock_context = MagicMock()
        mock_player_plugin = MagicMock()
        mock_particle_plugin = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 150.0
        mock_player_sprite.center_y = 250.0

        mock_context.player_plugin = mock_player_plugin
        mock_context.particle_plugin = mock_particle_plugin
        mock_player_plugin.get_player_sprite.return_value = mock_player_sprite

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_particle_plugin.emit_sparkles.assert_called_once_with(150.0, 250.0)
        assert action.executed is True

    def test_execute_sparkles_at_player_with_color(self) -> None:
        """Test emitting sparkles at player location with custom color."""
        action = EmitParticlesAction("sparkles", player=True, color=(0, 255, 0))

        # Create mock context
        mock_context = MagicMock()
        mock_player_plugin = MagicMock()
        mock_particle_plugin = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 150.0
        mock_player_sprite.center_y = 250.0

        mock_context.player_plugin = mock_player_plugin
        mock_context.particle_plugin = mock_particle_plugin
        mock_player_plugin.get_player_sprite.return_value = mock_player_sprite

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_particle_plugin.emit_sparkles.assert_called_once_with(150.0, 250.0, color=(0, 255, 0))

    def test_execute_trail_at_interactive_object(self) -> None:
        """Test emitting trail at interactive object location."""
        action = EmitParticlesAction("trail", interactive_object="waypoint")

        # Create mock context
        mock_context = MagicMock()
        mock_interaction_plugin = MagicMock()
        mock_particle_plugin = MagicMock()
        mock_obj_sprite = MagicMock()
        mock_obj_sprite.center_x = 300.0
        mock_obj_sprite.center_y = 400.0
        mock_interactive_obj = MagicMock()
        mock_interactive_obj.sprite = mock_obj_sprite

        mock_context.interaction_plugin = mock_interaction_plugin
        mock_context.particle_plugin = mock_particle_plugin
        mock_interaction_plugin.get_interactive_objects.return_value = {"waypoint": mock_interactive_obj}

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_particle_plugin.emit_trail.assert_called_once_with(300.0, 400.0)
        assert action.executed is True

    def test_execute_trail_at_interactive_object_with_color(self) -> None:
        """Test emitting trail at interactive object with custom color."""
        action = EmitParticlesAction("trail", interactive_object="waypoint", color=(0, 0, 255))

        # Create mock context
        mock_context = MagicMock()
        mock_interaction_plugin = MagicMock()
        mock_particle_plugin = MagicMock()
        mock_obj_sprite = MagicMock()
        mock_obj_sprite.center_x = 300.0
        mock_obj_sprite.center_y = 400.0
        mock_interactive_obj = MagicMock()
        mock_interactive_obj.sprite = mock_obj_sprite

        mock_context.interaction_plugin = mock_interaction_plugin
        mock_context.particle_plugin = mock_particle_plugin
        mock_interaction_plugin.get_interactive_objects.return_value = {"waypoint": mock_interactive_obj}

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_particle_plugin.emit_trail.assert_called_once_with(300.0, 400.0, color=(0, 0, 255))

    def test_execute_burst_at_interactive_object(self) -> None:
        """Test emitting burst at interactive object location."""
        action = EmitParticlesAction("burst", interactive_object="chest")

        # Create mock context
        mock_context = MagicMock()
        mock_interaction_plugin = MagicMock()
        mock_particle_plugin = MagicMock()
        mock_obj_sprite = MagicMock()
        mock_obj_sprite.center_x = 500.0
        mock_obj_sprite.center_y = 600.0
        mock_interactive_obj = MagicMock()
        mock_interactive_obj.sprite = mock_obj_sprite

        mock_context.interaction_plugin = mock_interaction_plugin
        mock_context.particle_plugin = mock_particle_plugin
        mock_interaction_plugin.get_interactive_objects.return_value = {"chest": mock_interactive_obj}

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_particle_plugin.emit_burst.assert_called_once_with(500.0, 600.0)
        assert action.executed is True

    def test_execute_burst_with_color(self) -> None:
        """Test emitting burst with custom color."""
        action = EmitParticlesAction("burst", player=True, color=(255, 215, 0))

        # Create mock context
        mock_context = MagicMock()
        mock_player_plugin = MagicMock()
        mock_particle_plugin = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 150.0
        mock_player_sprite.center_y = 250.0

        mock_context.player_plugin = mock_player_plugin
        mock_context.particle_plugin = mock_particle_plugin
        mock_player_plugin.get_player_sprite.return_value = mock_player_sprite

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_particle_plugin.emit_burst.assert_called_once_with(150.0, 250.0, color=(255, 215, 0))

    def test_execute_only_once(self) -> None:
        """Test that execute only emits particles once."""
        action = EmitParticlesAction("hearts", player=True)

        # Create mock context
        mock_context = MagicMock()
        mock_player_plugin = MagicMock()
        mock_particle_plugin = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 150.0
        mock_player_sprite.center_y = 250.0

        mock_context.player_plugin = mock_player_plugin
        mock_context.particle_plugin = mock_particle_plugin
        mock_player_plugin.get_player_sprite.return_value = mock_player_sprite

        # Execute multiple times
        action.execute(mock_context)
        action.execute(mock_context)
        action.execute(mock_context)

        # Should only emit once
        mock_particle_plugin.emit_hearts.assert_called_once()

    def test_execute_no_location_specified(self) -> None:
        """Test execution with no location specified."""
        action = EmitParticlesAction("hearts")

        # Create mock context
        mock_context = MagicMock()

        # Execute action
        result = action.execute(mock_context)

        # Should return True but not execute
        assert result is True
        assert action.executed is False

    def test_execute_multiple_locations_specified(self) -> None:
        """Test execution with multiple locations specified."""
        action = EmitParticlesAction("hearts", npc_name="yema", player=True)

        # Create mock context
        mock_context = MagicMock()

        # Execute action
        result = action.execute(mock_context)

        # Should return True but not execute
        assert result is True
        assert action.executed is False

    def test_execute_npc_not_found(self) -> None:
        """Test execution when NPC is not found."""
        action = EmitParticlesAction("hearts", npc_name="nonexistent")

        # Create mock context
        mock_context = MagicMock()
        mock_npc_plugin = MagicMock()
        mock_context.npc_plugin = mock_npc_plugin
        mock_npc_plugin.get_npcs.return_value = {}

        # Execute action
        result = action.execute(mock_context)

        # Should return True but not execute
        assert result is True
        assert action.executed is False

    def test_execute_player_sprite_not_available(self) -> None:
        """Test execution when player sprite is not available."""
        action = EmitParticlesAction("sparkles", player=True)

        # Create mock context
        mock_context = MagicMock()
        mock_player_plugin = MagicMock()
        mock_context.player_plugin = mock_player_plugin
        mock_player_plugin.get_player_sprite.return_value = None

        # Execute action
        result = action.execute(mock_context)

        # Should return True but not execute
        assert result is True
        assert action.executed is False

    def test_execute_interactive_object_not_found(self) -> None:
        """Test execution when interactive object is not found."""
        action = EmitParticlesAction("trail", interactive_object="nonexistent")

        # Create mock context
        mock_context = MagicMock()
        mock_interaction_plugin = MagicMock()
        mock_context.interaction_plugin = mock_interaction_plugin
        mock_interaction_plugin.get_interactive_objects.return_value = {}

        # Execute action
        result = action.execute(mock_context)

        # Should return True but not execute
        assert result is True
        assert action.executed is False

    def test_reset(self) -> None:
        """Test that reset allows re-execution."""
        action = EmitParticlesAction("hearts", player=True)

        # Create mock context
        mock_context = MagicMock()
        mock_player_plugin = MagicMock()
        mock_particle_plugin = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 150.0
        mock_player_sprite.center_y = 250.0

        mock_context.player_plugin = mock_player_plugin
        mock_context.particle_plugin = mock_particle_plugin
        mock_player_plugin.get_player_sprite.return_value = mock_player_sprite

        # Execute, reset, execute again
        action.execute(mock_context)
        assert action.executed is True

        action.reset()
        assert action.executed is False

        action.execute(mock_context)

        # Should have been called twice (once before reset, once after)
        assert mock_particle_plugin.emit_hearts.call_count == 2

    def test_from_dict_with_npc(self) -> None:
        """Test creating EmitParticlesAction from dictionary with NPC."""
        data = {"particle_type": "hearts", "npc": "yema"}

        action = EmitParticlesAction.from_dict(data)

        assert isinstance(action, EmitParticlesAction)
        assert action.particle_type == "hearts"
        assert action.npc_name == "yema"
        assert action.player is False
        assert action.interactive_object is None
        assert action.color is None

    def test_from_dict_with_player(self) -> None:
        """Test creating EmitParticlesAction from dictionary with player."""
        data = {"particle_type": "sparkles", "player": True}

        action = EmitParticlesAction.from_dict(data)

        assert isinstance(action, EmitParticlesAction)
        assert action.particle_type == "sparkles"
        assert action.player is True
        assert action.npc_name is None
        assert action.interactive_object is None

    def test_from_dict_with_interactive_object(self) -> None:
        """Test creating EmitParticlesAction from dictionary with interactive object."""
        data = {"particle_type": "trail", "interactive_object": "waypoint"}

        action = EmitParticlesAction.from_dict(data)

        assert isinstance(action, EmitParticlesAction)
        assert action.particle_type == "trail"
        assert action.interactive_object == "waypoint"
        assert action.npc_name is None
        assert action.player is False

    def test_from_dict_with_color(self) -> None:
        """Test creating EmitParticlesAction from dictionary with custom color."""
        data = {"particle_type": "burst", "player": True, "color": [255, 215, 0]}

        action = EmitParticlesAction.from_dict(data)

        assert isinstance(action, EmitParticlesAction)
        assert action.particle_type == "burst"
        assert action.color == (255, 215, 0)

    def test_from_dict_default_particle_type(self) -> None:
        """Test creating EmitParticlesAction with default particle type."""
        data = {"player": True}

        action = EmitParticlesAction.from_dict(data)

        assert isinstance(action, EmitParticlesAction)
        assert action.particle_type == "burst"

    def test_from_dict_default_player(self) -> None:
        """Test creating EmitParticlesAction with default player value."""
        data = {"particle_type": "hearts", "npc": "yema"}

        action = EmitParticlesAction.from_dict(data)

        assert isinstance(action, EmitParticlesAction)
        assert action.player is False

    def test_execute_unknown_particle_type(self) -> None:
        """Test execution with unknown particle type (no matching condition)."""
        action = EmitParticlesAction("unknown_type", player=True)

        # Create mock context
        mock_context = MagicMock()
        mock_player_plugin = MagicMock()
        mock_particle_plugin = MagicMock()
        mock_player_sprite = MagicMock()
        mock_player_sprite.center_x = 150.0
        mock_player_sprite.center_y = 250.0

        mock_context.player_plugin = mock_player_plugin
        mock_context.particle_plugin = mock_particle_plugin
        mock_player_plugin.get_player_sprite.return_value = mock_player_sprite

        # Execute action
        result = action.execute(mock_context)

        # Should return True and mark as executed even though no particle type matched
        assert result is True
        assert action.executed is True

        # No particle emission methods should be called
        mock_particle_plugin.emit_hearts.assert_not_called()
        mock_particle_plugin.emit_sparkles.assert_not_called()
        mock_particle_plugin.emit_trail.assert_not_called()
        mock_particle_plugin.emit_burst.assert_not_called()

    def test_execute_burst_at_interactive_object_with_color(self) -> None:
        """Test emitting burst at interactive object with custom color."""
        action = EmitParticlesAction("burst", interactive_object="chest", color=(255, 215, 0))

        # Create mock context
        mock_context = MagicMock()
        mock_interaction_plugin = MagicMock()
        mock_particle_plugin = MagicMock()
        mock_obj_sprite = MagicMock()
        mock_obj_sprite.center_x = 500.0
        mock_obj_sprite.center_y = 600.0
        mock_interactive_obj = MagicMock()
        mock_interactive_obj.sprite = mock_obj_sprite

        mock_context.interaction_plugin = mock_interaction_plugin
        mock_context.particle_plugin = mock_particle_plugin
        mock_interaction_plugin.get_interactive_objects.return_value = {"chest": mock_interactive_obj}

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_particle_plugin.emit_burst.assert_called_once_with(500.0, 600.0, color=(255, 215, 0))
        assert action.executed is True

    def test_execute_unknown_particle_type_at_interactive_object(self) -> None:
        """Test execution with unknown particle type at interactive object."""
        action = EmitParticlesAction("unknown", interactive_object="waypoint")

        # Create mock context
        mock_context = MagicMock()
        mock_interaction_plugin = MagicMock()
        mock_particle_plugin = MagicMock()
        mock_obj_sprite = MagicMock()
        mock_obj_sprite.center_x = 300.0
        mock_obj_sprite.center_y = 400.0
        mock_interactive_obj = MagicMock()
        mock_interactive_obj.sprite = mock_obj_sprite

        mock_context.interaction_plugin = mock_interaction_plugin
        mock_context.particle_plugin = mock_particle_plugin
        mock_interaction_plugin.get_interactive_objects.return_value = {"waypoint": mock_interactive_obj}

        # Execute action
        result = action.execute(mock_context)

        # Should return True and mark as executed even though no particle type matched
        assert result is True
        assert action.executed is True

        # No particle emission methods should be called
        mock_particle_plugin.emit_hearts.assert_not_called()
        mock_particle_plugin.emit_sparkles.assert_not_called()
        mock_particle_plugin.emit_trail.assert_not_called()
        mock_particle_plugin.emit_burst.assert_not_called()

    def test_execute_hearts_at_interactive_object(self) -> None:
        """Test emitting hearts at interactive object location."""
        action = EmitParticlesAction("hearts", interactive_object="shrine")

        # Create mock context
        mock_context = MagicMock()
        mock_interaction_plugin = MagicMock()
        mock_particle_plugin = MagicMock()
        mock_obj_sprite = MagicMock()
        mock_obj_sprite.center_x = 250.0
        mock_obj_sprite.center_y = 350.0
        mock_interactive_obj = MagicMock()
        mock_interactive_obj.sprite = mock_obj_sprite

        mock_context.interaction_plugin = mock_interaction_plugin
        mock_context.particle_plugin = mock_particle_plugin
        mock_interaction_plugin.get_interactive_objects.return_value = {"shrine": mock_interactive_obj}

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_particle_plugin.emit_hearts.assert_called_once_with(250.0, 350.0)
        assert action.executed is True

    def test_execute_sparkles_at_interactive_object(self) -> None:
        """Test emitting sparkles at interactive object location."""
        action = EmitParticlesAction("sparkles", interactive_object="portal")

        # Create mock context
        mock_context = MagicMock()
        mock_interaction_plugin = MagicMock()
        mock_particle_plugin = MagicMock()
        mock_obj_sprite = MagicMock()
        mock_obj_sprite.center_x = 450.0
        mock_obj_sprite.center_y = 550.0
        mock_interactive_obj = MagicMock()
        mock_interactive_obj.sprite = mock_obj_sprite

        mock_context.interaction_plugin = mock_interaction_plugin
        mock_context.particle_plugin = mock_particle_plugin
        mock_interaction_plugin.get_interactive_objects.return_value = {"portal": mock_interactive_obj}

        # Execute action
        result = action.execute(mock_context)

        assert result is True
        mock_particle_plugin.emit_sparkles.assert_called_once_with(450.0, 550.0)
        assert action.executed is True


class TestEmitParticlesActionValidation(unittest.TestCase):
    """Test EmitParticlesAction parameter validation."""

    def test_validate_params_success_with_npc(self) -> None:
        """Test validate_params with valid npc location."""
        data = {"particle_type": "hearts", "npc": "martin"}
        errors = EmitParticlesAction.validate_params(data)
        assert errors == []

    def test_validate_params_success_with_player(self) -> None:
        """Test validate_params with valid player location."""
        data = {"particle_type": "sparkles", "player": True}
        errors = EmitParticlesAction.validate_params(data)
        assert errors == []

    def test_validate_params_success_with_interactive_object(self) -> None:
        """Test validate_params with valid interactive_object location."""
        data = {"particle_type": "burst", "interactive_object": "portal"}
        errors = EmitParticlesAction.validate_params(data)
        assert errors == []

    def test_validate_params_success_default_particle_type(self) -> None:
        """Test validate_params with default particle_type (burst)."""
        data = {"npc": "martin"}
        errors = EmitParticlesAction.validate_params(data)
        assert errors == []

    def test_validate_params_invalid_particle_type(self) -> None:
        """Test validate_params detects invalid particle_type."""
        data = {"particle_type": "invalid_type", "npc": "martin"}
        errors = EmitParticlesAction.validate_params(data)
        assert len(errors) == 1
        assert "unknown particle_type 'invalid_type'" in errors[0]
        assert "valid: " in errors[0]

    def test_validate_params_no_location(self) -> None:
        """Test validate_params detects missing location."""
        data = {"particle_type": "hearts"}
        errors = EmitParticlesAction.validate_params(data)
        assert len(errors) == 1
        assert "must specify one location" in errors[0]

    def test_validate_params_multiple_locations_npc_and_player(self) -> None:
        """Test validate_params detects multiple locations (npc and player)."""
        data = {"particle_type": "hearts", "npc": "martin", "player": True}
        errors = EmitParticlesAction.validate_params(data)
        assert len(errors) == 1
        assert "only one location allowed" in errors[0]

    def test_validate_params_multiple_locations_all_three(self) -> None:
        """Test validate_params detects all three locations specified."""
        data = {"particle_type": "hearts", "npc": "martin", "player": True, "interactive_object": "portal"}
        errors = EmitParticlesAction.validate_params(data)
        assert len(errors) == 1
        assert "only one location allowed" in errors[0]

    def test_validate_params_multiple_errors(self) -> None:
        """Test validate_params detects multiple errors at once."""
        data = {"particle_type": "invalid_type"}
        errors = EmitParticlesAction.validate_params(data)
        assert len(errors) == 2
        assert any("unknown particle_type" in e for e in errors)
        assert any("must specify one location" in e for e in errors)

    def test_validate_params_particle_type_not_string(self) -> None:
        """Test validate_params detects non-string particle_type."""
        data = {"particle_type": 123, "npc": "martin"}
        errors = EmitParticlesAction.validate_params(data)
        assert len(errors) == 1
        assert "'particle_type' must be a string" in errors[0]

    def test_validate_params_npc_not_string(self) -> None:
        """Test validate_params detects non-string npc field."""
        data = {"npc": 123}
        errors = EmitParticlesAction.validate_params(data)
        assert len(errors) == 1
        assert "'npc' must be a string" in errors[0]

    def test_validate_params_player_not_bool(self) -> None:
        """Test validate_params detects non-bool player field."""
        data = {"player": "yes"}
        errors = EmitParticlesAction.validate_params(data)
        assert len(errors) == 1
        assert "'player' must be a bool" in errors[0]

    def test_validate_params_interactive_object_not_string(self) -> None:
        """Test validate_params detects non-string interactive_object field."""
        data = {"interactive_object": 123}
        errors = EmitParticlesAction.validate_params(data)
        assert len(errors) == 1
        assert "'interactive_object' must be a string" in errors[0]

    def test_validate_params_color_not_list(self) -> None:
        """Test validate_params detects non-list color field."""
        data = {"npc": "martin", "color": "red"}
        errors = EmitParticlesAction.validate_params(data)
        assert len(errors) == 1
        assert "'color' must be a list of 3 integers" in errors[0]

    def test_validate_params_color_wrong_length(self) -> None:
        """Test validate_params detects color list with wrong length."""
        data = {"npc": "martin", "color": [255, 0]}
        errors = EmitParticlesAction.validate_params(data)
        assert len(errors) == 1
        assert "'color' must be a list of 3 integers" in errors[0]

    def test_validate_params_color_non_integers(self) -> None:
        """Test validate_params detects color list with non-integers."""
        data = {"npc": "martin", "color": [255, "green", 0]}
        errors = EmitParticlesAction.validate_params(data)
        assert len(errors) == 1
        assert "'color' must be a list of 3 integers" in errors[0]

    def test_validate_params_color_with_bools(self) -> None:
        """Test validate_params detects color list with bools."""
        data = {"npc": "martin", "color": [True, False, 0]}
        errors = EmitParticlesAction.validate_params(data)
        assert len(errors) == 1
        assert "'color' must be a list of 3 integers" in errors[0]

    def test_validate_params_color_valid(self) -> None:
        """Test validate_params accepts valid color list."""
        data = {"npc": "martin", "color": [255, 128, 0]}
        errors = EmitParticlesAction.validate_params(data)
        assert errors == []


if __name__ == "__main__":
    unittest.main()
