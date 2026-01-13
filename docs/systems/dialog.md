# DialogManager

Manages dialog display with multi-page support and pagination.

## Location

`src/pedre/systems/dialog.py`

## Initialization

```python
from pedre.systems.dialog import DialogManager

dialog_manager = DialogManager()
```

## Key Methods

### `show_dialog(npc_name: str, text: list[str]) -> None`

Display a dialog from an NPC.

**Parameters:**

- `npc_name` - Name of the NPC speaking
- `text` - List of dialog text strings, one per page

**Example:**

```python
dialog_manager.show_dialog(
    npc_name="Merchant",
    text=[
        "Welcome to my shop!",
        "Take a look around.",
        "I have the finest wares in town!"
    ]
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

### `draw(window: arcade.Window) -> None`

Draw the dialog overlay (call in your view's `on_draw()`).

**Parameters:**

- `window` - The game window

**Example:**

```python
def on_draw(self):
    self.scene.draw()
    # Draw dialog on top
    self.dialog_manager.draw(self.window)
```

## Properties

- `showing: bool` - Whether a dialog is currently displayed
- `pages: list[DialogPage]` - List of all pages in current dialog
- `current_page_index: int` - Index of currently shown page
