# NPCManager

Manages NPC state, movement, pathfinding, and interactions.

## Location

`src/pedre/systems/npc.py`

## Initialization

```python
from pedre.systems.npc import NPCManager

npc_manager = NPCManager(
    pathfinding_manager=pathfinding_mgr,
    interaction_distance=50,  # pixels
    waypoint_threshold=2,     # pixels
    npc_speed=80.0,          # pixels/second
    inventory_manager=inventory_mgr,  # optional
    event_bus=event_bus               # optional
)
```

## Key Methods

### `add_npc(name: str, sprite: arcade.Sprite, dialog_level: int = 0) -> None`

Register an NPC in the manager.

**Parameters:**

- `name` - Unique NPC identifier
- `sprite` - The NPC's sprite object
- `dialog_level` - Starting conversation level (default: 0)

**Example:**

```python
merchant_sprite = AnimatedNPC(
    sprite_sheet="assets/images/characters/merchant.png",
    name="merchant"
)
npc_manager.add_npc("merchant", merchant_sprite, dialog_level=0)
```

### `get_nearby_npc(player_position: tuple[float, float]) -> tuple[arcade.Sprite, str, int] | None`

Find an NPC near the player.

**Parameters:**

- `player_position` - (x, y) tuple of player coordinates

**Returns:**

- Tuple of `(sprite, name, dialog_level)` if NPC found nearby
- `None` if no NPC within interaction distance

**Example:**

```python
nearby = npc_manager.get_nearby_npc(player.position)
if nearby:
    sprite, name, dialog_level = nearby
    print(f"Found {name} at dialog level {dialog_level}")
```

### `get_dialog(npc_name: str, scene: str) -> tuple[str, list[str]] | None`

Get dialog for an NPC based on their current conversation level.

**Parameters:**

- `npc_name` - Name of the NPC
- `scene` - Current scene/map name

**Returns:**

- Tuple of `(npc_display_name, dialog_pages)` if dialog exists
- `None` if no dialog configured

**Example:**

```python
dialog = npc_manager.get_dialog("merchant", scene="village")
if dialog:
    display_name, pages = dialog
    dialog_manager.show_dialog(display_name, pages)
```

### `set_dialog_level(npc_name: str, level: int) -> None`

Update an NPC's conversation progress.

**Parameters:**

- `npc_name` - Name of the NPC
- `level` - New dialog level

**Example:**

```python
# After completing a quest
npc_manager.set_dialog_level("merchant", 2)
```

### `move_npc_to_waypoint(npc_name: str, waypoint: tuple[float, float]) -> None`

Start pathfinding movement to a waypoint.

**Parameters:**

- `npc_name` - Name of the NPC to move
- `waypoint` - (x, y) destination coordinates

**Example:**

```python
# Move merchant to the well
npc_manager.move_npc_to_waypoint("merchant", (640, 480))
```

### `update(delta_time: float) -> None`

Update NPC movement and animations (call every frame).

**Parameters:**

- `delta_time` - Time since last update in seconds

**Example:**

```python
def on_update(self, delta_time):
    self.npc_manager.update(delta_time)
```

### `load_dialogs_from_json(json_path: Path | str) -> bool`

Load NPC dialogs from JSON file(s).

**Parameters:**

- `json_path` - Path to JSON file or directory of JSON files

**Returns:**

- `True` if loaded successfully, `False` otherwise

**Example:**

```python
npc_manager.load_dialogs_from_json("assets/dialogs/village_dialogs.json")
# or load all dialogs from a directory
npc_manager.load_dialogs_from_json("assets/dialogs/")
```

## Dialog JSON Format

```json
{
  "npc_name": {
    "0": {
      "name": "Display Name",
      "pages": ["Page 1 text", "Page 2 text"],
      "conditions": [
        {"type": "has_item", "item": "golden_key"}
      ],
      "on_condition_fail": [
        {"type": "show_message", "params": {"message": "Need a key!"}}
      ]
    },
    "1": {
      "name": "Display Name",
      "pages": ["Different dialog after progression"]
    }
  }
}
```

## Events Published

- `NPCInteractedEvent` - When player interacts with NPC
- `NPCMovementCompleteEvent` - When NPC reaches waypoint
- `NPCDisappearCompleteEvent` - When disappear animation finishes
