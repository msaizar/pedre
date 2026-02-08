"""Unit tests for InteractionPlugin."""

import unittest
from unittest.mock import MagicMock, patch

import arcade

# Mocking parts of pedre that might not be easily importable without full setup
# We assume pedre package is available in python path
from pedre.plugins.interaction import InteractionPlugin
from pedre.plugins.interaction.base import InteractiveObject
from pedre.plugins.interaction.events import ObjectInteractedEvent


class TestInteractionPlugin(unittest.TestCase):
    """Unit test class for InteractionPlugin."""

    def setUp(self) -> None:
        """Set up InteractionPlugin and mock context."""
        with patch("pedre.plugins.interaction.plugin.settings") as mock_settings:
            mock_settings.INTERACTION_PLUGIN_DISTANCE = 64.0
            self.plugin = InteractionPlugin()

        # Mock context
        self.mock_context = MagicMock()
        self.mock_context.event_bus = MagicMock()
        self.mock_context.player_plugin = MagicMock()
        self.plugin.context = self.mock_context

    def test_register_object(self) -> None:
        """Test registering objects."""
        sprite = arcade.Sprite()
        name = "test_obj"
        properties = {"interaction_type": "message", "message": "Hello"}

        self.plugin.register_object(sprite, name, properties)

        assert name in self.plugin.interactive_objects
        obj = self.plugin.interactive_objects[name]
        assert obj.name == name
        assert obj.sprite == sprite
        assert obj.properties == properties

    def test_get_nearby_object(self) -> None:
        """Test nearby object."""
        # Create a player sprite at 0,0
        player = arcade.Sprite()
        player.center_x = 0
        player.center_y = 0

        # Create a close object (within 50)
        close_sprite = arcade.Sprite()
        close_sprite.center_x = 30
        close_sprite.center_y = 0
        self.plugin.register_object(close_sprite, "close", {})

        # Create a far object (outside 50)
        far_sprite = arcade.Sprite()
        far_sprite.center_x = 200
        far_sprite.center_y = 0
        self.plugin.register_object(far_sprite, "far", {})

        # Check nearby object
        nearby = self.plugin.get_nearby_object(player)
        assert nearby is not None
        assert nearby.name == "close"

    def test_get_nearby_object_none(self) -> None:
        """Test far away object."""
        player = arcade.Sprite()
        player.center_x = 0
        player.center_y = 0

        # Only far object
        far_sprite = arcade.Sprite()
        far_sprite.center_x = 200
        far_sprite.center_y = 0
        self.plugin.register_object(far_sprite, "far", {})

        nearby = self.plugin.get_nearby_object(player)
        assert nearby is None

    def test_load_from_tiled(self) -> None:
        """Test loading data from Tiled."""
        # Mock Tiled map and objects
        mock_tile_map = MagicMock()
        mock_layer = MagicMock()

        # Create a mock Tiled object (TiledObject)
        mock_obj = MagicMock()
        mock_obj.name = "TestObj"
        # properties attribute on TiledObject
        mock_obj.properties = {"interaction_type": "toggle"}
        # shape attribute: list of points (polygon/polyline) or similar
        # For a rectangle object, accessors might vary, but our code expects .shape
        # Code logic: if isinstance(obj.shape, (list, tuple)) ...
        # Let's mock a rectangle shape logic: [(0,0), (0,10), (10,10), (10,0)]
        # width 10, height 10
        mock_obj.shape = [(0, 0), (10, 0), (10, 10), (0, 10)]

        mock_layer.__iter__.return_value = [mock_obj]
        mock_tile_map.object_lists = {"Interactive": mock_layer}

        mock_scene = MagicMock()  # arcade.Scene

        self.plugin.load_from_tiled(mock_tile_map, mock_scene)

        assert "testobj" in self.plugin.interactive_objects
        obj = self.plugin.interactive_objects["testobj"]

        # Check if sprite was created with correct dimensions
        # min x=0, max x=10 -> width 10, center_x 5
        # min y=0, max y=10 -> height 10, center_y 5
        assert obj.sprite.center_x == 5.0
        assert obj.sprite.center_y == 5.0
        assert obj.sprite.width == 10.0
        assert obj.sprite.height == 10.0

    def test_load_from_tiled_no_interactive_layer(self) -> None:
        """Test load_from_tiled with no Interactive layer - covers lines 120-121."""
        mock_tile_map = MagicMock()
        mock_tile_map.object_lists = {}  # No Interactive layer
        mock_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_scene)

        # Should not have any objects
        assert len(self.plugin.interactive_objects) == 0

    def test_load_from_tiled_object_without_name(self) -> None:
        """Test load_from_tiled with object missing name - covers lines 125-126."""
        mock_tile_map = MagicMock()
        mock_layer = MagicMock()

        mock_obj = MagicMock()
        mock_obj.name = None  # Missing name
        mock_obj.properties = {}
        mock_obj.shape = [(0, 0), (10, 10)]

        mock_layer.__iter__.return_value = [mock_obj]
        mock_tile_map.object_lists = {"Interactive": mock_layer}
        mock_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_scene)

        # Should skip object without name
        assert len(self.plugin.interactive_objects) == 0

    def test_load_from_tiled_nested_list_shape(self) -> None:
        """Test load_from_tiled with nested list shape - covers lines 136-138."""
        mock_tile_map = MagicMock()
        mock_layer = MagicMock()

        mock_obj = MagicMock()
        mock_obj.name = "NestedShape"
        mock_obj.properties = {}
        # Nested list shape like [(x1, y1), (x2, y2)]
        mock_obj.shape = [[10, 20], [30, 40]]

        mock_layer.__iter__.return_value = [mock_obj]
        mock_tile_map.object_lists = {"Interactive": mock_layer}
        mock_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_scene)

        assert "nestedshape" in self.plugin.interactive_objects
        obj = self.plugin.interactive_objects["nestedshape"]
        # min x=10, max x=30 -> center 20, width 20
        # min y=20, max y=40 -> center 30, height 20
        assert obj.sprite.center_x == 20.0
        assert obj.sprite.center_y == 30.0
        assert obj.sprite.width == 20.0
        assert obj.sprite.height == 20.0

    def test_load_from_tiled_flat_list_shape(self) -> None:
        """Test load_from_tiled with flat list shape - covers lines 140-141."""
        mock_tile_map = MagicMock()
        mock_layer = MagicMock()

        mock_obj = MagicMock()
        mock_obj.name = "FlatShape"
        mock_obj.properties = {}
        # Flat list shape [x, y]
        mock_obj.shape = [100, 200]

        mock_layer.__iter__.return_value = [mock_obj]
        mock_tile_map.object_lists = {"Interactive": mock_layer}
        mock_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_scene)

        assert "flatshape" in self.plugin.interactive_objects
        obj = self.plugin.interactive_objects["flatshape"]
        # Single point - center is the point, width and height are 0
        assert obj.sprite.center_x == 100.0
        assert obj.sprite.center_y == 200.0
        assert obj.sprite.width == 0.0
        assert obj.sprite.height == 0.0

    def test_load_from_tiled_invalid_shape(self) -> None:
        """Test load_from_tiled with invalid shape - covers lines 143-144."""
        mock_tile_map = MagicMock()
        mock_layer = MagicMock()

        mock_obj = MagicMock()
        mock_obj.name = "InvalidShape"
        mock_obj.properties = {}
        # Invalid shape (not a list or tuple)
        mock_obj.shape = "not_a_shape"

        mock_layer.__iter__.return_value = [mock_obj]
        mock_tile_map.object_lists = {"Interactive": mock_layer}
        mock_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_scene)

        # Should skip object with invalid shape
        assert len(self.plugin.interactive_objects) == 0

    def test_get_interactive_objects(self) -> None:
        """Test get_interactive_objects - covers line 158."""
        sprite = arcade.Sprite()
        self.plugin.register_object(sprite, "test", {})

        objects = self.plugin.get_interactive_objects()

        assert "test" in objects
        assert objects["test"].name == "test"

    def test_on_key_press_interaction_key(self) -> None:
        """Test on_key_press with interaction key - covers lines 171-186."""
        with patch("pedre.plugins.interaction.plugin.settings") as mock_settings:
            mock_settings.INTERACTION_KEY = "E"

            # Create player sprite
            player_sprite = arcade.Sprite()
            player_sprite.center_x = 0
            player_sprite.center_y = 0
            self.mock_context.player_plugin.get_player_sprite.return_value = player_sprite

            # Create nearby object
            obj_sprite = arcade.Sprite()
            obj_sprite.center_x = 30
            obj_sprite.center_y = 0
            self.plugin.register_object(obj_sprite, "nearby", {})

            # Press interaction key
            result = self.plugin.on_key_press(arcade.key.E, 0)

            assert result is True
            # Verify interaction event was published
            self.mock_context.event_bus.publish.assert_called_once()
            event = self.mock_context.event_bus.publish.call_args[0][0]
            assert isinstance(event, ObjectInteractedEvent)
            assert event.object_name == "nearby"

    def test_on_key_press_no_nearby_object(self) -> None:
        """Test on_key_press with no nearby object."""
        with patch("pedre.plugins.interaction.plugin.settings") as mock_settings:
            mock_settings.INTERACTION_KEY = "E"

            # Create player sprite
            player_sprite = arcade.Sprite()
            player_sprite.center_x = 0
            player_sprite.center_y = 0
            self.mock_context.player_plugin.get_player_sprite.return_value = player_sprite

            # No nearby objects

            # Press interaction key
            result = self.plugin.on_key_press(arcade.key.E, 0)

            # Should return False when no object nearby
            assert result is False

    def test_on_key_press_wrong_key(self) -> None:
        """Test on_key_press with non-interaction key."""
        with patch("pedre.plugins.interaction.plugin.settings") as mock_settings:
            mock_settings.INTERACTION_KEY = "E"

            # Press different key
            result = self.plugin.on_key_press(arcade.key.A, 0)

            # Should return False
            assert result is False

    def test_cleanup(self) -> None:
        """Test cleanup method - covers lines 190-191."""
        # Add some objects
        sprite = arcade.Sprite()
        self.plugin.register_object(sprite, "test", {})
        assert len(self.plugin.interactive_objects) > 0

        self.plugin.cleanup()

        # Objects should be cleared
        assert len(self.plugin.interactive_objects) == 0

    def test_handle_interaction(self) -> None:
        """Test handle_interaction - covers lines 300-303."""
        sprite = arcade.Sprite()
        obj = InteractiveObject(sprite=sprite, name="test_object", properties={})

        result = self.plugin.handle_interaction(obj)

        assert result is True
        # Verify object marked as interacted
        assert self.plugin.has_interacted_with("test_object")
        # Verify event published
        self.mock_context.event_bus.publish.assert_called_once()
        event = self.mock_context.event_bus.publish.call_args[0][0]
        assert isinstance(event, ObjectInteractedEvent)
        assert event.object_name == "test_object"

    def test_mark_as_interacted(self) -> None:
        """Test mark_as_interacted - covers lines 311-312."""
        self.plugin.mark_as_interacted("obj1")

        assert self.plugin.has_interacted_with("obj1")

    def test_has_interacted_with(self) -> None:
        """Test has_interacted_with - covers line 323."""
        # Not interacted yet
        assert not self.plugin.has_interacted_with("obj1")

        # Mark as interacted
        self.plugin.mark_as_interacted("obj1")

        # Now should return True
        assert self.plugin.has_interacted_with("obj1")

    def test_reset(self) -> None:
        """Test reset method - covers lines 327-328."""
        # Add objects and mark interactions
        sprite = arcade.Sprite()
        self.plugin.register_object(sprite, "obj1", {})
        self.plugin.mark_as_interacted("obj1")

        assert len(self.plugin.interactive_objects) > 0
        assert len(self.plugin.interacted_objects) > 0

        self.plugin.reset()

        # Both should be cleared
        assert len(self.plugin.interactive_objects) == 0
        assert len(self.plugin.interacted_objects) == 0

    def test_get_save_state(self) -> None:
        """Test get_save_state - covers line 360."""
        self.plugin.mark_as_interacted("obj1")
        self.plugin.mark_as_interacted("obj2")

        state = self.plugin.get_save_state()

        assert "interacted_objects" in state
        assert "obj1" in state["interacted_objects"]
        assert "obj2" in state["interacted_objects"]

    def test_restore_save_state(self) -> None:
        """Test restore_save_state - covers lines 364-365."""
        state = {"interacted_objects": ["obj1", "obj2"]}

        self.plugin.restore_save_state(state)

        assert self.plugin.has_interacted_with("obj1")
        assert self.plugin.has_interacted_with("obj2")

    def test_restore_save_state_no_interacted_objects(self) -> None:
        """Test restore_save_state with missing key."""
        state = {}  # No interacted_objects key

        self.plugin.restore_save_state(state)

        # Should not crash
        assert len(self.plugin.interacted_objects) == 0

    def test_to_dict(self) -> None:
        """Test to_dict serialization - covers line 369."""
        self.plugin.mark_as_interacted("obj1")
        self.plugin.mark_as_interacted("obj2")

        data = self.plugin.to_dict()

        assert "interacted_objects" in data
        assert "obj1" in data["interacted_objects"]
        assert "obj2" in data["interacted_objects"]

    def test_from_dict(self) -> None:
        """Test from_dict deserialization - covers line 373."""
        data = {"interacted_objects": ["obj1", "obj2"]}

        self.plugin.from_dict(data)

        assert self.plugin.has_interacted_with("obj1")
        assert self.plugin.has_interacted_with("obj2")

    def test_load_from_tiled_no_properties(self) -> None:
        """Test load_from_tiled with object missing properties attribute."""
        mock_tile_map = MagicMock()
        mock_layer = MagicMock()

        mock_obj = MagicMock()
        mock_obj.name = "NoProps"
        # Simulate hasattr(obj, "properties") returning False
        del mock_obj.properties
        mock_obj.shape = [(0, 0), (10, 10)]

        mock_layer.__iter__.return_value = [mock_obj]
        mock_tile_map.object_lists = {"Interactive": mock_layer}
        mock_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_scene)

        # Should handle missing properties gracefully
        assert "noprops" in self.plugin.interactive_objects
        obj = self.plugin.interactive_objects["noprops"]
        assert obj.properties == {}

    def test_clear(self) -> None:
        """Test clear method."""
        # Add objects
        sprite = arcade.Sprite()
        self.plugin.register_object(sprite, "obj1", {})

        self.plugin.clear()

        assert len(self.plugin.interactive_objects) == 0

    def test_on_key_press_no_player(self) -> None:
        """Test on_key_press when player sprite is None."""
        with patch("pedre.plugins.interaction.plugin.settings") as mock_settings:
            mock_settings.INTERACTION_KEY = "E"
            self.mock_context.player_plugin.get_player_sprite.return_value = None

            result = self.plugin.on_key_press(arcade.key.E, 0)

            # Should return False when no player
            assert result is False

    def test_load_from_tiled_shape_with_invalid_points(self) -> None:
        """Test load_from_tiled with nested shape containing invalid points - covers branch 136->135."""
        mock_tile_map = MagicMock()
        mock_layer = MagicMock()

        mock_obj = MagicMock()
        mock_obj.name = "InvalidPoints"
        mock_obj.properties = {}
        # Nested list shape with some invalid points (less than 2 elements)
        # Valid point: [10, 20], invalid points: [30] (only 1 element), [] (empty)
        mock_obj.shape = [[10, 20], [30], [], [40, 50]]

        mock_layer.__iter__.return_value = [mock_obj]
        mock_tile_map.object_lists = {"Interactive": mock_layer}
        mock_scene = MagicMock()

        self.plugin.load_from_tiled(mock_tile_map, mock_scene)

        # Should create object with only the valid points
        assert "invalidpoints" in self.plugin.interactive_objects
        obj = self.plugin.interactive_objects["invalidpoints"]
        # Only points [10, 20] and [40, 50] should be used
        # min x=10, max x=40 -> center 25, width 30
        # min y=20, max y=50 -> center 35, height 30
        assert obj.sprite.center_x == 25.0
        assert obj.sprite.center_y == 35.0
        assert obj.sprite.width == 30.0
        assert obj.sprite.height == 30.0


if __name__ == "__main__":
    unittest.main()
