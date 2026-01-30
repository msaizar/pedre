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
- `show_load_game()` - Switch to load game view
- `show_save_game()` - Switch to save game view
- `continue_game()` - Resume or load auto-save
- `load_game(save_data: GameSaveData)` - Load game from save data
- `exit_game()` - Close window and exit
- `load_map(map_name: str, spawn_waypoint: str | None = None)` - Request map load via SceneManager

**Properties:**

- `menu_view: MenuView` - Get or create menu view
- `game_view: GameView` - Get or create game view
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
- `get_save_state() -> dict[str, int]` - Get all NPC dialog levels
- `restore_save_state(state: dict[str, int])` - Restore NPC dialog levels

### DialogManager

Displays conversations with pagination.

```python
from pedre import DialogManager

dialog_manager = DialogManager()
```

**Methods:**

- `show_dialog(npc_name: str, text: list[str], *, instant: bool = settings.DIALOG_INSTANT_TEXT_DEFAULT, auto_close: bool = settings.DIALOG_AUTO_CLOSE_DEFAULT, dialog_level: int | None = None, npc_key: str | None = None)` - Display dialog
  - `npc_name`: Display name of the character speaking (shown at top of dialog box)
  - `text`: List of dialog text strings, one per page
  - `instant`: If True, text appears immediately without letter-by-letter reveal. Defaults to settings.DIALOG_INSTANT_TEXT_DEFAULT
  - `auto_close`: If True, dialog automatically closes after configured duration. If False, player must manually close. Defaults to settings.DIALOG_AUTO_CLOSE_DEFAULT
  - `dialog_level`: Optional dialog level for event tracking
  - `npc_key`: Optional NPC key name for event tracking
- `advance_page() -> bool` - Advance to next dialog page or close if on last page (returns True if closed)
- `close_dialog()` - Close dialog box
- `is_showing() -> bool` - Check if dialog is showing
- `get_current_page() -> DialogPage | None` - Get the currently displayed page
- `set_current_dialog_level(dialog_level: int)` - Set current dialog level for event tracking
- `set_current_npc_name(npc_name: str)` - Set current NPC name for event tracking
- `speed_up_text()` - Instantly reveal all text on the current page
- `setup(context: GameContext)` - Initialize the dialog system
- `cleanup()` - Clean up dialog resources
- `update(delta_time: float)` - Update text reveal animation and auto-close timer
- `on_key_press(symbol: int, modifiers: int) -> bool` - Handle input for dialog advancement
- `on_draw_ui()` - Render dialog box

### SystemLoader

Initializes and manages all game systems.

```python
from pedre.systems import SystemLoader

loader = SystemLoader(context, settings)
loader.load_systems()
```

### SceneManager

Manages scene transitions and map loading.

```python
from pedre.systems import SceneManager
# Accessed via context.get_system("scene")
```

**Methods:**

- `request_transition(map_file: str, spawn_waypoint: str | None = None)` - Request smooth transition
- `load_level(map_file: str, spawn_waypoint: str | None)` - Load map immediately

### InventoryManager

Manages player's inventory and item collection with a visual grid overlay.

```python
from pedre import InventoryManager

inventory_manager = InventoryManager(game_context)
```

**Methods:**

- `acquire_item(item_id: str) -> bool` - Mark an item as acquired by the player
  - Returns `True` if newly acquired, `False` if already owned, doesn't exist, or inventory is full
  - Publishes `ItemAcquiredEvent` on success, `ItemAcquisitionFailedEvent` on failure
- `consume_item(item_id: str) -> bool` - Mark an item as consumed by the player
  - Returns `True` if successfully consumed, `False` if not available
  - Publishes `ItemConsumedEvent` when successful
- `add_item(item: InventoryItem) -> bool` - Add a new item to the inventory system
  - Returns `True` if successfully added, `False` if ID exists or capacity exceeded
  - Useful for dynamically creating items not in JSON
- `has_item(item_id: str) -> bool` - Check if player has acquired a specific item
  - Returns `True` if item exists and is acquired (and not consumed)
  - Pure query with no side effects
- `has_been_accessed() -> bool` - Check if inventory has been opened at least once
- `get_save_state() -> dict[str, Any]` - Serialize inventory state for saving
- `restore_save_state(state: dict[str, Any])` - Restore from saved state
- `to_dict() -> dict[str, dict[str, bool]]` - Convert inventory to dictionary (acquired/consumed flags)
- `from_dict(data: dict[str, dict[str, bool]])` - Load inventory from dictionary
- `setup(context: GameContext)` - Initialize the inventory system
- `cleanup()` - Clean up inventory resources
- `reset()` - Reset inventory state for new game
- `on_key_press(symbol: int, modifiers: int) -> bool` - Handle key presses (I to toggle, arrows to navigate, V to view, C to consume, ESC to close)
- `on_draw_ui()` - Render inventory overlay

**InventoryItem:**

```python
from pedre.systems.inventory.base import InventoryItem

item = InventoryItem(
    id="health_potion",              # Unique identifier
    name="Health Potion",            # Display name
    description="Restores 50 HP",   # Description text
    image_path="items/potion.png",   # Full-size image path (optional)
    icon_path="items/icons/potion.png",  # Icon/thumbnail path (optional)
    category="consumable",           # Item category
    acquired=False,                  # Whether player has this item
    consumed=False,                  # Whether item has been used
    consumable=True                  # Whether item can be consumed from UI
)
```

**Properties:**

- `items: dict[str, InventoryItem]` - All available items (acquired and unacquired)
- `accessed: bool` - Whether inventory has been accessed
- `showing: bool` - Whether inventory overlay is currently visible

See [InventoryManager documentation](systems/inventory.md) for detailed usage.

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
- `follow_player` - Camera follows player
- `follow_npc` - Camera follows NPC
- `stop_camera_follow` - Stop camera following

### InputManager

Manages keyboard input state and movement calculation.

```python
from pedre import InputManager

input_manager = InputManager()
```

**Methods:**

- `on_key_press(symbol: int, modifiers: int) -> bool` - Register key press event
- `on_key_release(symbol: int, modifiers: int) -> bool` - Register key release event
- `get_movement_vector(delta_time: float) -> tuple[float, float]` - Calculate normalized movement vector with frame-rate independent movement
- `is_key_pressed(symbol: int) -> bool` - Check if specific key is pressed
- `clear()` - Clear all pressed keys from input state

**Properties:**

- `movement_speed: float` - Base movement speed in pixels per second
- `keys_pressed: set[int]` - Set of currently pressed key symbols

See [InputManager documentation](systems/input.md) for detailed usage.

### AudioManager

Manages background music and sound effects.

```python
from pedre import AudioManager

audio_manager = AudioManager(game_context)
```

**Methods:**

- `play_music(filename: str, volume: float = 1.0, loop: bool = True)` - Play background music
- `stop_music(fade_duration: float = 1.0)` - Stop current music
- `play_sound(filename: str, volume: float = 1.0)` - Play sound effect
- `set_music_volume(volume: float)` - Adjust music volume
- `get_save_state() -> dict` - Get current audio state
- `restore_save_state(state: dict)` - Restore audio state

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

Controls camera movement with smooth following and boundary constraints.

```python
from pedre import CameraManager

camera_manager = CameraManager(camera, lerp_speed=0.1)
```

**Methods:**

- `smooth_follow(target_x: float, target_y: float)` - Smoothly follow target using interpolation
- `instant_follow(target_x: float, target_y: float)` - Instantly move camera to target
- `set_follow_player(*, smooth: bool = True)` - Automatically follow player sprite
- `set_follow_npc(npc_name: str, *, smooth: bool = True)` - Automatically follow NPC sprite
- `stop_follow()` - Stop following, keep camera at current position
- `set_bounds(map_width: float, map_height: float, viewport_width: float, viewport_height: float)` - Set camera boundaries
- `use()` - Activate camera for rendering
- `update(delta_time: float)` - Update camera position (called automatically)
- `load_from_tiled(tile_map: arcade.TileMap, arcade_scene: arcade.Scene)` - Load camera config from map

**Properties:**

- `camera: arcade.Camera2D` - The managed camera object
- `lerp_speed: float` - Interpolation speed (0.0 to 1.0)
- `bounds: tuple[float, float, float, float] | None` - Boundary constraints (min_x, max_x, min_y, max_y)
- `follow_mode: str | None` - Current follow mode (`"player"`, `"npc"`, or `None`)

See [CameraManager documentation](systems/camera.md) for detailed usage.

### InteractionManager

Manages interactive objects that players can activate in the game world.

```python
from pedre import InteractionManager

interaction_manager = InteractionManager()
```

**Methods:**

- `register_object(sprite: arcade.Sprite, name: str, properties: dict)` - Register an interactive object
- `get_nearby_object(player_sprite: arcade.Sprite) -> InteractiveObject | None` - Get nearest interactive object within interaction distance
- `get_interactive_objects() -> dict[str, InteractiveObject]` - Get all registered interactive objects
- `handle_interaction(obj: InteractiveObject) -> bool` - Handle interaction with an object by publishing an event
- `mark_as_interacted(object_name: str)` - Mark an object as interacted with
- `has_interacted_with(object_name: str) -> bool` - Check if an object has been interacted with
- `clear()` - Clear all registered interactive objects
- `reset()` - Reset both interactive objects and interaction state
- `on_key_press(symbol: int, modifiers: int) -> bool` - Handle interaction input (SPACE key)
- `load_from_tiled(tile_map: arcade.TileMap, arcade_scene: arcade.Scene)` - Load interactive objects from Tiled map

**Properties:**

- `interaction_distance: float` - Maximum distance in pixels for interaction
- `interactive_objects: dict[str, InteractiveObject]` - Dictionary mapping object names to InteractiveObject instances
- `interacted_objects: set[str]` - Set of object names that have been interacted with

See [InteractionManager documentation](systems/interaction.md) for detailed usage.

### PortalManager

Handles map transitions through an event-driven system.

```python
from pedre.systems.portal import PortalManager
from pedre.systems.events import EventBus

event_bus = EventBus()
portal_manager = PortalManager(
    event_bus=event_bus,
    interaction_distance=64.0
)
```

**Methods:**

- `register_portal(sprite: arcade.Sprite, name: str)` - Register a portal from Tiled map data
- `check_portals(player_sprite: arcade.Sprite)` - Check player proximity and publish events on entry
- `clear()` - Clear all registered portals

**Portal:**

```python
from pedre.systems.portal import Portal

@dataclass
class Portal:
    sprite: arcade.Sprite  # Portal location and collision area
    name: str              # Unique identifier for script triggers
```

Portal transitions are handled via scripts using `portal_entered` events and `change_scene` actions.

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
)
```

**Attributes:**

- `view_manager: ViewManager` - View controller
- `event_bus: EventBus` - Event system

## Events

Common event types used throughout the framework:

- `NPCInteractedEvent` - Player interacted with NPC
- `ItemCollectedEvent` - Item added to inventory
- `DialogOpenedEvent` - Dialog window opened
- `DialogClosedEvent` - Dialog finished
- `InventoryClosedEvent` - Inventory view closed
- `PortalEnteredEvent` - Player entered portal zone
- `ObjectInteractedEvent` - Player interacted with object

## Configuration

Configuration is handled through the `settings.py` file:

```python
SCREEN_WIDTH=1280
SCREEN_HEIGHT=720
WINDOW_TITLE="My RPG"
PLAYER_MOVEMENT_SPEED=180.0
TILE_SIZE=32
INTERACTION_MANAGER_DISTANCE=50
NPC_INTERACTION_DISTANCE=50
PORTAL_INTERACTION_DISTANCE=50
INVENTORY_GRID_COLS=10
INVENTORY_GRID_ROWS=4
INVENTORY_BOX_SIZE=30
INVENTORY_BOX_SPACING=5
DIALOG_AUTO_CLOSE_DURATION=0.5  # seconds to wait after text reveal before auto-closing
```

Access configuration:

```python
from pedre.conf import settings

window_width = settings.SCREEN_WIDTH
player_speed = settings.PLAYER_MOVEMENT_SPEED
```

## See Also

- [Getting Started Guide](getting-started.md) - Build your first RPG
- [Systems Reference](systems/index.md) - Detailed manager documentation
- [Tiled Integration](tiled-integration.md) - Map editor integration
- [Scripting Guide](scripting/index.md) - Event-driven scripting
