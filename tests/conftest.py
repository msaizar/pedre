"""Shared pytest configuration and fixtures."""

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import arcade
import pytest

from pedre.config import GameSettings

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(scope="session", autouse=True)
def _setup_arcade_resources() -> Generator[None]:
    """Set up arcade resource handles for tests.

    This fixture runs automatically for the entire test session and registers
    the game_assets resource handle so that asset_path() calls work in tests.
    If the assets directory doesn't exist, creates a temporary one.
    """
    # Find the assets directory relative to this test file
    tests_dir = Path(__file__).parent
    project_root = tests_dir.parent
    assets_dir = project_root / "assets"

    # If assets directory exists, use it; otherwise create a temporary one
    if assets_dir.exists():
        arcade.resources.add_resource_handle("game_assets", assets_dir.resolve())
        yield
    else:
        # Create a temporary directory to serve as the assets folder
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_assets = Path(temp_dir)

            # Create minimal required structure for tests
            data_dir = temp_assets / "data"
            data_dir.mkdir(exist_ok=True)

            # Create empty inventory items file with correct structure
            inventory_file = data_dir / "inventory_items.json"
            inventory_file.write_text('{"items": []}')

            arcade.resources.add_resource_handle("game_assets", temp_assets.resolve())
            yield


@pytest.fixture
def game_settings() -> GameSettings:
    """Create a GameSettings instance for testing.

    Returns:
        GameSettings with default values.
    """
    return GameSettings()


@pytest.fixture
def headless_window(game_settings: GameSettings) -> Generator[arcade.Window]:
    """Create a headless arcade window for testing with settings attached.

    Args:
        game_settings: GameSettings fixture.

    Yields:
        Headless arcade window with settings attribute.
    """
    window = arcade.Window(
        width=1280,
        height=720,
        title="Test",
        visible=False,
    )
    window.settings = game_settings
    yield window
    window.close()
