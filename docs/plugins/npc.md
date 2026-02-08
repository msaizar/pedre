# NPCPlugin

Manages NPC state, movement, pathfinding, dialog progression, and interactions.

## Location

- Implementation: [src/pedre/plugins/npc/plugin.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/npc/plugin.py)
- Base class: [src/pedre/plugins/npc/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/npc/base.py)
- Events: [src/pedre/plugins/npc/events.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/npc/events.py)
- Actions: [src/pedre/plugins/npc/actions.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/npc/actions.py)
- Conditions: [src/pedre/plugins/npc/conditions.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/npc/conditions.py)
- Sprites: [src/pedre/plugins/npc/sprites.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/npc/sprites.py)

## Configuration

The NPCPlugin uses the following settings from `pedre.conf.settings`:

### Movement and Interaction Settings

- `NPC_INTERACTION_DISTANCE` - Maximum distance in pixels for player to interact with NPCs (default: 50)
- `NPC_WAYPOINT_THRESHOLD` - Distance in pixels to consider an NPC has reached a waypoint (default: 5)
- `NPC_MOVEMENT_SPEED` - Movement speed in pixels per second (default: 80.0)
- `NPC_INTERACTION_KEY` - Key to interact with NPCs (default: "SPACE")

These can be overridden in your project's `settings.py`:

```python
# Custom NPC settings
NPC_INTERACTION_DISTANCE = 60
NPC_WAYPOINT_THRESHOLD = 8
NPC_MOVEMENT_SPEED = 100.0
NPC_INTERACTION_KEY = "E"
```

## Public API

### NPC Registration

#### register_npc

`register_npc(sprite: arcade.Sprite, name: str) -> None`

Register an NPC sprite for management.

**Parameters:**

- `sprite` - The NPC sprite (typically AnimatedNPC)
- `name` - Unique identifier for the NPC

**Example:**

```python
# Create and register an NPC
npc_sprite = AnimatedNPC(
    sprite_sheet="characters/merchant.png",
    center_x=320,
    center_y=240
)
npc_plugin.register_npc(npc_sprite, "merchant")
```

**Notes:**

- NPCs must be registered before they can be interacted with
- Name should be unique within the scene
- Usually called automatically by `load_npcs_from_objects()`

### Dialog Management

#### load_dialogs_from_json

`load_dialogs_from_json(json_path: Path | str) -> bool`

Load NPC dialog configurations from a JSON file or directory.

**Parameters:**

- `json_path` - Path to JSON file or directory containing dialog files

**Returns:**

- `True` if dialogs loaded successfully, `False` otherwise

**Example:**

```python
# Load from single file
npc_plugin.load_dialogs_from_json("assets/dialogs/village_dialogs.json")

# Load all dialogs from directory
npc_plugin.load_dialogs_from_json("assets/dialogs/")
```

**Notes:**

- Files are named `{scene}_dialogs.json` (e.g., `casa_dialogs.json`)
- Scene name is extracted from filename
- Loading a directory processes all `.json` files

#### get_dialog

`get_dialog(npc_name: str, dialog_level: int, scene: str = "default") -> tuple[NPCDialogConfig | None, list[dict[str, Any]] | None]`

Get dialog for an NPC at a specific conversation level in a scene.

**Parameters:**

- `npc_name` - The NPC name
- `dialog_level` - Current conversation level
- `scene` - Scene name (defaults to "default")

**Returns:**

- Tuple of `(dialog_config, on_condition_fail_actions)`:
  - `dialog_config`: NPCDialogConfig if conditions met, None if no dialog found
  - `on_condition_fail_actions`: List of actions if conditions failed, None otherwise

**Example:**

```python
current_scene = context.scene_plugin.get_current_scene()
dialog_data = npc_plugin.get_dialog("merchant", 0, current_scene)
if dialog_data:
    dialog_config, on_fail = dialog_data
    if dialog_config:
        dialog_plugin.show_dialog("Merchant", dialog_config.text)
```

**Notes:**

- Checks dialog conditions using ConditionRegistry
- Falls back to "default" scene if scene-specific dialog not found
- Returns `on_condition_fail` actions when conditions aren't met

#### advance_dialog

`advance_dialog(npc_name: str) -> int`

Advance the dialog level for an NPC by 1.

**Parameters:**

- `npc_name` - The NPC name

**Returns:**

- The new dialog level

**Example:**

```python
# After completing a conversation
new_level = npc_plugin.advance_dialog("merchant")
print(f"Merchant now at dialog level {new_level}")
```

**Notes:**

- Increments dialog_level by 1
- Dialog level tracks conversation progression
- Used to show different dialog on subsequent interactions

### Movement and Pathfinding

#### move_npc_to_position

`move_npc_to_position(npc_name: str, x: float, y: float) -> None`

Start moving an NPC to a target position using A* pathfinding.

**Parameters:**

- `npc_name` - Name of the NPC to move
- `x` - Target x coordinate in pixels
- `y` - Target y coordinate in pixels

**Example:**

```python
# Move NPC to specific pixel coordinates
npc_plugin.move_npc_to_position("merchant", 320.0, 480.0)
```

**Notes:**

- Uses A* pathfinding to avoid obstacles
- Movement is asynchronous (doesn't block)
- Publishes `NPCMovementCompleteEvent` when destination reached
- Automatically excludes other moving NPCs from pathfinding

#### update

`update(delta_time: float) -> None`

Update NPC movements and animations.

**Parameters:**

- `delta_time` - Time since last update in seconds

**Example:**

```python
def on_update(self, delta_time):
    self.npc_plugin.update(delta_time)
```

**Notes:**

- Called automatically by PluginLoader each frame
- Updates NPC positions along paths
- Updates AnimatedNPC animations
- Publishes movement/animation complete events

### Interaction

#### get_nearby_npc

`get_nearby_npc(player_sprite: arcade.Sprite) -> tuple[arcade.Sprite, str, int] | None`

Find the nearest NPC within interaction distance.

**Parameters:**

- `player_sprite` - The player sprite

**Returns:**

- Tuple of `(sprite, name, dialog_level)` or `None`

**Example:**

```python
player_sprite = context.player_plugin.get_player_sprite()
nearby = npc_plugin.get_nearby_npc(player_sprite)
if nearby:
    sprite, name, dialog_level = nearby
    print(f"Near {name} at level {dialog_level}")
```

**Notes:**

- Uses `NPC_INTERACTION_DISTANCE` setting
- Returns closest NPC within range
- Skips NPCs that are currently moving
- Skips invisible NPCs

#### interact_with_npc

`interact_with_npc(name: str) -> bool`

Trigger interaction with a specific NPC.

**Parameters:**

- `name` - Name of the NPC to interact with

**Returns:**

- `True` if interaction started (dialog shown)

**Example:**

```python
if npc_plugin.interact_with_npc("merchant"):
    print("Started conversation with merchant")
```

**Notes:**

- Retrieves NPC's current dialog
- Checks dialog conditions
- Shows dialog via DialogPlugin
- Marks NPC as interacted in current scene

#### mark_npc_as_interacted

`mark_npc_as_interacted(npc_name: str, scene_name: str | None = None) -> None`

Mark an NPC as interacted with in a specific scene.

**Parameters:**

- `npc_name` - Name of the NPC
- `scene_name` - Scene name (defaults to current scene if not provided)

**Example:**

```python
# Mark NPC as interacted in current scene
npc_plugin.mark_npc_as_interacted("merchant")

# Mark NPC as interacted in specific scene
npc_plugin.mark_npc_as_interacted("guard", "castle")
```

**Notes:**

- Interaction tracking is per-scene
- Used by `npc_interacted` condition check
- Called automatically during normal interactions

#### has_npc_been_interacted_with

`has_npc_been_interacted_with(npc_name: str, scene_name: str | None = None) -> bool`

Check if an NPC has been interacted with in a specific scene.

**Parameters:**

- `npc_name` - Name of the NPC to check
- `scene_name` - Scene name (defaults to current scene if not provided)

**Returns:**

- `True` if the NPC has been interacted with in the specified scene

**Example:**

```python
if npc_plugin.has_npc_been_interacted_with("merchant"):
    print("Player has talked to merchant before")
```

**Notes:**

- Check is scene-specific
- Returns False for NPCs never interacted with
- Used by `npc_interacted` condition

### Visibility Management

#### show_npcs

`show_npcs(npc_names: list[str]) -> None`

Make hidden NPCs visible and add them to collision.

**Parameters:**

- `npc_names` - List of NPC names to reveal

**Example:**

```python
# Reveal multiple NPCs at once
npc_plugin.show_npcs(["guard", "captain", "merchant"])
```

**Notes:**

- Makes sprite.visible = True
- Starts appear animation for AnimatedNPCs
- Adds NPC to wall collision list
- Used by `start_appear_animation` action

### State Queries

#### get_npc_by_name

`get_npc_by_name(name: str) -> NPCState | None`

Get NPC state by name.

**Parameters:**

- `name` - The NPC name

**Returns:**

- NPCState or None if not found

**Example:**

```python
npc = npc_plugin.get_npc_by_name("merchant")
if npc:
    print(f"Merchant at ({npc.sprite.center_x}, {npc.sprite.center_y})")
    print(f"Dialog level: {npc.dialog_level}")
    print(f"Moving: {npc.is_moving}")
```

#### get_npcs

`get_npcs() -> dict[str, NPCState]`

Get all registered NPCs.

**Returns:**

- Dictionary mapping NPC names to NPCState instances

**Example:**

```python
for name, npc in npc_plugin.get_npcs().items():
    print(f"{name}: level {npc.dialog_level}, moving={npc.is_moving}")
```

#### has_moving_npcs

`has_moving_npcs() -> bool`

Check if any NPCs are currently moving.

**Returns:**

- `True` if at least one NPC is currently moving

**Example:**

```python
if npc_plugin.has_moving_npcs():
    print("Cannot pause: NPCs are moving")
```

**Notes:**

- Useful for blocking pausing during cutscenes
- Checks is_moving flag for all NPCs

### Save/Load Support

#### get_save_state

`get_save_state() -> dict[str, Any]`

Return serializable state for saving.

**Returns:**

- Dictionary containing NPC states and interaction history

**Example:**

```python
save_data = {
    "player_position": (x, y),
    "npc": npc_plugin.get_save_state(),
    # ... other save data
}
```

**Notes:**

- Saves positions, visibility, dialog levels, animation flags
- Saves per-scene interaction history

#### restore_save_state

`restore_save_state(state: dict[str, Any]) -> None`

Phase 1: No metadata to restore for NPCs (sprites don't exist yet).

**Parameters:**

- `state` - Dictionary containing saved NPC state

#### apply_entity_state

`apply_entity_state(state: dict[str, Any]) -> None`

Phase 2: Apply saved NPC state after sprites exist.

**Parameters:**

- `state` - Dictionary containing saved NPC state

**Example:**

```python
npc_plugin.apply_entity_state(save_data["npc"])
```

**Notes:**

- Restores positions, visibility, dialog levels
- Restores animation flags for AnimatedNPCs
- Restores per-scene interaction history

### Scene Caching

#### cache_scene_state

`cache_scene_state(scene_name: str) -> dict[str, Any]`

Return state to cache during scene transitions.

**Parameters:**

- `scene_name` - Name of the scene being cached

**Returns:**

- Dictionary containing NPC entity state for the scene

**Notes:**

- Only caches NPC entity state (positions, visibility, dialog levels)
- Interaction history is global and saved separately

#### restore_scene_state

`restore_scene_state(scene_name: str, state: dict[str, Any]) -> None`

Restore cached state when returning to a scene.

**Parameters:**

- `scene_name` - Name of the scene being restored
- `state` - Previously cached state

### Plugin Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the NPC plugin with game context.

**Parameters:**

- `context` - Game context providing access to other plugins

**Notes:**

- Called automatically by PluginLoader
- Stores reference to game context

#### cleanup

`cleanup() -> None`

Clean up NPC resources when the scene unloads.

**Notes:**

- Clears all registered NPCs
- Clears dialog cache
- Called automatically by PluginLoader

#### reset

`reset() -> None`

Reset NPC plugin for new game.

**Notes:**

- Clears NPCs, dialogs, and interaction history
- Called when starting a new game

#### on_key_press

`on_key_press(symbol: int, modifiers: int) -> bool`

Handle key presses for NPC interaction.

**Parameters:**

- `symbol` - Arcade key constant
- `modifiers` - Modifier key bitfield

**Returns:**

- `True` if input was consumed

**Notes:**

- Called automatically by PluginLoader
- Checks for NPC_INTERACTION_KEY press
- Finds nearby NPC and triggers interaction

#### load_from_tiled

`load_from_tiled(tile_map: arcade.TileMap, arcade_scene: arcade.Scene) -> None`

Load NPCs from Tiled map object layer.

**Parameters:**

- `tile_map` - The loaded Tiled map
- `arcade_scene` - The arcade Scene to add NPCs to

**Notes:**

- Called automatically by PluginLoader
- Looks for "NPCs" object layer
- Creates AnimatedNPC sprites from object data

## NPC Data Structures

### NPCState

Runtime state tracking for a single NPC.

**Attributes:**

- `sprite: arcade.Sprite` - The NPC's sprite
- `name: str` - Unique identifier
- `dialog_level: int` - Current conversation level (default: 0)
- `path: deque[tuple[float, float]]` - Pathfinding waypoints
- `is_moving: bool` - Whether NPC is currently moving
- `appear_event_emitted: bool` - Tracks if appear event published
- `disappear_event_emitted: bool` - Tracks if disappear event published

**Example:**

```python
npc = npc_plugin.get_npc_by_name("merchant")
print(f"Dialog level: {npc.dialog_level}")
print(f"Position: ({npc.sprite.center_x}, {npc.sprite.center_y})")
print(f"Moving: {npc.is_moving}, Path length: {len(npc.path)}")
```

### NPCDialogConfig

Configuration for NPC dialog at a specific conversation level.

**Attributes:**

- `text: list[str]` - Dialog text pages to display
- `name: str | None` - Optional display name for speaker
- `conditions: list[dict[str, Any]] | None` - Optional conditions to check
- `on_condition_fail: list[dict[str, Any]] | None` - Actions to execute if conditions fail

**Example:**

```python
dialog_config = NPCDialogConfig(
    text=["Hello!", "Welcome to my shop."],
    name="Merchant",
    conditions=[{"check": "inventory_accessed", "equals": True}],
    on_condition_fail=[
        {"type": "dialog", "speaker": "Merchant", "text": ["Check your inventory first!"]}
    ]
)
```

## Dialog Plugin

### Dialog JSON Format

Dialog files are named `{scene}_dialogs.json` (e.g., `casa_dialogs.json`). The scene name is extracted from the filename.

```json
{
  "npc_name": {
    "0": {
      "name": "Display Name",
      "text": ["First conversation page", "Second page"],
      "conditions": [
        {"check": "inventory_accessed", "equals": true}
      ],
      "on_condition_fail": [
        {"type": "dialog", "speaker": "NPC", "text": ["Not ready yet!"]}
      ]
    },
    "1": {
      "name": "Display Name",
      "text": ["Different dialog after progression"]
    }
  }
}
```

**Structure:**

- Top level: NPC name (key used in scripts)
- Second level: Dialog level (string, converted to int)
- Third level: Dialog configuration object

**Fields:**

- `name` (optional) - Display name shown in dialog box
- `text` (required) - Array of dialog pages
- `conditions` (optional) - Array of condition checks
- `on_condition_fail` (optional) - Array of actions if conditions fail

### Scene-Aware Dialogs

Dialogs are organized by scene, allowing NPCs to have different conversations depending on location:

```python
# Load scene-specific dialogs
npc_plugin.load_scene_dialogs("village")

# Get dialog for current scene
current_scene = context.scene_plugin.get_current_scene()
dialog_data = npc_plugin.get_dialog("merchant", 0, current_scene)
```

If no scene-specific dialog exists, the plugin falls back to "default" scene.

### Dialog Conditions

Dialog can be conditional based on game state:

```json
{
  "merchant": {
    "1": {
      "name": "Merchant",
      "text": ["You checked your inventory!"],
      "conditions": [
        {"check": "inventory_accessed", "equals": true}
      ],
      "on_condition_fail": [
        {"type": "dialog", "speaker": "Merchant", "text": ["Please check your inventory first!"]}
      ]
    }
  }
}
```

When conditions fail:

1. Returns None for dialog_config
2. Returns on_condition_fail actions
3. Scripts can execute fallback actions

## AnimatedNPC Sprites

AnimatedNPCs are specialized sprites with multi-directional animations and special effects.

### Creating AnimatedNPC

```python
from pedre.plugins.npc.sprites import AnimatedNPC

npc = AnimatedNPC(
    sprite_sheet="characters/merchant.png",
    center_x=320,
    center_y=240,
    scale=2.0,
    tile_size=32,
    # Walk animations (4 directions)
    walk_up_frames=4,
    walk_up_row=0,
    walk_down_frames=4,
    walk_down_row=1,
    walk_left_frames=4,
    walk_left_row=2,
    walk_right_frames=4,
    walk_right_row=3,
    # Idle animations
    idle_up_frames=1,
    idle_up_row=4,
    idle_down_frames=1,
    idle_down_row=5,
    # Special animations
    appear_frames=6,
    appear_row=8,
    disappear_frames=6,
    disappear_row=9
)
```

### Animation Properties

**Base Animation Properties (from sprite sheet):**

- `walk_up_frames`, `walk_up_row` - Walk upward animation
- `walk_down_frames`, `walk_down_row` - Walk downward animation
- `walk_left_frames`, `walk_left_row` - Walk left animation
- `walk_right_frames`, `walk_right_row` - Walk right animation
- `idle_up_frames`, `idle_up_row` - Idle facing up
- `idle_down_frames`, `idle_down_row` - Idle facing down
- `idle_left_frames`, `idle_left_row` - Idle facing left
- `idle_right_frames`, `idle_right_row` - Idle facing right

**NPC-Specific Special Animations:**

- `appear_frames`, `appear_row` - Appear/spawn animation
- `disappear_frames`, `disappear_row` - Disappear/fade animation
- `interact_up_frames`, `interact_up_row` - Interaction facing up
- `interact_down_frames`, `interact_down_row` - Interaction facing down
- `interact_left_frames`, `interact_left_row` - Interaction facing left
- `interact_right_frames`, `interact_right_row` - Interaction facing right

### Tiled Map Integration

NPCs can be placed in Tiled maps using object layers:

1. Create an "NPCs" object layer
2. Add point objects where NPCs should spawn
3. Set custom properties on each object:

**Required Properties:**

- `name` (string) - Unique NPC identifier (e.g., "merchant")
- `sprite_sheet` (string) - Path to sprite sheet (relative to assets)

**Optional Properties:**

- `tile_size` (int) - Size of each tile in sprite sheet (default: from sheet)
- `scale` (float) - Sprite scale multiplier (default: 1.0)
- `initially_hidden` (bool) - Start invisible (default: false)
- Animation properties (see above)

**Example Tiled Properties:**

```yaml
name: merchant
sprite_sheet: characters/merchant.png
tile_size: 32
scale: 2.0
walk_up_frames: 4
walk_up_row: 0
walk_down_frames: 4
walk_down_row: 1
appear_frames: 6
appear_row: 8
```

## Events

### NPCInteractedEvent

Published when player interacts with an NPC.

**Attributes:**

- `npc_name: str` - Name of the NPC that was interacted with
- `dialog_level: int` - Current conversation level

**Script Trigger Example:**

```json
{
    "trigger": {
        "event": "npc_interacted",
        "npc": "merchant"
    },
    "actions": [
        {"type": "play_sfx", "file": "npc_interact.wav"}
    ]
}
```

**Notes:**

- Fires before dialog is shown
- The `npc` filter is optional (omit to trigger for any NPC)

### NPCMovementCompleteEvent

Published when an NPC completes movement to target.

**Attributes:**

- `npc_name: str` - Name of the NPC that completed movement

**Script Trigger Example:**

```json
{
    "trigger": {
        "event": "npc_movement_complete",
        "npc": "guard"
    },
    "actions": [
        {"type": "dialog", "speaker": "Guard", "text": ["I've arrived!"]}
    ]
}
```

**Notes:**

- Fires when NPC reaches final waypoint
- Path is empty and is_moving is False
- The `npc` filter is optional

### NPCAppearCompleteEvent

Published when an NPC completes appear animation.

**Attributes:**

- `npc_name: str` - Name of the NPC that appeared

**Script Trigger Example:**

```json
{
    "trigger": {
        "event": "npc_appear_complete",
        "npc": "spirit"
    },
    "actions": [
        {"type": "play_sfx", "file": "materialize.wav"},
        {"type": "dialog", "speaker": "Spirit", "text": ["I have been summoned!"]}
    ]
}
```

**Notes:**

- Only AnimatedNPCs have appear animations
- Used internally by WaitForNPCsAppearAction
- The `npc` filter is optional (omit to trigger for any NPC)
- Useful for triggering dialog or effects after dramatic entrances

### NPCDisappearCompleteEvent

Published when an NPC completes disappear animation.

**Attributes:**

- `npc_name: str` - Name of the NPC that disappeared

**Script Trigger Example:**

```json
{
    "trigger": {
        "event": "npc_disappear_complete",
        "npc": "ghost"
    },
    "actions": [
        {"type": "play_sfx", "file": "vanish.wav"}
    ]
}
```

**Notes:**

- Only AnimatedNPCs have disappear animations
- NPC automatically hidden after animation
- The `npc` filter is optional

## Actions

### MoveNPCAction

Move one or more NPCs to a waypoint using pathfinding.

**Type:** `move_npc`

**Parameters:**

- `npcs: list[str]` - List of NPC names to move
- `waypoint: str` - Name of waypoint to move to

**Example:**

```json
{
    "type": "move_npc",
    "npcs": ["merchant", "guard"],
    "waypoint": "town_square"
}
```

**Notes:**

- Initiates movement immediately
- Doesn't wait for arrival (use `wait_for_movement` for that)
- Uses A* pathfinding to avoid obstacles
- Publishes `NPCMovementCompleteEvent` when done

### StartAppearAnimationAction

Start the appear animation for one or more NPCs.

**Type:** `start_appear_animation`

**Parameters:**

- `npcs: list[str]` - List of NPC names to reveal

**Example:**

```json
{
    "type": "start_appear_animation",
    "npcs": ["spirit", "guardian"]
}
```

**Notes:**

- Makes sprite.visible = True
- Starts appear animation for AnimatedNPCs
- Adds to collision wall list
- Publishes `NPCAppearCompleteEvent` when animation done

### AdvanceDialogAction

Advance an NPC's dialog level by 1.

**Type:** `advance_dialog`

**Parameters:**

- `npc: str` - Name of the NPC

**Example:**

```json
{
    "type": "advance_dialog",
    "npc": "merchant"
}
```

**Notes:**

- Increments dialog_level by 1
- Used to progress conversations
- New level immediately available for next interaction

### SetDialogLevelAction

Set an NPC's dialog level to a specific value.

**Type:** `set_dialog_level`

**Parameters:**

- `npc: str` - Name of the NPC
- `dialog_level: int` - The dialog level to set

**Example:**

```json
{
    "type": "set_dialog_level",
    "npc": "merchant",
    "dialog_level": 5
}
```

**Notes:**

- Sets exact dialog level (doesn't increment)
- Useful for jumping to specific conversation states
- Can reset dialog by setting to 0

### SetCurrentNPCAction

Set the current NPC tracking for dialog event attribution.

**Type:** `set_current_npc`

**Parameters:**

- `npc: str` - Name of the NPC

**Example:**

```json
{
    "type": "set_current_npc",
    "npc": "merchant"
}
```

**Notes:**

- Necessary for scripted dialogs (not from direct interaction)
- Ensures DialogClosedEvent has proper NPC attribution
- Should be used before showing scripted dialog

### WaitForNPCMovementAction

Wait for NPC to complete movement.

**Type:** `wait_for_movement`

**Parameters:**

- `npc: str` - Name of the NPC to wait for

**Example:**

```json
[
    {"type": "move_npc", "npcs": ["guard"], "waypoint": "gate"},
    {"type": "wait_for_movement", "npc": "guard"},
    {"type": "dialog", "speaker": "Guard", "text": ["I'm here!"]}
]
```

**Notes:**

- Pauses script until NPC stops moving
- Checks path is empty and is_moving is False
- Commonly used after move_npc

### WaitForNPCsAppearAction

Wait for multiple NPCs to complete appear animations.

**Type:** `wait_npcs_appear`

**Parameters:**

- `npcs: list[str]` - List of NPC names to wait for

**Example:**

```json
[
    {"type": "start_appear_animation", "npcs": ["spirit", "guardian"]},
    {"type": "wait_npcs_appear", "npcs": ["spirit", "guardian"]},
    {"type": "dialog", "speaker": "Spirit", "text": ["We have arrived!"]}
]
```

**Notes:**

- Only AnimatedNPCs have appear animations
- Waits for all NPCs in list
- Regular sprites complete immediately

### WaitForNPCsDisappearAction

Wait for multiple NPCs to complete disappear animations.

**Type:** `wait_for_npcs_disappear`

**Parameters:**

- `npcs: list[str]` - List of NPC names to wait for

**Example:**

```json
[
    {"type": "start_disappear_animation", "npcs": ["ghost"]},
    {"type": "wait_for_npcs_disappear", "npcs": ["ghost"]},
    {"type": "change_scene", "target_map": "next_area.tmx"}
]
```

**Notes:**

- Only AnimatedNPCs have disappear animations
- Waits for all NPCs in list
- Regular sprites complete immediately

### StartDisappearAnimationAction

Start the disappear animation for one or more NPCs.

**Type:** `start_disappear_animation`

**Parameters:**

- `npcs: list[str]` - List of NPC names to make disappear

**Example:**

```json
{
    "type": "start_disappear_animation",
    "npcs": ["ghost", "spirit"]
}
```

**Notes:**

- Only AnimatedNPCs have disappear animations
- Waits for animations to complete before finishing
- Removes NPCs from wall collision list when done
- Publishes `NPCDisappearCompleteEvent` for each NPC

## Conditions

### npc_interacted

Check if an NPC has been interacted with in a specific scene.

**Parameters:**

- `check`: `"npc_interacted"`
- `npc`: Name of the NPC to check
- `scene`: Optional scene name (defaults to current scene)
- `equals`: Expected value (default: true)

**Example:**

```json
{
    "trigger": {
        "event": "portal_entered",
        "portal": "exit"
    },
    "conditions": [
        {
            "check": "npc_interacted",
            "npc": "guard"
        }
    ]
}
```

**Check if NOT interacted:**

```json
{
    "check": "npc_interacted",
    "npc": "guard",
    "equals": false
}
```

**Use Cases:**

- Gating progression behind conversations
- Quest prerequisites
- Conditional scene transitions

### npc_dialog_level

Check an NPC's dialog level.

**Parameters:**

- `check`: `"npc_dialog_level"`
- `npc`: Name of the NPC
- `equals`: Exact level to match

**Example:**

```json
{
    "trigger": {
        "event": "npc_interacted",
        "npc": "merchant"
    },
    "conditions": [
        {
            "check": "npc_dialog_level",
            "npc": "merchant",
            "equals": 2
        }
    ]
}
```

**Use Cases:**

- Branching conversations
- Quest progression tracking
- Conditional NPC responses

## Usage Examples

### Basic NPC Interaction

```python
# Check for nearby NPC
player_sprite = context.player_plugin.get_player_sprite()
nearby = npc_plugin.get_nearby_npc(player_sprite)
if nearby:
    sprite, name, dialog_level = nearby
    print(f"Near {name} at dialog level {dialog_level}")
```

### Moving an NPC

```json
{
    "move_merchant": {
        "scene": "village",
        "trigger": {
            "event": "object_interacted",
            "object_name": "bell"
        },
        "actions": [
            {"type": "move_npc", "npcs": ["merchant"], "waypoint": "market"},
            {"type": "wait_for_movement", "npc": "merchant"},
            {"type": "dialog", "speaker": "Merchant", "text": ["You called?"]}
        ]
    }
}
```

### Revealing Hidden NPCs

```json
{
    "summon_spirits": {
        "scene": "forest",
        "trigger": {
            "event": "object_interacted",
            "object_name": "ritual_circle"
        },
        "actions": [
            {"type": "play_sfx", "file": "magic.wav"},
            {"type": "start_appear_animation", "npcs": ["spirit_1", "spirit_2", "spirit_3"]},
            {"type": "wait_npcs_appear", "npcs": ["spirit_1", "spirit_2", "spirit_3"]},
            {"type": "dialog", "speaker": "Spirit", "text": ["You have summoned us!"]}
        ]
    }
}
```

### Progressive Conversations

```json
{
    "merchant_chat_1": {
        "scene": "village",
        "trigger": {
            "event": "npc_interacted",
            "npc": "merchant",
            "dialog_level": 0
        },
        "actions": [
            {"type": "dialog", "speaker": "Merchant", "text": ["Hello! Check your inventory."]},
            {"type": "wait_for_dialog_close"},
            {"type": "advance_dialog", "npc": "merchant"}
        ]
    },
    "merchant_chat_2": {
        "scene": "village",
        "trigger": {
            "event": "npc_interacted",
            "npc": "merchant",
            "dialog_level": 1
        },
        "conditions": [
            {"check": "inventory_accessed", "equals": true}
        ],
        "actions": [
            {"type": "dialog", "speaker": "Merchant", "text": ["Great! You found the inventory!"]},
            {"type": "wait_for_dialog_close"},
            {"type": "advance_dialog", "npc": "merchant"}
        ]
    }
}
```

### Coordinated NPC Movement

```json
{
    "guards_assemble": {
        "scene": "castle",
        "trigger": {
            "event": "object_interacted",
            "object_name": "alarm_bell"
        },
        "actions": [
            {"type": "move_npc", "npcs": ["guard_1"], "waypoint": "gate"},
            {"type": "move_npc", "npcs": ["guard_2"], "waypoint": "gate"},
            {"type": "move_npc", "npcs": ["guard_3"], "waypoint": "gate"},
            {"type": "wait_for_movement", "npc": "guard_1"},
            {"type": "wait_for_movement", "npc": "guard_2"},
            {"type": "wait_for_movement", "npc": "guard_3"},
            {"type": "dialog", "speaker": "Captain", "text": ["All guards assembled!"]}
        ]
    }
}
```

### NPC Disappearing

```json
{
    "ghost_vanish": {
        "scene": "haunted_house",
        "trigger": {
            "event": "dialog_closed",
            "npc": "ghost"
        },
        "actions": [
            {"type": "start_disappear_animation", "npcs": ["ghost"]},
            {"type": "wait_for_npcs_disappear", "npcs": ["ghost"]},
            {"type": "play_sfx", "file": "vanish.wav"},
            {"type": "dialog", "speaker": "Narrator", "text": ["The ghost has vanished..."]}
        ]
    }
}
```

## Custom NPC Implementation

If you need to replace the NPC plugin with a custom implementation, you can extend the `NPCBasePlugin` abstract base class.

### NPCBasePlugin

**Location:** [src/pedre/plugins/npc/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/npc/base.py)

The `NPCBasePlugin` class defines the minimum interface that any NPC plugin must implement.

#### Required Methods

Your custom NPC plugin must implement these abstract methods:

```python
from pedre.plugins.npc.base import NPCBasePlugin, NPCState

class CustomNPCPlugin(NPCBasePlugin):
    """Custom NPC implementation."""

    name = "npc"
    dependencies = ["pathfinding"]

    def get_npcs(self) -> dict[str, NPCState]:
        """Get all NPCs."""
        ...

    def load_scene_dialogs(self, scene_name: str) -> dict[str, Any]:
        """Load dialogs for a specific scene."""
        ...

    def get_npc_by_name(self, name: str) -> NPCState | None:
        """Get NPC state by name."""
        ...

    def move_npc_to_position(self, npc_name: str, x: float, y: float) -> None:
        """Start moving an NPC to a target position in pixel coordinates."""
        ...

    def has_npc_been_interacted_with(npc_name: str, scene_name: str | None = None) -> bool:
        """Check if an NPC has been interacted with."""
        ...

    def advance_dialog(self, npc_name: str) -> int:
        """Advance the dialog level for an NPC."""
        ...

    def show_npcs(self, npc_names: list[str]) -> None:
        """Make hidden NPCs visible and add them to collision."""
        ...
```

#### Registration

Register your custom NPC plugin using the `@PluginRegistry.register` decorator:

```python
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.npc.base import NPCBasePlugin

@PluginRegistry.register
class CustomNPCPlugin(NPCBasePlugin):
    name = "npc"
    dependencies = ["pathfinding"]

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom plugin inherits from `BasePlugin` (via `NPCBasePlugin`), so you must implement the standard plugin lifecycle methods: `setup()`, `cleanup()`, and `reset()`
- The `role` attribute is set to `"npc_plugin"` in the base class
- Your implementation can use any dialog storage or movement plugin
- Register your custom NPC plugin in your project's `INSTALLED_PLUGINS` setting before the default `"pedre.plugins.npc"` to replace it

**Example Custom Implementation:**

```python
# In myproject/plugins/custom_npc.py
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.npc.base import NPCBasePlugin

@PluginRegistry.register
class DatabaseNPCPlugin(NPCBasePlugin):
    """NPC plugin that stores state in a database."""

    name = "npc"
    dependencies = ["pathfinding"]

    def __init__(self):
        self.db = Database()
        # ... rest of initialization ...

    def get_npc_by_name(self, name: str) -> NPCState | None:
        # Query database for NPC
        return self.db.query("SELECT * FROM npcs WHERE name = ?", name)

    # ... implement other abstract methods ...
```

```python
# In myproject/settings.py
INSTALLED_PLUGINS = [
    "myproject.plugins.custom_npc",  # Load custom NPC first
    "pedre.plugins.camera",
    "pedre.plugins.audio",
    # ... rest of plugins (omit "pedre.plugins.npc") ...
]
```

## See Also

- [DialogPlugin](dialog.md) - Conversation plugin
- [ScriptPlugin](script.md) - Event-driven scripting
- [PathfindingPlugin](pathfinding.md) - A* pathfinding plugin
- [Configuration Guide](../guides/configuration.md)
- [Scripting Actions](../scripting/actions.md)
- [Scripting Conditions](../scripting/conditions.md)
- [Scripting Events](../scripting/events.md)
