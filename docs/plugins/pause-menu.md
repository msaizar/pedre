# PauseMenuPlugin

Provides an in-game pause menu overlay that appears when ESC is pressed, offering options like Resume, New Game, Load Game, Save Game, and Exit.

## Location

- Implementation: [src/pedre/plugins/pause_menu/plugin.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/pause_menu/plugin.py)
- Base class: [src/pedre/plugins/pause_menu/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/pause_menu/base.py)

## Configuration

The PauseMenuPlugin uses the following settings from `pedre.conf.settings`:

### Visual Settings

- `PAUSE_MENU_OVERLAY_ALPHA` - Opacity of the semi-transparent overlay (0-255, default: 180)
- `PAUSE_MENU_COLOR_OVERLAY` - RGB color of the overlay (default: (0, 0, 0))
- `PAUSE_MENU_COLOR_BOX_BACKGROUND` - RGB color of the menu box background (default: (102, 102, 153))
- `PAUSE_MENU_COLOR_BOX_BORDER` - RGB color of the menu box border (default: (255, 255, 255))
- `PAUSE_MENU_COLOR_TITLE` - RGB color of the title text (default: (255, 255, 255))
- `PAUSE_MENU_COLOR_OPTION` - RGB color of unselected options (default: (255, 255, 255))
- `PAUSE_MENU_COLOR_SELECTED` - RGB color of the selected option (default: (255, 255, 0))
- `PAUSE_MENU_COLOR_DISABLED` - RGB color of disabled options (default: (128, 128, 128))
- `PAUSE_MENU_COLOR_FEEDBACK` - RGB color of feedback messages (default: (0, 255, 0))

### Text Settings

- `PAUSE_MENU_TITLE` - Title shown at the top of the menu (default: "Pedre Game")
- `PAUSE_MENU_TEXT_RESUME` - Text for Resume option (default: "Resume")
- `PAUSE_MENU_TEXT_NEW_GAME` - Text for New Game option (default: "New Game")
- `PAUSE_MENU_TEXT_LOAD_GAME` - Text for Load Game option (default: "Load Game")
- `PAUSE_MENU_TEXT_SAVE_GAME` - Text for Save Game option (default: "Save Game")
- `PAUSE_MENU_TEXT_EXIT` - Text for Exit option (default: "Exit Game")
- `PAUSE_MENU_TEXT_BACK` - Text for Back option (default: "Back")
- `PAUSE_MENU_TEXT_EMPTY_SLOT` - Text shown for empty save slots (default: "(Empty)")
- `PAUSE_MENU_CONFIRM_NEW_GAME` - Confirmation message for New Game (default: "Start a new game? Current progress will be lost.")

### Layout Settings

- `PAUSE_MENU_DESIGN` - Dictionary containing design specifications:
  - `box_width` - Width of the menu box in design units (default: 500)
  - `box_height` - Height of the menu box in design units (default: 400)
  - `border_width` - Width of the menu box border in design units (default: 4)
  - `title_padding` - Padding above the title in design units (default: 20)
  - `title_area_height` - Height reserved for the title area (default: 80)
  - `horizontal_padding` - Left/right padding inside the box (default: 40)
  - `spacing` - Vertical spacing between options (default: 50)
  - `content_bottom_padding` - Bottom padding for slot lists (default: 20)
  - `confirmation_message_offset` - Vertical offset for confirmation message (default: 50)
  - `confirmation_options_offset` - Vertical offset for confirmation options (default: 30)
  - `feedback_offset` - Offset for feedback messages (default: 50)

### Scaling Settings

- `PAUSE_MENU_UI_SCALE_MIN` - Minimum UI scale factor (default: 0.5)
- `PAUSE_MENU_UI_SCALE_MAX` - Maximum UI scale factor (default: 2.0)

These can be overridden in your project's `settings.py`:

```python
# Custom pause menu settings
PAUSE_MENU_TITLE = "My Awesome Game"
PAUSE_MENU_COLOR_SELECTED = (255, 100, 0)
PAUSE_MENU_OVERLAY_ALPHA = 200

# Customize text
PAUSE_MENU_TEXT_RESUME = "Continue"
PAUSE_MENU_TEXT_EXIT = "Quit"

# Customize layout
PAUSE_MENU_DESIGN = {
    "box_width": 600,
    "box_height": 450,
    "border_width": 5,
    "title_padding": 25,
    "title_area_height": 90,
    "horizontal_padding": 50,
    "spacing": 60,
    "content_bottom_padding": 25,
    "confirmation_message_offset": 60,
    "confirmation_options_offset": 40,
    "feedback_offset": 60,
}
```

## Public API

### Menu Visibility

#### show

`show() -> None`

Show the pause menu overlay.

**Example:**

```python
# Show the pause menu programmatically
pause_menu_plugin.show()
```

**Notes:**

- Resets menu to main menu state
- Resets selected option to first item (Resume)
- Typically triggered automatically by pressing ESC

#### hide

`hide() -> None`

Hide the pause menu overlay.

**Example:**

```python
# Hide the pause menu
pause_menu_plugin.hide()
```

**Notes:**

- Typically called automatically when Resume is selected or ESC is pressed
- Can be called programmatically to close the menu

#### showing

`@property showing -> bool`

Check if the pause menu overlay is currently visible.

**Returns:**

- `True` if the pause menu is currently displayed

**Example:**

```python
if pause_menu_plugin.showing:
    print("Game is paused")
```

**Notes:**

- Use this to check if the game is paused
- Input is consumed by the pause menu when showing

### Plugin Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the pause menu plugin with game context.

**Parameters:**

- `context` - Game context providing access to other plugins

**Notes:**

- Called automatically by PluginLoader
- Stores reference to game context and window

#### cleanup

`cleanup() -> None`

Clean up the pause menu plugin when the scene unloads.

**Notes:**

- Hides the pause menu if showing
- Called automatically by PluginLoader

#### update

`update(delta_time: float) -> None`

Update the pause menu plugin timers.

**Parameters:**

- `delta_time` - Time since last update in seconds

**Example:**

```python
def on_update(self, delta_time):
    self.pause_menu_plugin.update(delta_time)
```

**Notes:**

- Called automatically by PluginLoader each frame
- Updates save feedback message timer

#### on_key_press

`on_key_press(symbol: int, modifiers: int) -> bool`

Handle key presses for pause menu navigation.

**Parameters:**

- `symbol` - Arcade key constant
- `modifiers` - Modifier key bitfield

**Returns:**

- `True` if input was consumed

**Notes:**

- Called automatically by PluginLoader
- Handles UP/DOWN arrow keys for navigation
- Handles ENTER to select options
- Handles ESC to close menu or go back
- Consumes all input when menu is showing

#### on_draw_ui

`on_draw_ui() -> None`

Draw the pause menu overlay in screen coordinates.

**Notes:**

- Called automatically by PluginLoader after all world rendering
- Only draws when menu is showing
- Renders overlay, menu box, title, and options
- Uses responsive scaling based on window size

## Menu States

The pause menu has four distinct states, defined in the `PauseMenuState` enum:

### MAIN_MENU

The default main menu with options: Resume, New Game, Load Game, Save Game, and Exit.

### LOAD_SLOTS

Displays save slots 0-3 for loading games. Slot 0 is the autosave slot.

**Notes:**

- Shows save slot info: map name and save date
- Empty slots are shown as "(Empty)" in disabled color
- Only slots with existing saves can be loaded

### SAVE_SLOTS

Displays save slots 1-3 for saving games. Autosave slot (0) is not available for manual saves.

**Notes:**

- Shows save slot info: map name and save date
- Empty slots are available for new saves
- Overwrites existing saves when selected

### CONFIRMATION

Displays a confirmation dialog with Yes/No options.

**Notes:**

- Currently used for confirming New Game action
- Shows warning message about losing current progress
- Defaults to "No" for safety

## Menu Options

The main menu options are defined in the `PauseMenuOption` enum:

### RESUME (0)

Closes the pause menu and resumes gameplay.

### NEW_GAME (1)

Shows confirmation dialog, then starts a new game if confirmed.

**Notes:**

- Shows warning about losing current progress
- Auto-saves before starting new game
- Resets all game state

### LOAD_GAME (2)

Transitions to load slots menu for selecting a save to load.

### SAVE_GAME (3)

Transitions to save slots menu for selecting where to save.

**Notes:**

- Only manual save slots (1-3) are available
- Shows "Game Saved!" feedback message for 2 seconds

### EXIT (4)

Auto-saves and exits the game.

**Notes:**

- Performs auto-save before exiting
- Closes the game window

## UI Scaling

The pause menu uses responsive UI scaling to adapt to different window sizes:

- Design units are scaled based on window dimensions
- Scale factor is computed using `compute_ui_scale()`
- Clamped between `PAUSE_MENU_UI_SCALE_MIN` and `PAUSE_MENU_UI_SCALE_MAX`
- Font sizes are scaled using `scale_font()`
- All layout dimensions are scaled proportionally

**Example:**

```python
# UI scale is computed automatically
ui_scale = compute_ui_scale(
    window.width,
    window.height,
    min_scale=settings.PAUSE_MENU_UI_SCALE_MIN,
    max_scale=settings.PAUSE_MENU_UI_SCALE_MAX,
)

# Design units are converted to screen pixels
screen_pixels = design_units * ui_scale
```

## Usage Examples

### Basic Usage

The pause menu is typically used automatically:

```python
# User presses ESC - pause menu appears
# User navigates with UP/DOWN arrows
# User selects option with ENTER
# User closes with ESC or selects Resume
```

### Programmatic Control

```python
# Show pause menu from code
pause_menu_plugin.show()

# Check if menu is showing
if pause_menu_plugin.showing:
    print("Game is paused")

# Hide pause menu
pause_menu_plugin.hide()
```

### Customizing Appearance

```python
# In your project's settings.py
PAUSE_MENU_TITLE = "My RPG Adventure"

# Custom colors (RGB tuples)
PAUSE_MENU_COLOR_BOX_BACKGROUND = (50, 50, 100)
PAUSE_MENU_COLOR_SELECTED = (255, 200, 0)
PAUSE_MENU_OVERLAY_ALPHA = 200

# Custom text
PAUSE_MENU_TEXT_NEW_GAME = "Start Over"
PAUSE_MENU_TEXT_LOAD_GAME = "Continue"
PAUSE_MENU_TEXT_SAVE_GAME = "Save Progress"
```

### Custom Layout

```python
# In your project's settings.py
PAUSE_MENU_DESIGN = {
    "box_width": 600,
    "box_height": 500,
    "border_width": 6,
    "spacing": 70,  # More space between options
    "horizontal_padding": 60,
}
```

## Save Integration

The pause menu integrates with the SavePlugin for loading and saving games:

### Loading Games

1. User selects "Load Game" from main menu
2. Menu transitions to load slots view
3. Shows slots 0-3 (autosave + manual saves)
4. User selects a slot with existing save data
5. Save is loaded via `context.load_game(save_data)`
6. Menu closes automatically

### Saving Games

1. User selects "Save Game" from main menu
2. Menu transitions to save slots view
3. Shows slots 1-3 (manual saves only)
4. User selects a slot (empty or existing)
5. Game is saved via `save_plugin.save_game(slot=slot)`
6. "Game Saved!" feedback message appears for 2 seconds
7. Menu returns to main menu

### Auto-Save

Auto-save is triggered automatically when exiting:

```python
# When Exit is selected:
success = context.save_plugin.auto_save()  # Saves to slot 0
if success:
    logger.info("Auto-saved game before exit")
arcade.close_window()
```

## Custom Pause Menu Implementation

If you need to replace the pause menu plugin with a custom implementation, you can extend the `PauseMenuBasePlugin` abstract base class.

### PauseMenuBasePlugin

**Location:** [src/pedre/plugins/pause_menu/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/pause_menu/base.py)

The `PauseMenuBasePlugin` class defines the minimum interface that any pause menu plugin must implement.

#### Required Methods

Your custom pause menu plugin must implement these abstract methods:

```python
from pedre.plugins.pause_menu.base import PauseMenuBasePlugin

class CustomPauseMenuPlugin(PauseMenuBasePlugin):
    """Custom pause menu implementation."""

    name = "pause_menu"
    dependencies = []

    @property
    def showing(self) -> bool:
        """Whether the pause menu overlay is currently visible."""
        ...

    def show(self) -> None:
        """Show the pause menu overlay."""
        ...

    def hide(self) -> None:
        """Hide the pause menu overlay."""
        ...
```

#### Registration

Register your custom pause menu plugin using the `@PluginRegistry.register` decorator:

```python
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.pause_menu.base import PauseMenuBasePlugin

@PluginRegistry.register
class CustomPauseMenuPlugin(PauseMenuBasePlugin):
    name = "pause_menu"
    dependencies = []

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom plugin inherits from `BasePlugin` (via `PauseMenuBasePlugin`), so you must implement the standard plugin lifecycle methods: `setup()`, `cleanup()`, and optionally `update()` and `on_key_press()`
- The `role` attribute is set to `"pause_menu_plugin"` in the base class
- Your implementation can use any UI framework or rendering approach
- Register your custom pause menu plugin in your project's `INSTALLED_PLUGINS` setting before the default `"pedre.plugins.pause_menu"` to replace it

**Example Custom Implementation:**

```python
# In myproject/plugins/custom_pause_menu.py
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.pause_menu.base import PauseMenuBasePlugin

@PluginRegistry.register
class MinimalPauseMenuPlugin(PauseMenuBasePlugin):
    """Minimal pause menu with only Resume and Exit options."""

    name = "pause_menu"
    dependencies = []

    def __init__(self):
        self._showing = False

    @property
    def showing(self) -> bool:
        return self._showing

    def show(self) -> None:
        self._showing = True
        print("Game Paused")

    def hide(self) -> None:
        self._showing = False
        print("Game Resumed")

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        if not self._showing:
            return False
        # Custom key handling...
        return True

    def on_draw_ui(self) -> None:
        if not self._showing:
            return
        # Custom rendering...
```

```python
# In myproject/settings.py
INSTALLED_PLUGINS = [
    "myproject.plugins.custom_pause_menu",  # Load custom pause menu first
    "pedre.plugins.camera",
    "pedre.plugins.audio",
    # ... rest of plugins (omit "pedre.plugins.pause_menu") ...
]
```

## See Also

- [SavePlugin](save.md) - Game save/load functionality
- [Configuration Guide](../guides/configuration.md)
