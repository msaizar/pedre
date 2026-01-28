# DialogManager

Manages dialog display with multi-page support and pagination.

## Location

`src/pedre/systems/dialog/manager.py`

## Initialization

```python
from pedre.systems.dialog import DialogManager

dialog_manager = DialogManager()
```

## Key Methods

### `show_dialog(npc_name: str, text: list[str], *, instant: bool = False, auto_close: bool = False) -> None`

Display a dialog from an NPC.

**Parameters:**

- `npc_name` - Name of the NPC speaking
- `text` - List of dialog text strings, one per page
- `instant` - If True, text appears immediately without letter-by-letter reveal (default: False)
- `auto_close` - If True, dialog automatically closes after configured duration (default: False)

**Example:**

```python
# Manual dialog that player must advance
dialog_manager.show_dialog(
    npc_name="Merchant",
    text=[
        "Welcome to my shop!",
        "Take a look around.",
        "I have the finest wares in town!"
    ]
)

# Auto-closing dialog for cutscenes
dialog_manager.show_dialog(
    npc_name="Narrator",
    text=["The adventure begins..."],
    auto_close=True
)
```

### `advance_page() -> bool`

Advance to the next dialog page or close if on the last page.

**Returns:**

- `True` if dialog was closed (was on last page)
- `False` if advanced to next page

**Example:**

```python
# In your input handler
if key == arcade.key.SPACE:
    was_closed = dialog_manager.advance_page()
    if was_closed:
        # Dialog finished, handle completion
        event_bus.publish(DialogClosedEvent(npc_name="Merchant"))
```

### `get_current_page() -> DialogPage | None`

Get the currently displayed page.

**Returns:**

- `DialogPage` object with `npc_name`, `text`, `page_num`, `total_pages`
- `None` if no dialog is showing

**Example:**

```python
page = dialog_manager.get_current_page()
if page:
    print(f"{page.npc_name}: {page.text}")
    print(f"Page {page.page_num + 1}/{page.total_pages}")
```

### `close_dialog() -> None`

Immediately close the currently showing dialog.

**Example:**

```python
# Force close on ESC key
if key == arcade.key.ESCAPE:
    dialog_manager.close_dialog()
```

### `on_draw_ui(context: GameContext) -> None`

Draw the dialog overlay (called automatically by system loader).

**Parameters:**

- `context` - The GameContext

**Example:**

```python
# Typically called automatically, but can be manual:
dialog_manager.on_draw_ui(game_context)
```

## Properties

- `showing: bool` - Whether a dialog is currently displayed
- `pages: list[DialogPage]` - List of all pages in current dialog
- `current_page_index: int` - Index of currently shown page
