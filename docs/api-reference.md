# API Reference

This document provides a reference for the core classes and methods in the Pedre framework.

## Core Classes

### ViewManager

Central controller for all game views and screen transitions.

```python
from pedre import ViewManager

view_manager = ViewManager(window)
```

**Methods:**

- `show_menu(*, from_game_pause: bool = False)` - Switch to menu view
- `show_game(*, trigger_post_inventory_dialog: bool = False)` - Switch to game view
- `show_inventory()` - Switch to inventory view
- `show_load_game()` - Switch to load game view
- `show_save_game()` - Switch to save game view
- `continue_game()` - Resume or load auto-save
- `load_game(save_data: GameSaveData)` - Load game from save data
- `exit_game()` - Close window and exit

**Properties:**

- `menu_view: MenuView` - Get or create menu view
- `game_view: GameView` - Get or create game view
- `inventory_view: InventoryView` - Get or create inventory view
- `load_game_view: LoadGameView` - Get or create load game view
- `save_game_view: SaveGameView` - Get or create save game view

## Views

### GameView

Primary gameplay view with player control, NPCs, and interactions.

```python
from pedre import GameView

game_view = GameView(view_manager, map_file="level1.tmx", scene_name="forest")
```

**Constructor Parameters:**

- `view_manager: ViewManager` - ViewManager instance
- `map_file: str` - Path to Tiled .tmx map file (optional)
- `scene_name: str` - Unique identifier for this scene (optional)

**Key Managers:**

- `npc_manager: NPCManager` - NPC state and interactions
- `dialog_manager: DialogManager` - Dialog display
- `inventory_manager: InventoryManager` - Item management
- `script_manager: ScriptManager` - Event-driven scripts
- `audio_manager: AudioManager` - Sound and music
- `save_manager: SaveManager` - Game persistence
- `camera_manager: CameraManager` - Camera control
- `portal_manager: PortalManager` - Map transitions
- `interaction_manager: InteractionManager` - Object interactions
- `particle_manager: ParticleManager` - Visual effects

### MenuView

Main menu with navigation and asset preloading.

```python
from pedre import MenuView

menu_view = MenuView(view_manager)
```

### InventoryView

Displays collected items in a grid layout.

```python
from pedre import InventoryView

inventory_view = InventoryView(view_manager, inventory_manager)
```

## Sprite Classes

### AnimatedPlayer

Player character sprite with animation and movement.

```python
from pedre import AnimatedPlayer

player = AnimatedPlayer(
    sprite_sheet_path="player.png",
    sprite_width=32,
    sprite_height=32,
    movement_speed=3.0
)
```

**Methods:**

- `update_animation(delta_time: float)` - Update sprite animation
- `move_to(x: float, y: float)` - Set target position for movement

### AnimatedNPC

Non-player character sprite with animation and AI.

```python
from pedre import AnimatedNPC

npc = AnimatedNPC(
    name="merchant",
    sprite_sheet_path="npc.png",
    sprite_width=32,
    sprite_height=32,
    dialog_level=0
)
```

**Attributes:**

- `name: str` - Unique NPC identifier
- `dialog_level: int` - Current dialog progression

## Game Systems

### NPCManager

Manages all NPCs in the current scene.

```python
from pedre import NPCManager

npc_manager = NPCManager(game_context)
```

**Methods:**

- `add_npc(npc: AnimatedNPC)` - Register an NPC
- `get_npc(name: str) -> AnimatedNPC | None` - Get NPC by name
- `update_dialog_level(npc_name: str, level: int)` - Set dialog progress
- `get_state() -> dict[str, int]` - Get all NPC dialog levels
- `restore_state(state: dict[str, int])` - Restore NPC dialog levels

### DialogManager

Displays conversations with pagination.

```python
from pedre import DialogManager

dialog_manager = DialogManager(game_context)
```

**Methods:**

- `show_dialog(speaker: str, pages: list[str])` - Display dialog
- `next_page()` - Advance to next dialog page
- `close_dialog()` - Close dialog box
- `is_active() -> bool` - Check if dialog is showing
- `draw()` - Render dialog box

### InventoryManager

Manages item collection and display.

```python
from pedre import InventoryManager

inventory_manager = InventoryManager(game_context)
```

**Methods:**

- `add_item(item: InventoryItem)` - Add item to inventory
- `has_item(item_name: str) -> bool` - Check if item exists
- `get_items() -> list[InventoryItem]` - Get all items
- `get_state() -> list[dict]` - Serialize inventory state
- `restore_state(items_data: list[dict])` - Restore from saved state

**InventoryItem:**

```python
from pedre import InventoryItem

item = InventoryItem(
    name="potion",
    image_path="items/potion.png",
    category="consumable"
)
```

### ScriptManager

Executes event-driven scripted sequences.

```python
from pedre import ScriptManager

script_manager = ScriptManager(game_context, scripts_path="scripts.json")
```

**Methods:**

- `handle_event(event_type: str, event_data: dict)` - Process game events
- `is_active() -> bool` - Check if script is running
- `update(delta_time: float)` - Update active script

**Supported Actions:**

- `dialog` - Show conversation
- `move_npc` - Move NPC to position
- `add_to_inventory` - Give item to player
- `play_sfx` - Play sound effect
- `wait` - Pause execution
- `set_dialog_level` - Update NPC dialog progress

### AudioManager

Manages background music and sound effects.

```python
from pedre import AudioManager

audio_manager = AudioManager(game_context)
```

**Methods:**

- `play_music(filename: str, volume: float = 1.0, loop: bool = True)` - Play background music
- `stop_music()` - Stop current music
- `play_sound(filename: str, volume: float = 1.0)` - Play sound effect
- `set_music_volume(volume: float)` - Adjust music volume
- `get_state() -> dict` - Get current audio state
- `restore_state(state: dict)` - Restore audio state

### SaveManager

Handles game state persistence.

```python
from pedre import SaveManager

save_manager = SaveManager(game_context)
```

**Methods:**

- `save_game(slot: int, player_sprite: AnimatedPlayer)` - Save to slot 1-3
- `load_game(slot: int) -> GameSaveData | None` - Load from slot
- `auto_save(player_sprite: AnimatedPlayer)` - Save to auto-save slot
- `load_auto_save() -> GameSaveData | None` - Load auto-save
- `has_save(slot: int) -> bool` - Check if save exists
- `get_save_info(slot: int) -> dict | None` - Get save metadata

**GameSaveData:**

```python
from pedre import GameSaveData

# Loaded from save file
save_data = save_manager.load_game(slot=1)

# Access saved state
current_map = save_data.current_map
player_x = save_data.player_x
player_y = save_data.player_y
npc_states = save_data.npc_dialog_levels
inventory = save_data.inventory_items
```

### CameraManager

Controls camera movement and bounds.

```python
from pedre import CameraManager

camera_manager = CameraManager(window_width, window_height)
```

**Methods:**

- `update(player_x: float, player_y: float)` - Center on player
- `apply()` - Apply camera transformation
- `set_bounds(min_x: float, min_y: float, max_x: float, max_y: float)` - Limit camera area

### PortalManager

Handles map transitions.

```python
from pedre import PortalManager

portal_manager = PortalManager(game_context)
```

**Methods:**

- `add_portal(portal: Portal)` - Register a portal
- `check_portal_collision(sprite: arcade.Sprite) -> Portal | None` - Check if sprite is in portal
- `get_portal_by_name(name: str) -> Portal | None` - Find portal by name

**Portal:**

```python
from pedre import Portal

portal = Portal(
    name="to_forest",
    x=100,
    y=200,
    width=50,
    height=50,
    target_map="forest.tmx",
    target_portal="from_village",
    required_item=None  # Optional item requirement
)
```

### EventBus

Publish-subscribe event system for decoupled communication.

```python
from pedre import EventBus

event_bus = EventBus()

# Subscribe to events
def on_item_collected(event):
    print(f"Collected: {event.item_name}")

event_bus.subscribe("item_collected", on_item_collected)

# Publish events
event_bus.publish(ItemCollectedEvent(item_name="key"))
```

**Methods:**

- `subscribe(event_type: str, callback: Callable)` - Listen for events
- `unsubscribe(event_type: str, callback: Callable)` - Stop listening
- `publish(event: Event)` - Broadcast event to subscribers

### GameContext

Shared state container for all game systems.

```python
from pedre import GameContext

context = GameContext(
    view_manager=view_manager,
    event_bus=event_bus,
    current_scene="village",
    current_map="village.tmx"
)
```

**Attributes:**

- `view_manager: ViewManager` - View controller
- `event_bus: EventBus` - Event system
- `current_scene: str` - Current scene identifier
- `current_map: str` - Current map file

## Events

Common event types used throughout the framework:

- `NPCInteractedEvent` - Player interacted with NPC
- `ItemCollectedEvent` - Item added to inventory
- `DialogClosedEvent` - Dialog finished
- `InventoryClosedEvent` - Inventory view closed
- `PortalTriggeredEvent` - Player entered portal
- `ObjectInteractedEvent` - Player interacted with object

## Configuration

Configuration is handled through the `GameSettings` dataclass:

```python
from pedre import GameSettings

settings = GameSettings(
    screen_width=1280,
    screen_height=720,
    window_title="My RPG",
    player_movement_speed=3,
    tile_size=32,
    interaction_manager_distance=50,
    npc_interaction_distance=50,
    portal_interaction_distance=50,
    inventory_grid_cols=10,
    inventory_grid_rows=4,
    inventory_box_size=30,
    inventory_box_spacing=5
)
```

Access configuration:

```python
from pedre import GameSettings

settings = GameSettings()
window_width = settings.screen_width
player_speed = settings.player_movement_speed
```

## See Also

- [Getting Started Guide](getting-started.md) - Build your first RPG
- [Systems Reference](systems/index.md) - Detailed manager documentation
- [Tiled Integration](tiled-integration.md) - Map editor integration
- [Scripting Guide](scripting/index.md) - Event-driven scripting
