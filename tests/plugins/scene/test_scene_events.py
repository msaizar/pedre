"""Unit tests for scene events."""

import unittest

from pedre.plugins.scene.events import SceneStartEvent


class TestSceneStartEvent(unittest.TestCase):
    """Test SceneStartEvent."""

    def test_init(self) -> None:
        """Test SceneStartEvent initialization."""
        event = SceneStartEvent(scene_name="forest")

        assert event.scene_name == "forest"

    def test_get_script_data(self) -> None:
        """Test get_script_data returns correct dictionary."""
        event = SceneStartEvent(scene_name="dungeon")

        data = event.get_script_data()

        assert data == {"scene": "dungeon"}

    def test_get_script_data_with_different_values(self) -> None:
        """Test get_script_data with different values."""
        event = SceneStartEvent(scene_name="town")

        data = event.get_script_data()

        assert data == {"scene": "town"}


if __name__ == "__main__":
    unittest.main()
