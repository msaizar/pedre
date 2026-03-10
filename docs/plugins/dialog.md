# DialogPlugin

Manages dialog display and pagination for game conversations.

## Location

- Implementation: [src/pedre/plugins/dialog/plugin.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/dialog/plugin.py)
- Base class: [src/pedre/plugins/dialog/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/dialog/base.py)
- Events: [src/pedre/plugins/dialog/events.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/dialog/events.py)
- Actions: [src/pedre/plugins/dialog/actions.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/dialog/actions.py)

## Configuration

The DialogPlugin uses the following settings from `pedre.conf.settings`:

### Behavior Settings

- `DIALOG_AUTO_CLOSE_DEFAULT` - Default auto-close behavior when not explicitly specified (default: `False`)
- `DIALOG_AUTO_CLOSE_DURATION` - Seconds to wait after text reveal before auto-closing (default: `0.5`)
- `DIALOG_CHAR_REVEAL_SPEED` - Characters per second for text reveal animation (default: `20`)
- `DIALOG_INSTANT_TEXT_DEFAULT` - Whether text appears instantly by default (default: `False`)
- `DIALOG_SHOW_HELP` - Whether to show instruction text (default: `True`)
- `DIALOG_SHOW_PAGINATION` - Whether to show page indicators (default: `True`)

### Input Settings

- `DIALOG_KEY_ADVANCE` - Key for advancing dialog pages and closing dialogs (default: `"SPACE"`)

### Layout Settings

- `DIALOG_DESIGN` - Dictionary containing design specifications:
  - `box_width` - Width of the dialog box in design units (default: `800`)
  - `box_height` - Height of the dialog box in design units (default: `200`)
  - `border_width` - Width of the dialog box border in design units (default: `3`)
  - `horizontal_padding` - Left/right padding inside the box (default: `20`)
  - `vertical_padding` - Top/bottom padding inside the box (default: `20`)
  - `npc_name_offset` - Vertical offset of NPC name from top of dialog box (default: `30`)
  - `footer_offset` - Vertical offset of footer elements from bottom (default: `20`)
  - `vertical_position` - Dialog box vertical position from bottom as fraction of window height (default: `0.25`)

- `DIALOG_OVERLAY_ALPHA` - Transparency of background overlay (0-255, default: `128`)

### Scaling Settings

- `DIALOG_UI_SCALE_MIN` - Minimum UI scale factor (default: `0.5`)
- `DIALOG_UI_SCALE_MAX` - Maximum UI scale factor (default: `2.0`)

### Visual Settings

- `DIALOG_COLOR_BOX_BACKGROUND` - RGB color of the dialog box background (default: `(45, 52, 54)`)
- `DIALOG_COLOR_BOX_BORDER` - RGB color of the dialog box border (default: `(255, 255, 255)`)
- `DIALOG_COLOR_NPC_NAME` - RGB color of the NPC name text (default: `(255, 255, 0)`)
- `DIALOG_COLOR_TEXT` - RGB color of the dialog text (default: `(255, 255, 255)`)
- `DIALOG_COLOR_INSTRUCTION` - RGB color of instruction text (default: `(211, 211, 211)`)
- `DIALOG_COLOR_PAGE_INDICATOR` - RGB color of page indicator text (default: `(211, 211, 211)`)

### Text Labels

- `DIALOG_TEXT_NEXT_PAGE` - Instruction for advancing to next page (default: `"Press SPACE for next page"`)
- `DIALOG_TEXT_CLOSE` - Instruction for closing dialog (default: `"Press SPACE to close"`)
- `DIALOG_TEXT_PAGE` - Label for page indicator (default: `"Page"`)

These can be overridden in your project's `settings.py`:

```python
# Custom dialog settings
DIALOG_AUTO_CLOSE_DEFAULT = True
DIALOG_AUTO_CLOSE_DURATION = 1.0
DIALOG_CHAR_REVEAL_SPEED = 30
DIALOG_KEY_ADVANCE = "RETURN"

# Custom colors
DIALOG_COLOR_BOX_BACKGROUND = (30, 30, 50)
DIALOG_COLOR_NPC_NAME = (255, 200, 0)

# Custom layout
DIALOG_DESIGN = {
    "box_width": 900,
    "box_height": 250,
    "border_width": 4,
    "horizontal_padding": 30,
    "npc_name_offset": 40,
}
```

## Public API

### Dialog Display

#### show_dialog

`show_dialog(npc_name: str, text: list[str], *, instant: bool = settings.DIALOG_INSTANT_TEXT_DEFAULT, auto_close: bool = settings.DIALOG_AUTO_CLOSE_DEFAULT, dialog_level: int | None = None, npc_key: str | None = None) -> None`

Display a dialog from an NPC.

**Parameters:**

- `npc_name` - Display name of the character speaking (shown at top of dialog box)
- `text` - List of dialog text strings, one per page. Each string can contain multiple lines and will be wrapped automatically
- `instant` - If `True`, text appears immediately without letter-by-letter reveal. Defaults to `settings.DIALOG_INSTANT_TEXT_DEFAULT`. Useful for narration, system messages, or cutscenes
- `auto_close` - If `True`, dialog automatically closes after configured duration. If `False`, player must manually close. Defaults to `settings.DIALOG_AUTO_CLOSE_DEFAULT`
- `dialog_level` - Optional dialog level for event tracking. Used when emitting `DialogClosedEvent`
- `npc_key` - Optional NPC key name for event tracking. If provided, this is used in `DialogClosedEvent` instead of `npc_name`. Use this when the display name differs from the NPC's key name

**Example:**

```python
# Basic dialog with manual advancement
dialog_plugin.show_dialog("Martin", [
    "Hello! I'm Martin, the village elder.",
    "Welcome to our humble town.",
    "Feel free to explore and talk to the other villagers!"
])

# Instant narration dialog
dialog_plugin.show_dialog(
    "Narrator",
    ["The world fades to black..."],
    instant=True
)

# Auto-closing cutscene dialog
dialog_plugin.show_dialog(
    "Plugin",
    ["Achievement unlocked!"],
    instant=True,
    auto_close=True
)

# Dialog with level tracking
dialog_plugin.show_dialog(
    "Merchant",
    ["Thanks for your help!"],
    dialog_level=1,
    npc_key="merchant"
)
```

**Notes:**

- Each string in the text list becomes one page of dialog
- Players advance through pages by pressing the configured `DIALOG_KEY_ADVANCE` key (default: SPACE)
- Text reveals letter-by-letter unless `instant=True` or `settings.DIALOG_INSTANT_TEXT_DEFAULT=True`
- Auto-close timer starts after text is fully revealed
- Publishes `DialogOpenedEvent` when dialog is shown

#### `close_dialog() -> None`

Close the currently showing dialog.

**Example:**

```python
# Force close on ESC key
if key == arcade.key.ESCAPE and dialog_plugin.is_showing():
    dialog_plugin.close_dialog()
```

**Notes:**

- Dismisses the dialog overlay and clears all dialog state
- Called automatically when the player advances past the last page
- Does not publish `DialogClosedEvent` (that only happens via player interaction)

#### advance_page

`advance_page() -> bool`

Advance to the next page or close dialog if on last page.

**Returns:**

- `True` if dialog was closed (was on last page)
- `False` if text was revealed or advanced to next page

**Example:**

```python
# In your input handler
if symbol == arcade.key.SPACE and dialog_plugin.is_showing():
    was_closed = dialog_plugin.advance_page()
    if was_closed:
        # Dialog finished, can trigger follow-up actions
        pass
```

**Notes:**

- If text is still being revealed, it instantly completes the reveal animation
- Otherwise, advances to the next page if there are more pages
- Closes the dialog and returns `True` if on the last page
- Called automatically by the DialogPlugin's `on_key_press` method

### State Queries

#### is_showing

`is_showing() -> bool`

Check if dialog is currently displayed.

**Returns:**

- `True` if a dialog is currently showing, `False` otherwise

**Example:**

```python
if dialog_plugin.is_showing():
    # Don't allow player movement during dialog
    return
```

#### get_current_page

`get_current_page() -> DialogPage | None`

Get the currently displayed page.

**Returns:**

- `DialogPage` object with `npc_name`, `text`, `page_num`, `total_pages`
- `None` if no dialog is showing

**Example:**

```python
page = dialog_plugin.get_current_page()
if page:
    print(f"{page.npc_name}: {page.text}")
    print(f"Page {page.page_num + 1}/{page.total_pages}")
```

### Dialog State Management

#### set_current_dialog_level

`set_current_dialog_level(dialog_level: int) -> None`

Set the current dialog level for event tracking.

**Parameters:**

- `dialog_level` - Dialog level to set

**Notes:**

- Used internally for event emission
- Typically set automatically when showing dialog

#### set_current_npc_name

`set_current_npc_name(npc_name: str) -> None`

Set the current NPC name for event tracking.

**Parameters:**

- `npc_name` - NPC name to set

**Notes:**

- Used internally for event emission
- Typically set automatically when showing dialog

### Text Reveal Control

#### speed_up_text

`speed_up_text() -> None`

Instantly reveal all text on the current page.

**Example:**

```python
# Skip text reveal animation
if user_pressed_skip:
    dialog_plugin.speed_up_text()
```

**Notes:**

- Called automatically when player presses SPACE while text is revealing
- Useful for implementing skip functionality

### Plugin Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the dialog plugin with game settings.

**Parameters:**

- `context` - Game context for accessing the event bus

**Notes:**

- Called automatically by the PluginLoader
- Stores the game context for event publishing

#### cleanup

`cleanup() -> None`

Clean up dialog resources when the scene unloads.

**Notes:**

- Closes any open dialog and clears text objects
- Called automatically by the PluginLoader

#### update

`update(delta_time: float) -> None`

Update the dialog text reveal animation and auto-close timer.

**Parameters:**

- `delta_time` - Time elapsed since last update, in seconds

**Notes:**

- Called automatically every frame
- Handles text reveal animation at rate controlled by `DIALOG_CHAR_REVEAL_SPEED`
- Manages auto-close countdown when enabled

#### on_key_press

`on_key_press(symbol: int, modifiers: int) -> bool`

Handle input for dialog advancement.

**Parameters:**

- `symbol` - Arcade key constant
- `modifiers` - Modifier key bitfield

**Returns:**

- `True` if dialog is showing and event was consumed
- `False` if dialog is not showing

**Notes:**

- Called automatically by the PluginLoader
- Handles the configured `DIALOG_KEY_ADVANCE` key to advance pages or close dialog
- Publishes `DialogClosedEvent` when dialog closes

#### on_draw_ui

`on_draw_ui() -> None`

Draw the dialog overlay in screen coordinates.

**Notes:**

- Called automatically by the PluginLoader during UI draw phase
- Renders the complete dialog UI on top of the game world
- Uses responsive scaling to adapt to different window sizes
- Uses lazy initialization for text objects

## UI Scaling

The dialog plugin uses responsive UI scaling to adapt to different window sizes:

- Design units are scaled based on window dimensions
- Scale factor is computed using `compute_ui_scale()`
- Clamped between `DIALOG_UI_SCALE_MIN` and `DIALOG_UI_SCALE_MAX`
- Font sizes are scaled using `scale_font()` with `UI_FONT_*` tiers
- All layout dimensions are scaled proportionally

**Example:**

```python
# UI scale is computed automatically
ui_scale = compute_ui_scale(
    window.width,
    window.height,
    min_scale=settings.DIALOG_UI_SCALE_MIN,
    max_scale=settings.DIALOG_UI_SCALE_MAX,
)

# Design units are converted to screen pixels
screen_pixels = design_units * ui_scale
```

**Font Tiers:**

The dialog uses the following font tiers from `settings`:

- `UI_FONT_LARGE` - NPC name (default: `(16, 22, 30)`)
- `UI_FONT_NORMAL` - Dialog text (default: `(12, 16, 22)`)
- `UI_FONT_SMALL` - Instructions and page indicator (default: `(8, 12, 16)`)

Each tier is a tuple `(small_screen, reference, large_screen)` that interpolates based on UI scale:

- At `ui_scale <= 0.5`: uses small_screen value
- At `ui_scale == 1.0`: uses reference value
- At `ui_scale >= 2.0`: uses large_screen value
- In between: linear interpolation

## Dialog Configuration Files

Dialogs are loaded from the content registry. Files live in the `dialogs/` subdirectory of your content directory, one file per scene named `{scene}.json`.

```text
assets/
  data/
    content/
      dialogs/
        village.json
        forest.json
```

### JSON Structure

Each file is a flat object. Keys follow the pattern `"{npc_name}/{level}"`:

```json
{
    "npc_name/0": {
        "name": "Display Name",
        "text": [
            "First page of dialog",
            "Second page of dialog"
        ]
    },
    "npc_name/1": {
        "name": "Display Name",
        "text": ["Next dialog level"],
        "conditions": [
            {
                "name": "inventory_accessed",
                "equals": true
            }
        ],
        "on_condition_fail": [
            {
                "name": "dialog",
                "speaker": "Display Name",
                "text": ["Alternative text if condition fails"]
            }
        ]
    }
}
```

**Fields:**

- `name` - Optional display name shown in the dialog box instead of the NPC's key name
- `text` - Required array of strings, one per page
- `conditions` - Optional array of conditions that must be met to show this dialog
- `on_condition_fail` - Optional array of actions to run if conditions fail

### Example Dialog File

```json
{
    "martin/0": {
        "name": "Martin",
        "text": [
            "Buenos días mi amor! Feliz cumpleaños!",
            "Te hice un café, me acompañas a tomarlo?"
        ]
    },
    "martin/1": {
        "name": "Martin",
        "text": ["Qué hermoso día, no?"],
        "conditions": [
            {
                "name": "inventory_accessed",
                "equals": true
            }
        ]
    },
    "merchant/0": {
        "text": [
            "Welcome to my shop!",
            "I have the finest wares in town."
        ]
    }
}
```

See [Dialogs Content Reference](../content/dialogs.md) for the full schema.

## Events

### DialogOpenedEvent

Published when a dialog is shown to the player.

**Attributes:**

- `npc_name: str` - Name of the NPC whose dialog was opened
- `dialog_level: int` - Conversation level at the time dialog was shown

**Script Trigger Example:**

```json
{
    "trigger": {
        "event": "dialog_opened",
        "npc": "martin",
        "dialog_level": 1
    },
    "actions": [
        {"name": "play_sfx", "sound": "dialog_open.wav"}
    ]
}
```

### DialogClosedEvent

Published when a dialog is dismissed by the player.

**Attributes:**

- `npc_name: str` - Name of the NPC whose dialog was closed
- `dialog_level: int` - Conversation level at the time dialog was shown

**Script Trigger Example:**

```json
{
    "trigger": {
        "event": "dialog_closed",
        "npc": "martin",
        "dialog_level": 0
    },
    "actions": [
        {"name": "set_dialog_level", "npc": "martin", "level": 1}
    ]
}
```

**Notes:**

- Trigger filters (`npc`, `dialog_level`) are optional
- Omit `npc` to trigger for any NPC
- Omit `dialog_level` to trigger at any level

## Actions

### DialogAction

Show a dialog to the player.

**Type:** `dialog`

**Parameters:**

- `speaker: str` - Name of the character speaking
- `text: list[str]` - List of dialog pages to show
- `instant: bool` - If `True`, text appears immediately without letter-by-letter reveal. Defaults to `settings.DIALOG_INSTANT_TEXT_DEFAULT` (optional)
- `auto_close: bool` - If `True`, dialog automatically closes after configured duration. If `False`, player must manually close. Defaults to `settings.DIALOG_AUTO_CLOSE_DEFAULT` (optional)

**Example:**

```json
{
    "name": "dialog",
    "speaker": "Martin",
    "text": ["Hello there!", "Welcome to the game."]
}
```

```json
{
    "name": "dialog",
    "speaker": "Narrator",
    "text": ["The world fades to black..."],
    "instant": true,
    "auto_close": true
}
```

**Notes:**

- Action completes immediately after queuing the dialog
- Use `WaitForDialogCloseAction` to wait for player to dismiss the dialog

### WaitForDialogCloseAction

Wait for dialog to be closed.

**Type:** `wait_for_dialog_close`

**Parameters:** None

**Example:**

```json
[
    {"name": "dialog", "speaker": "Martin", "text": ["Hello!"]},
    {"name": "wait_for_dialog_close"},
    {"name": "dialog", "speaker": "Yema", "text": ["Hi there!"]}
]
```

**Notes:**

- Pauses script execution until the player dismisses the currently showing dialog
- Essential for creating proper dialog sequences where each message should be read before continuing

## Custom Dialog Implementation

If you need to replace the dialog plugin with a custom implementation, you can extend the `DialogBasePlugin` abstract base class.

### DialogBasePlugin

**Location:** [src/pedre/plugins/dialog/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/dialog/base.py)

The `DialogBasePlugin` class defines the minimum interface that any dialog plugin must implement.

#### Required Methods

Your custom dialog plugin must implement these abstract methods:

```python
from pedre.conf import settings
from pedre.plugins.dialog.base import DialogBasePlugin

class CustomDialogPlugin(DialogBasePlugin):
    """Custom dialog implementation."""

    name = "dialog"
    dependencies = ["npc", "interaction"]

    def show_dialog(
        self,
        npc_name: str,
        text: list[str],
        *,
        instant: bool = settings.DIALOG_INSTANT_TEXT_DEFAULT,
        auto_close: bool = settings.DIALOG_AUTO_CLOSE_DEFAULT,
        dialog_level: int | None = None,
        npc_key: str | None = None,
    ) -> None:
        """Show a dialog from an NPC."""
        ...

    def set_current_dialog_level(self, dialog_level: int) -> None:
        """Set current dialog level."""
        ...

    def set_current_npc_name(self, npc_name: str) -> None:
        """Set current NPC name."""
        ...

    def is_showing(self) -> bool:
        """Verify if dialog is showing."""
        ...
```

#### Registration

Register your custom dialog plugin using the `@PluginRegistry.register` decorator:

```python
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.dialog.base import DialogBasePlugin

@PluginRegistry.register
class CustomDialogPlugin(DialogBasePlugin):
    name = "dialog"
    dependencies = ["npc", "interaction"]

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom plugin inherits from `BasePlugin` (via `DialogBasePlugin`), so you must implement the standard plugin lifecycle methods: `setup()`, `cleanup()`, and `on_key_press()`
- The `role` attribute is set to `"dialog_plugin"` in the base class
- Your implementation can use any rendering backend, not just Arcade's text system
- Register your custom dialog plugin in your project's `INSTALLED_PLUGINS` setting before the default `"pedre.plugins.dialog"` to replace it

**Example Custom Implementation:**

```python
# In myproject/plugins/custom_dialog.py
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.dialog.base import DialogBasePlugin

@PluginRegistry.register
class RichTextDialogPlugin(DialogBasePlugin):
    """Custom dialog plugin with rich text support."""

    name = "dialog"
    dependencies = ["npc", "interaction"]

    def __init__(self):
        self.showing = False
        self.rich_text_renderer = RichTextRenderer()
        # ... rest of initialization ...

    def show_dialog(
        self,
        npc_name: str,
        text: list[str],
        *,
        instant: bool = settings.DIALOG_INSTANT_TEXT_DEFAULT,
        auto_close: bool = settings.DIALOG_AUTO_CLOSE_DEFAULT,
        dialog_level: int | None = None,
        npc_key: str | None = None,
    ) -> None:
        # Custom rich text dialog display logic
        self.rich_text_renderer.render(npc_name, text)
        self.showing = True

    # ... implement other abstract methods ...
```

```python
# In myproject/settings.py
INSTALLED_PLUGINS = [
    "myproject.plugins.custom_dialog",  # Load custom dialog first
    "pedre.plugins.camera",
    "pedre.plugins.audio",
    # ... rest of plugins (omit "pedre.plugins.dialog") ...
]
```

## Usage Examples

### Basic Dialog Interaction

```python
# Show a simple greeting
dialog_plugin.show_dialog("Guard", [
    "Halt! Who goes there?",
    "State your business in our town."
])
```

### Cutscene with Auto-Close

```python
# Narration that auto-advances
dialog_plugin.show_dialog(
    "Narrator",
    [
        "A long time ago...",
        "In a land far away...",
        "A hero was born."
    ],
    instant=True,
    auto_close=True
)
```

### Scripted Dialog Sequence

```json
{
    "trigger": {
        "event": "npc_interacted",
        "npc": "martin"
    },
    "actions": [
        {
            "name": "dialog",
            "speaker": "Martin",
            "text": ["Hello!", "How are you today?"]
        },
        {
            "name": "wait_for_dialog_close"
        },
        {
            "name": "set_dialog_level",
            "npc": "martin",
            "level": 1
        }
    ]
}
```

### Dialog with Event Tracking

```python
# Show dialog with level tracking for scripts
dialog_plugin.show_dialog(
    "Elder",
    ["You have completed the first trial."],
    dialog_level=1,
    npc_key="elder"
)
# This will publish DialogOpenedEvent(npc_name="elder", dialog_level=1)
# And DialogClosedEvent(npc_name="elder", dialog_level=1) when dismissed
```

## See Also

- [AudioPlugin](audio.md) - Background music and sound effects
- [ScriptPlugin](script.md) - Event-driven scripting
- [NPCPlugin](npc.md) - NPC state and interactions
- [Configuration Guide](../guides/configuration.md)
