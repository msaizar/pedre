# InventoryManager

Manages item collection and categorization.

## Location

`src/pedre/systems/inventory.py`

## Initialization

```python
from pedre.systems.inventory import InventoryManager

inventory_manager = InventoryManager()
```

## Key Methods

### `add_item(item_name: str, category: str = "items") -> None`

Add an item to the inventory.

**Parameters:**

- `item_name` - Unique item identifier
- `category` - Item category (e.g., "keys", "photos", "notes")

**Example:**

```python
inventory_manager.add_item("golden_key", category="keys")
inventory_manager.add_item("beach_photo", category="photos")
```

### `has_item(item_name: str) -> bool`

Check if an item is in the inventory.

**Parameters:**

- `item_name` - Item identifier to check

**Returns:**

- `True` if item is in inventory, `False` otherwise

**Example:**

```python
if inventory_manager.has_item("silver_key"):
    # Unlock the door
    pass
```

### `get_items_by_category(category: str) -> list[str]`

Get all items in a specific category.

**Parameters:**

- `category` - Category name

**Returns:**

- List of item names in that category

**Example:**

```python
keys = inventory_manager.get_items_by_category("keys")
for key in keys:
    print(f"You have: {key}")
```

### `get_all_items() -> dict[str, list[str]]`

Get all items organized by category.

**Returns:**

- Dictionary mapping categories to item lists

**Example:**

```python
all_items = inventory_manager.get_all_items()
for category, items in all_items.items():
    print(f"{category}: {', '.join(items)}")
```

## Item Categories

Common categories:

- `"keys"` - Door keys, special keys
- `"photos"` - Collectible photos
- `"notes"` - Letters, documents
- `"quest"` - Quest items
- `"consumables"` - Usable items
