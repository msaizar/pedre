"""Shared pytest configuration and fixtures."""

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import arcade
import pytest

from pedre.conf import settings

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


@pytest.fixture(autouse=True)
def configure_test_settings() -> Generator[None]:
    """Configure settings for each test using the new settings system.

    This fixture runs automatically before each test to configure settings
    and resets them after the test completes.

    Yields:
        None
    """
    # Configure settings with test defaults
    settings.configure(
        SCREEN_WIDTH=1280,
        SCREEN_HEIGHT=720,
        ASSETS_HANDLE="game_assets",
        WINDOW_TITLE="Test",
        MENU_TITLE="Test Menu",
        PLAYER_MOVEMENT_SPEED=3,
        INTERACTION_MANAGER_DISTANCE=50,
        NPC_INTERACTION_DISTANCE=50,
        PORTAL_INTERACTION_DISTANCE=50,
        WAYPOINT_THRESHOLD=2,
        NPC_SPEED=80.0,
        INITIAL_MAP="map.tmx",
        INVENTORY_GRID_COLS=4,
        INVENTORY_GRID_ROWS=3,
        INVENTORY_BOX_SIZE=100,
        INVENTORY_BOX_SPACING=15,
        INVENTORY_BOX_BORDER_WIDTH=3,
        DIALOG_AUTO_CLOSE_DEFAULT=False,
        DIALOG_AUTO_CLOSE_DURATION=0.5,
        MENU_TITLE_SIZE=48,
        MENU_OPTION_SIZE=24,
        MENU_SPACING=50,
        MENU_BACKGROUND_IMAGE="",
        MENU_MUSIC_FILES=[],
        MENU_TEXT_CONTINUE="Continue",
        MENU_TEXT_NEW_GAME="New Game",
        MENU_TEXT_SAVE_GAME="Save Game",
        MENU_TEXT_LOAD_GAME="Load Game",
        MENU_TEXT_EXIT="Exit",
        INVENTORY_BACKGROUND_IMAGE="",
    )
    yield
    # Reset settings after test
    settings._wrapped = None


@pytest.fixture
def headless_window() -> Generator[arcade.Window]:
    """Create a headless arcade window for testing.

    The window no longer needs settings attached as they're available globally
    via the settings singleton.

    Yields:
        Headless arcade window.
    """
    window = arcade.Window(
        width=1280,
        height=720,
        title="Test",
        visible=False,
    )
    yield window
    window.close()
