# InventoryManager

Manages player's inventory and item collection with a visual grid overlay.

## Location

- Implementation: [src/pedre/systems/inventory/manager.py](../../src/pedre/systems/inventory/manager.py)
- Base class: [src/pedre/systems/inventory/base.py](../../src/pedre/systems/inventory/base.py)
- Events: [src/pedre/systems/inventory/events.py](../../src/pedre/systems/inventory/events.py)
- Actions: [src/pedre/systems/inventory/actions.py](../../src/pedre/systems/inventory/actions.py)
- Conditions: [src/pedre/systems/inventory/conditions.py](../../src/pedre/systems/inventory/conditions.py)

## Configuration

The InventoryManager uses the following settings from `pedre.conf.settings`:

### Grid Layout Settings

- `INVENTORY_GRID_COLS` - Number of columns in inventory grid (default: 4)
- `INVENTORY_GRID_ROWS` - Number of rows in inventory grid (default: 3)
- `INVENTORY_BOX_SIZE` - Size of each inventory slot in pixels (default: 100)
- `INVENTORY_BOX_SPACING` - Spacing between inventory slots in pixels (default: 15)
- `INVENTORY_BOX_BORDER_WIDTH` - Border width for inventory slots in pixels (default: 3)

### Capacity and Display Settings

- `INVENTORY_MAX_SPACE` - Maximum number of items the inventory can hold (default: 12)
- `INVENTORY_CAPACITY_FONT_SIZE` - Font size for capacity counter (default: 14)
- `INVENTORY_BACKGROUND_IMAGE` - Path to background image (optional, default: "")

### Data and Input Settings

- `INVENTORY_ITEMS_FILE` - Path to JSON file with item definitions (default: "data/inventory_items.json")
- `INVENTORY_KEY_VIEW` - Key to view selected item in detail (default: "V")
- `INVENTORY_KEY_CONSUME` - Key to consume selected item (default: "C")

### Hint Text Settings

- `INVENTORY_HINT_VIEW` - Hint text for viewing items (default: "[V] View")
- `INVENTORY_HINT_CONSUME` - Hint text for consuming items (default: "[C] Consume")
- `INVENTORY_HINT_FONT_SIZE` - Font size for hint text (default: 12)

These can be overridden in your project's `settings.py`:

```python
# Custom inventory settings
INVENTORY_GRID_COLS = 6
INVENTORY_GRID_ROWS = 4
INVENTORY_BOX_SIZE = 80
INVENTORY_MAX_SPACE = 24
INVENTORY_ITEMS_FILE = "data/items.json"
```

## Public API

### Item Management

#### `acquire_item(item_id: str) -> bool`

Mark an item as acquired by the player.

**Parameters:**

- `item_id` - Unique identifier of the item to acquire

**Returns:**

- `True` if the item was newly acquired, `False` if the item was not found, was already acquired, or inventory is at capacity

**Example:**

```python
# When player picks up an item
if inventory_manager.acquire_item("ancient_scroll"):
    # Item was newly acquired
    show_notification("Found: Ancient Scroll!")
else:
    # Item was already owned, doesn't exist, or inventory is full
    pass
```

**Notes:**

- The method enforces inventory capacity limits
- Publishes `ItemAcquiredEvent` when item is newly acquired
- Publishes `ItemAcquisitionFailedEvent` if acquisition fails
- Returns `False` if item doesn't exist in the registry

#### `consume_item(item_id: str) -> bool`

Mark an item as consumed by the player.

**Parameters:**

- `item_id` - Unique identifier of the item to consume

**Returns:**

- `True` if the item was successfully consumed, `False` if the item doesn't exist, hasn't been acquired, or was already consumed

**Example:**

```python
# When player uses a consumable item
if inventory_manager.consume_item("health_potion"):
    # Item was consumed successfully
    restore_player_health(50)
else:
    # Item couldn't be consumed (not available)
    show_message("You don't have that item!")
```

**Notes:**

- Only works on items that have been acquired
- Consumed items no longer appear in the inventory display
- Publishes `ItemConsumedEvent` when successful

#### `add_item(item: InventoryItem) -> bool`

Add a new item to the inventory system and optionally acquire it.

**Parameters:**

- `item` - The `InventoryItem` to add to the system

**Returns:**

- `True` if the item was successfully added, `False` if an item with that ID already exists or if adding it would exceed inventory capacity

**Example:**

```python
from pedre.systems.inventory.base import InventoryItem
import uuid

# Add a health potion that's immediately available
potion = InventoryItem(
    id=str(uuid.uuid4()),  # Generate unique ID
    name="Health Potion",
    description="Restores 50 HP",
    icon_path="items/potion.png",
    category="consumable",
    acquired=True,
    consumable=True
)
if inventory_manager.add_item(potion):
    show_notification("Found: Health Potion!")
```

**Notes:**

- Allows dynamically adding items not defined in `inventory_items.json`
- Useful for consumable items obtained through gameplay
- If `acquired=True`, publishes `ItemAcquiredEvent`
- Checks inventory capacity before adding

#### `has_item(item_id: str) -> bool`

Check if the player has acquired a specific item.

**Parameters:**

- `item_id` - Unique identifier of the item to check

**Returns:**

- `True` if the player has acquired the item, `False` if the item doesn't exist or hasn't been acquired

**Example:**

```python
# Check for key before allowing door interaction
if inventory_manager.has_item("tower_key"):
    unlock_door("tower_entrance")
    dialog_manager.show_dialog("Info", ["The key fits perfectly!"])
else:
    dialog_manager.show_dialog("Info", ["The door is locked."])
```

**Notes:**

- Pure query method with no side effects
- Doesn't modify state or trigger events
- Consumed items return `False`

### State Queries

#### `has_been_accessed() -> bool`

Check if inventory has been accessed by the player.

**Returns:**

- `True` if the player has opened the inventory at least once, `False` otherwise

**Example:**

```python
if inventory_manager.has_been_accessed():
    # Player knows about inventory system
    pass
```

**Notes:**

- Used for tutorial progression
- Flag is set when inventory overlay is first opened
- Persists through save/load

### Save/Load Support

#### `get_save_state() -> dict[str, Any]`

Return serializable state for saving.

**Returns:**

- Dictionary containing inventory state

**Example:**

```python
save_data = {
    "player_position": (x, y),
    "inventory": inventory_manager.get_save_state(),
    # ... other save data
}
```

#### `restore_save_state(state: dict[str, Any]) -> None`

Restore state from save data.

**Parameters:**

- `state` - Dictionary containing saved inventory state

**Example:**

```python
inventory_manager.restore_save_state(save_data["inventory"])
```

### Internal Serialization Methods

#### `to_dict() -> dict[str, dict[str, bool]]`

Convert inventory state to dictionary for save data serialization.

**Returns:**

- Dictionary mapping item IDs to state dictionaries with `acquired` and `consumed` flags

**Example:**

```python
import json
save_data = {
    "inventory": inventory_manager.to_dict(),
    "player_position": (x, y),
}
with open("save.json", "w") as f:
    json.dump(save_data, f)
```

#### `from_dict(data: dict[str, dict[str, bool]]) -> None`

Load inventory state from saved dictionary data.

**Parameters:**

- `data` - Dictionary mapping item IDs to state dictionaries

**Example:**

```python
import json
with open("save.json", "r") as f:
    save_data = json.load(f)
inventory_manager.from_dict(save_data["inventory"])
```

### System Lifecycle

#### `setup(context: GameContext) -> None`

Initialize the inventory system with game context.

**Parameters:**

- `context` - Game context providing access to event bus

**Notes:**

- Called automatically by the SystemLoader
- Loads items from `INVENTORY_ITEMS_FILE`

#### `cleanup() -> None`

Clean up inventory resources when the scene unloads.

**Notes:**

- Clears all items and resets accessed flag
- Called automatically by the SystemLoader

#### `reset() -> None`

Reset inventory state for new game.

**Notes:**

- Clears items, accessed flag, and overlay state
- Reloads default items from JSON

#### `on_key_press(symbol: int, modifiers: int) -> bool`

Handle key presses for inventory overlay.

**Parameters:**

- `symbol` - Arcade key constant
- `modifiers` - Modifier key bitfield

**Returns:**

- `True` if input was consumed, `False` otherwise

**Notes:**

- Called automatically by the SystemLoader
- Press `I` to toggle inventory overlay
- Arrow keys navigate the grid
- `V` views selected item in detail
- `C` consumes selected item
- `ESC` closes overlay

#### `on_draw_ui() -> None`

Draw the inventory overlay in screen coordinates.

**Notes:**

- Called automatically by the SystemLoader during UI draw phase
- Renders grid, items, hints, and capacity counter

## Inventory Items

### InventoryItem Data Class

Items are defined using the `InventoryItem` dataclass:

```python
@dataclass
class InventoryItem:
    id: str                    # Unique identifier
    name: str                  # Display name
    description: str           # Item description
    image_path: str | None     # Path to full-size image (optional)
    icon_path: str | None      # Path to icon/thumbnail (optional)
    category: str              # Item category (default: "general")
    acquired: bool             # Whether player has this item (default: False)
    consumed: bool             # Whether item has been used (default: False)
    consumable: bool           # Whether item can be consumed (default: False)
```

**Attributes:**

- `id` - Unique identifier (e.g., "secret_key", "photo_01"). Used for lookups, save data, and script references.
- `name` - Display name shown to the player (e.g., "Rusty Key", "Family Photo")
- `description` - Flavor text or description shown when examining the item
- `image_path` - Optional path to full-size image file, relative to `assets/`. Displayed when viewing item in detail.
- `icon_path` - Optional path to icon/thumbnail, relative to `assets/`. Displayed in inventory grid.
- `category` - Item category for filtering (e.g., "photo", "note", "key", "potion", "general")
- `acquired` - Whether the player has collected this item
- `consumed` - Whether the item has been consumed/used
- `consumable` - Whether the item can be consumed from the inventory overlay UI

**Example:**

```python
# A collectible photograph
photo = InventoryItem(
    id="beach_memory",
    name="Beach Day",
    description="A sunny day at the coast with friends.",
    image_path="photos/beach.jpg",
    icon_path="photos/icons/beach_icon.png",
    category="photo",
    acquired=False
)

# A consumable item
potion = InventoryItem(
    id="health_potion_1",
    name="Health Potion",
    description="Restores 50 HP",
    icon_path="items/potion.png",
    category="consumable",
    acquired=True,
    consumable=True
)
```

### Item Definition File

Items are typically loaded from a JSON file specified by `INVENTORY_ITEMS_FILE`:

```json
{
  "items": [
    {
      "id": "golden_key",
      "name": "Golden Key",
      "description": "A shiny key that opens the tower door.",
      "image_path": "items/golden_key.png",
      "icon_path": "items/icons/key_icon.png",
      "category": "key",
      "acquired": false
    },
    {
      "id": "beach_photo",
      "name": "Beach Memory",
      "description": "A sunny day at the coast.",
      "image_path": "photos/beach.jpg",
      "icon_path": "photos/icons/beach_icon.png",
      "category": "photo",
      "acquired": false
    },
    {
      "id": "health_potion",
      "name": "Health Potion",
      "description": "Restores 50 HP",
      "icon_path": "items/icons/potion.png",
      "category": "consumable",
      "acquired": false,
      "consumable": true
    }
  ]
}
```

**Notes:**

- All fields except `id`, `name`, and `description` are optional
- Items default to `acquired=false` and `consumable=false`
- Paths are relative to the assets directory

## Events

### ItemAcquiredEvent

Published when player acquires an inventory item for the first time.

**Attributes:**

- `item_id: str` - Unique identifier of the acquired item
- `item_name: str` - Display name of the item

**Script Trigger Example:**

```json
{
    "trigger": {
        "event": "item_acquired",
        "item_id": "rusty_key"
    },
    "actions": [
        {"type": "dialog", "speaker": "Narrator", "text": ["You found a key!"]}
    ]
}
```

**Notes:**

- Only fires when item transitions from unacquired to acquired
- Filter by `item_id` is optional (omit to trigger for any item)

### ItemAcquisitionFailedEvent

Published when an attempt to acquire an item fails.

**Attributes:**

- `item_id: str` - Unique identifier of the item
- `reason: str` - Reason for failure: `"capacity"`, `"unknown_item"`, or `"already_owned"`

**Script Trigger Example:**

```json
{
    "trigger": {
        "event": "item_acquisition_failed",
        "reason": "capacity"
    },
    "actions": [
        {"type": "dialog", "speaker": "Narrator", "text": ["Your inventory is full!"]}
    ]
}
```

**Use Cases:**

- Showing feedback when inventory is full
- Handling unknown item errors
- Preventing duplicate acquisition notifications

### ItemConsumedEvent

Published when player consumes an inventory item.

**Attributes:**

- `item_id: str` - Unique identifier of the consumed item
- `item_name: str` - Display name of the item
- `category: str` - Category of the consumed item

**Script Trigger Example:**

```json
{
    "trigger": {
        "event": "item_consumed",
        "item_id": "health_potion_1"
    },
    "actions": [
        {"type": "dialog", "speaker": "Narrator", "text": ["You feel refreshed!"]}
    ]
}
```

**Filter by category:**

```json
{
    "trigger": {
        "event": "item_consumed",
        "category": "consumable"
    },
    "actions": [
        {"type": "play_sfx", "sound": "potion_drink.wav"}
    ]
}
```

**Notes:**

- Triggers when item is consumed from the inventory overlay or via script action
- Can filter by `item_id`, `category`, or both

### InventoryClosedEvent

Published when the inventory view is closed by the player.

**Attributes:**

- `has_been_accessed: bool` - Whether inventory has been accessed before

**Script Trigger Example:**

```json
{
    "trigger": {
        "event": "inventory_closed"
    },
    "conditions": [
        {
            "check": "inventory_accessed",
            "equals": true
        }
    ],
    "actions": [
        {"type": "dialog", "speaker": "Tutorial", "text": ["Good job checking your inventory!"]}
    ]
}
```

**Use Cases:**

- Tutorial progression
- Achievement triggers
- First-time inventory checks

## Actions

### AcquireItemAction

Give an item to the player's inventory.

**Type:** `acquire_item`

**Parameters:**

- `item_id: str` - Unique identifier of the item to acquire

**Example:**

```json
{
    "type": "acquire_item",
    "item_id": "rusty_key"
}
```

**In a script after finding a treasure chest:**

```json
{
    "actions": [
        {"type": "dialog", "speaker": "Narrator", "text": ["You found a key!"]},
        {"type": "acquire_item", "item_id": "tower_key"},
        {"type": "wait_for_dialog_close"}
    ]
}
```

**Notes:**

- The item must already be defined in the inventory system
- Publishes `ItemAcquiredEvent` on success
- Publishes `ItemAcquisitionFailedEvent` on failure
- Returns `False` and blocks script progression if acquisition fails

### AddItemAction

Add a new item to the inventory system.

**Type:** `add_item`

**Parameters:**

- `name: str` - Display name of the item (required)
- `description: str` - Description text for the item (required)
- `item_id: str` - Unique identifier (optional, auto-generates UUID if omitted)
- `image_path: str` - Path to full-size image (optional)
- `icon_path: str` - Path to icon/thumbnail (optional)
- `category: str` - Item category (default: "general")
- `acquired: bool` - Whether item is immediately acquired (default: true)
- `consumable: bool` - Whether item can be consumed (default: false)

**Example without item_id (UUID auto-generated):**

```json
{
    "type": "add_item",
    "name": "Health Potion",
    "description": "Restores 50 HP",
    "icon_path": "items/potion.png",
    "category": "potion",
    "consumable": true,
    "acquired": true
}
```

**Example with explicit item_id:**

```json
{
    "type": "add_item",
    "item_id": "rusty_key",
    "name": "Rusty Key",
    "description": "Opens an old door",
    "icon_path": "items/key.png",
    "category": "key",
    "acquired": true
}
```

**Notes:**

- Dynamically creates items without requiring JSON definition
- Useful for consumable items obtained through gameplay
- Auto-generates UUID if `item_id` is omitted (prevents conflicts)
- Publishes `ItemAcquiredEvent` if `acquired=true`

### ConsumeItemAction

Consume an item from the player's inventory.

**Type:** `consume_item`

**Parameters:**

- `item_id: str` - Unique identifier of the item to consume

**Example:**

```json
{
    "type": "consume_item",
    "item_id": "health_potion"
}
```

**In a script for using a consumable:**

```json
{
    "actions": [
        {"type": "consume_item", "item_id": "ancient_key"},
        {"type": "dialog", "speaker": "Narrator", "text": ["The key dissolves into dust..."]},
        {"type": "wait_for_dialog_close"}
    ]
}
```

**Notes:**

- Item must be acquired and not already consumed
- Publishes `ItemConsumedEvent` when successful
- Action completes immediately regardless of success

### WaitForInventoryAccessAction

Wait for inventory to be accessed.

**Type:** `wait_inventory_access`

**Parameters:** None

**Example:**

```json
[
    {"type": "dialog", "speaker": "martin", "text": ["Check your inventory!"]},
    {"type": "wait_for_dialog_close"},
    {"type": "wait_inventory_access"},
    {"type": "dialog", "speaker": "martin", "text": ["Great job!"]}
]
```

**Notes:**

- Pauses script execution until player opens inventory
- Useful for tutorial sequences
- Monitors the `has_been_accessed` flag

## Conditions

### inventory_accessed

Check if the player has opened their inventory.

**Parameters:**

- `check`: `"inventory_accessed"`
- `equals`: `true` or `false`

**Example:**

```json
{
    "trigger": {
        "event": "inventory_closed"
    },
    "conditions": [
        {
            "check": "inventory_accessed",
            "equals": true
        }
    ]
}
```

**Use Cases:**

- Tutorial completion
- Achievement triggers
- First-time inventory checks

### item_acquired

Check if an inventory item was acquired.

**Parameters:**

- `check`: `"item_acquired"`
- `item_id`: Item identifier

**Example:**

```json
{
    "trigger": {
        "event": "portal_entered",
        "portal": "dungeon_gate"
    },
    "conditions": [
        {
            "check": "item_acquired",
            "item_id": "dungeon_key"
        }
    ],
    "actions": [
        {"type": "change_scene", "target_map": "dungeon.tmx", "spawn_waypoint": "entrance"}
    ]
}
```

**Use Cases:**

- Gating progression behind item collection
- Quest prerequisite checks
- Conditional NPC responses

## Inventory Overlay

### Opening the Inventory

Press `I` to toggle the inventory overlay. The overlay shows:

- Grid of acquired items with icons
- Selected item name at bottom
- Hints for available actions
- Capacity counter (e.g., "8/12")

### Navigation

- Arrow keys: Move selection in grid
- `V`: View selected item in detail (if it has an image)
- `C`: Consume selected item (if it's consumable)
- `ESC`: Close overlay

### Grid Display

- **Filled slots**: Show items with icons, solid background, white border
- **Empty slots**: Show semi-transparent background, dim border
- **Selected slot**: Yellow border (thicker than normal)

### Photo Viewer

When viewing an item with an `image_path`:

- Full-screen black background
- Photo scaled to fit screen (maintains aspect ratio)
- Item name displayed below photo
- Item description below name
- `ESC` to return to grid

## Custom Inventory Implementation

If you need to replace the inventory system with a custom implementation, you can extend the `InventoryBaseManager` abstract base class.

### InventoryBaseManager

**Location:** [src/pedre/systems/inventory/base.py](../../src/pedre/systems/inventory/base.py)

The `InventoryBaseManager` class defines the minimum interface that any inventory manager must implement.

#### Required Methods

Your custom inventory manager must implement these abstract methods:

```python
from pedre.systems.inventory.base import InventoryBaseManager, InventoryItem

class CustomInventoryManager(InventoryBaseManager):
    """Custom inventory implementation."""

    name = "inventory"
    dependencies = []

    def has_been_accessed(self) -> bool:
        """Check if inventory has been accessed."""
        ...

    def has_item(self, item_id: str) -> bool:
        """Check if the player has acquired a specific item."""
        ...

    def acquire_item(self, item_id: str) -> bool:
        """Mark an item as acquired by the player."""
        ...

    def consume_item(self, item_id: str) -> bool:
        """Mark an item as consumed by the player."""
        ...

    def add_item(self, item: InventoryItem) -> bool:
        """Add a new item to the inventory system."""
        ...
```

#### Registration

Register your custom inventory manager using the `@SystemRegistry.register` decorator:

```python
from pedre.systems.registry import SystemRegistry
from pedre.systems.inventory.base import InventoryBaseManager

@SystemRegistry.register
class CustomInventoryManager(InventoryBaseManager):
    name = "inventory"
    dependencies = []

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom manager inherits from `BaseSystem` (via `InventoryBaseManager`), so you must implement the standard system lifecycle methods: `setup()`, `cleanup()`, and `reset()`
- The `role` attribute is set to `"inventory_manager"` in the base class
- Your implementation can use any storage backend or UI system
- Register your custom inventory manager in your project's `INSTALLED_SYSTEMS` setting before the default `"pedre.systems.inventory"` to replace it

**Example Custom Implementation:**

```python
# In myproject/systems/custom_inventory.py
from pedre.systems.registry import SystemRegistry
from pedre.systems.inventory.base import InventoryBaseManager

@SystemRegistry.register
class DatabaseInventoryManager(InventoryBaseManager):
    """Inventory manager that stores items in a database."""

    name = "inventory"
    dependencies = []

    def __init__(self):
        self.db = Database()
        # ... rest of initialization ...

    def has_item(self, item_id: str) -> bool:
        # Query database for item
        return self.db.query("SELECT acquired FROM items WHERE id = ?", item_id)

    # ... implement other abstract methods ...
```

```python
# In myproject/settings.py
INSTALLED_SYSTEMS = [
    "myproject.systems.custom_inventory",  # Load custom inventory first
    "pedre.systems.camera",
    "pedre.systems.audio",
    # ... rest of systems (omit "pedre.systems.inventory") ...
]
```

## Usage Examples

### Basic Item Collection

```python
# When player picks up an item
if inventory_manager.acquire_item("ancient_scroll"):
    show_notification("Found: Ancient Scroll!")
    audio_manager.play_sfx("item_get.wav")
```

### Conditional Door Unlock

```python
# Check for key before unlocking door
if inventory_manager.has_item("tower_key"):
    unlock_door("tower_entrance")
    dialog_manager.show_dialog("Info", ["The key fits perfectly!"])
else:
    dialog_manager.show_dialog("Info", ["The door is locked."])
```

### Consumable Item

```python
# When player uses a health potion
if inventory_manager.consume_item("health_potion"):
    restore_player_health(50)
    show_notification("HP restored!")
else:
    show_message("You don't have any health potions!")
```

### Tutorial Sequence

```json
{
    "tutorial_inventory": {
        "scene": "casa",
        "trigger": {
            "event": "dialog_closed",
            "npc": "martin",
            "dialog_level": 0
        },
        "actions": [
            {"type": "acquire_item", "item_id": "beach_photo"},
            {"type": "dialog", "speaker": "Martin", "text": ["Check your inventory (press I)!"]},
            {"type": "wait_for_dialog_close"},
            {"type": "wait_inventory_access"},
            {"type": "dialog", "speaker": "Martin", "text": ["Great! You can view the photo by pressing V."]},
            {"type": "wait_for_dialog_close"},
            {"type": "advance_dialog", "npc": "martin"}
        ]
    }
}
```

### Quest Item Gating

```json
{
    "locked_door": {
        "scene": "dungeon",
        "trigger": {
            "event": "object_interacted",
            "object_name": "iron_door"
        },
        "conditions": [
            {
                "check": "item_acquired",
                "item_id": "iron_key"
            }
        ],
        "actions": [
            {"type": "dialog", "speaker": "Narrator", "text": ["The door opens with a creak."]},
            {"type": "wait_for_dialog_close"},
            {"type": "consume_item", "item_id": "iron_key"}
        ]
    },
    "door_locked": {
        "scene": "dungeon",
        "trigger": {
            "event": "object_interacted",
            "object_name": "iron_door"
        },
        "actions": [
            {"type": "dialog", "speaker": "Narrator", "text": ["The door is locked. You need a key."]}
        ]
    }
}
```

## See Also

- [DialogManager](dialog.md) - Conversation system
- [ScriptManager](script.md) - Event-driven scripting
- [Configuration Guide](../configuration.md) - Inventory system settings
- [Scripting Actions](../scripting/actions.md) - Inventory actions
- [Scripting Conditions](../scripting/conditions.md) - Inventory conditions
