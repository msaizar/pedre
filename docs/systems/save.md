# SaveManager

Handles game state persistence with auto-save and manual save slots.

## Location

`src/pedre/systems/save.py`

## Initialization

```python
from pedre.systems.save import SaveManager

save_manager = SaveManager(save_directory="saves/")
```

## Key Methods

### `save_game(slot: str, game_state: dict) -> bool`

Save current game state to a slot.

**Parameters:**

- `slot` - Save slot identifier (e.g., "slot_1", "autosave")
- `game_state` - Dictionary containing game state

**Returns:**

- `True` if save successful, `False` otherwise

**Example:**

```python
state = {
    "player": {
        "x": player.center_x,
        "y": player.center_y,
        "facing": "down"
    },
    "current_map": "village.tmx",
    "npcs": {
        "merchant": {"dialog_level": 2}
    },
    "inventory": inventory_manager.get_all_items()
}
save_manager.save_game("slot_1", state)
```

### `load_game(slot: str) -> dict | None`

Load game state from a slot.

**Parameters:**

- `slot` - Save slot identifier

**Returns:**

- Dictionary containing game state if successful
- `None` if slot doesn't exist or load failed

**Example:**

```python
state = save_manager.load_game("slot_1")
if state:
    player.center_x = state["player"]["x"]
    player.center_y = state["player"]["y"]
    # Restore other state...
```

### `delete_save(slot: str) -> bool`

Delete a save file.

**Parameters:**

- `slot` - Save slot identifier

**Returns:**

- `True` if deleted successfully, `False` otherwise

**Example:**

```python
save_manager.delete_save("slot_2")
```

### `list_saves() -> list[str]`

Get list of available save slots.

**Returns:**

- List of save slot identifiers

**Example:**

```python
saves = save_manager.list_saves()
for slot in saves:
    print(f"Found save: {slot}")
```

## Save File Format

Save files are JSON formatted and stored in the save directory:

```text
saves/
  ├── slot_1.json
  ├── slot_2.json
  └── autosave.json
```
