"""Unit tests for InteractionManager."""

import unittest
from unittest.mock import MagicMock

import arcade

# Mocking parts of pedre that might not be easily importable without full setup
# We assume pedre package is available in python path
from pedre.systems.interaction.manager import InteractionManager


class TestInteractionManager(unittest.TestCase):
    """Unit test class for InteractionManager."""

    def setUp(self) -> None:
        """Set up InteractionManager."""
        self.manager = InteractionManager()

    def test_register_object(self) -> None:
        """Test registering objects."""
        sprite = arcade.Sprite()
        name = "test_obj"
        properties = {"interaction_type": "message", "message": "Hello"}

        self.manager.register_object(sprite, name, properties)

        assert name in self.manager.interactive_objects
        obj = self.manager.interactive_objects[name]
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
        self.manager.register_object(close_sprite, "close", {})

        # Create a far object (outside 50)
        far_sprite = arcade.Sprite()
        far_sprite.center_x = 200
        far_sprite.center_y = 0
        self.manager.register_object(far_sprite, "far", {})

        # Check nearby object
        nearby = self.manager.get_nearby_object(player)
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
        self.manager.register_object(far_sprite, "far", {})

        nearby = self.manager.get_nearby_object(player)
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

        self.manager.load_from_tiled(mock_tile_map, mock_scene)

        assert "testobj" in self.manager.interactive_objects
        obj = self.manager.interactive_objects["testobj"]

        # Check if sprite was created with correct dimensions
        # min x=0, max x=10 -> width 10, center_x 5
        # min y=0, max y=10 -> height 10, center_y 5
        assert obj.sprite.center_x == 5.0
        assert obj.sprite.center_y == 5.0
        assert obj.sprite.width == 10.0
        assert obj.sprite.height == 10.0


if __name__ == "__main__":
    unittest.main()
