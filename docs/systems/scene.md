# SceneManager

Manages scene transitions, map loading, lifecycle, and collision detection.

## Location

- Implementation: [src/pedre/systems/scene/manager.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/scene/manager.py)
- Base class: [src/pedre/systems/scene/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/scene/base.py)
- Events: [src/pedre/systems/scene/events.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/scene/events.py)
- Actions: [src/pedre/systems/scene/actions.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/scene/actions.py)

## Configuration

The SceneManager uses the following settings from `pedre.conf.settings`:

### Scene Transition Settings

- `SCENE_TRANSITION_ALPHA` - Starting alpha value for transitions (default: 0.0)
- `SCENE_TRANSITION_SPEED` - Speed of fade in/out transitions (default: 3.0)
- `SCENE_MAPS_FOLDER` - Folder containing .tmx map files (default: "maps")
- `SCENE_TILEMAP_SCALING` - Scaling factor for tile maps (default: 1.0)
- `SCENE_COLLISION_LAYER_NAMES` - List of layer names used for collision detection (default: ["Walls", "Collision", "Objects", "Buildings"])

These can be overridden in your project's `settings.py`:

```python
# Custom scene settings
SCENE_TRANSITION_SPEED = 5.0  # Faster transitions
SCENE_MAPS_FOLDER = "levels"  # Different folder
SCENE_TILEMAP_SCALING = 2.0  # Scale up tiles
SCENE_COLLISION_LAYER_NAMES = ["Walls", "Collision"]  # Only specific layers
```

## Public API

### Scene Information

#### get_current_scene

`get_current_scene() -> str`

Get the name of the current scene.

**Returns:**

- Current scene name (map filename without .tmx extension, lowercase)

**Example:**

```python
current_scene = context.scene_manager.get_current_scene()
print(f"Player is in: {current_scene}")  # e.g., "village"
```

**Notes:**

- Scene name is derived from map filename
- Automatically converted to lowercase
- Used for scene-specific script triggers and dialog

#### get_current_map

`get_current_map() -> str`

Get the filename of the currently loaded map.

**Returns:**

- Current map filename (e.g., "village.tmx")

**Example:**

```python
current_map = context.scene_manager.get_current_map()
print(f"Loaded map: {current_map}")  # e.g., "village.tmx"
```

#### get_transition_state

`get_transition_state() -> TransitionState`

Get the current transition state.

**Returns:**

- TransitionState enum value (NONE, FADING_OUT, LOADING, FADING_IN)

**Example:**

```python
from pedre.systems.scene.base import TransitionState

state = context.scene_manager.get_transition_state()
if state == TransitionState.NONE:
    print("No transition in progress")
elif state == TransitionState.FADING_OUT:
    print("Fading out current scene")
```

**Notes:**

- NONE - No transition happening
- FADING_OUT - Screen fading to black
- LOADING - Map being loaded (internal state)
- FADING_IN - Screen fading back in

### Scene Loading and Transitions

#### load_level

`load_level(map_file: str, *, initial: bool = False) -> None`

Load a new map level immediately without visual transition.

**Parameters:**

- `map_file` - Filename of the .tmx map to load (e.g., "village.tmx")
- `initial` - If True, skips caching current scene (use for first load)

**Example:**

```python
# Load the initial map when game starts
scene_manager.load_level("start.tmx", initial=True)

# Load a different map directly
scene_manager.load_level("forest.tmx")
```

**Notes:**

- In most cases, use `request_transition()` for smooth visual transitions
- This method loads immediately without fade effects
- Caches current scene state before loading (unless initial=True)
- Orchestrates all system updates in proper order:
  1. Cache current scene state
  2. Load Tiled map
  3. Extract collision layers
  4. Load system data from Tiled (waypoints, portals, NPCs, etc.)
  5. Apply entity states from save data
  6. Load NPC dialogs and scripts
  7. Restore cached scene state
  8. Publish SceneStartEvent

#### request_transition

`request_transition(map_file: str, spawn_waypoint: str | None = None) -> None`

Request a smooth visual transition to a new map (fade out → load → fade in).

**Parameters:**

- `map_file` - Filename of the .tmx map to load
- `spawn_waypoint` - Optional waypoint name to spawn the player at

**Example:**

```python
# Transition to forest map at default spawn
scene_manager.request_transition("forest.tmx")

# Transition to castle at specific entrance
scene_manager.request_transition("castle.tmx", "main_gate")
```

**Notes:**

- Preferred method for map transitions (provides smooth visual feedback)
- Initiates transition state machine (FADING_OUT → LOADING → FADING_IN)
- If transition already in progress, logs warning and ignores request
- Actual map loading happens during LOADING state while screen is black
- Spawn waypoint is applied after map loads

### Collision Management

#### get_wall_list

`get_wall_list() -> arcade.SpriteList | None`

Get the collision wall sprite list.

**Returns:**

- SpriteList containing all collision sprites, or None if no map loaded

**Example:**

```python
wall_list = context.scene_manager.get_wall_list()
if wall_list:
    print(f"Collision sprites: {len(wall_list)}")
```

**Notes:**

- Contains sprites from all layers listed in `SCENE_COLLISION_LAYER_NAMES`
- Used by PhysicsManager for collision detection
- Includes static map tiles and dynamic entities (NPCs, objects)

#### add_to_wall_list

`add_to_wall_list(sprite: arcade.Sprite) -> None`

Add a sprite to the collision wall list.

**Parameters:**

- `sprite` - The sprite to add to collision detection

**Example:**

```python
# Add a revealed NPC to collision
scene_manager.add_to_wall_list(npc_sprite)
```

**Notes:**

- Used when revealing NPCs or spawning dynamic obstacles
- Sprite will block player movement after being added

#### remove_from_wall_list

`remove_from_wall_list(sprite: arcade.Sprite) -> None`

Remove a sprite from the collision wall list.

**Parameters:**

- `sprite` - The sprite to remove from collision detection

**Example:**

```python
# Remove a disappeared NPC from collision
scene_manager.remove_from_wall_list(npc_sprite)
```

**Notes:**

- Used when hiding NPCs or removing dynamic obstacles
- Sprite will no longer block player movement

### Spawn Waypoints

#### get_next_spawn_waypoint

`get_next_spawn_waypoint() -> str`

Get the waypoint name where the player should spawn.

**Returns:**

- Waypoint name, or empty string if default spawn should be used

**Example:**

```python
waypoint = context.scene_manager.get_next_spawn_waypoint()
if waypoint:
    print(f"Spawn at waypoint: {waypoint}")
else:
    print("Using default spawn point")
```

**Notes:**

- Set by `request_transition()` when spawn_waypoint parameter is provided
- Cleared after player is spawned
- PlayerManager checks this during scene load

#### clear_next_spawn_waypoint

`clear_next_spawn_waypoint() -> None`

Clear the next spawn waypoint.

**Example:**

```python
# After spawning player
scene_manager.clear_next_spawn_waypoint()
```

**Notes:**

- Called automatically by PlayerManager after spawning
- Ensures spawn waypoint only applies once

### Rendering

#### on_draw

`on_draw() -> None`

Draw the map scene and transition overlay.

**Notes:**

- Called automatically by game view each frame
- Draws the arcade.Scene containing all map layers
- Draws transition overlay if transition in progress

#### draw_overlay

`draw_overlay() -> None`

Draw the transition overlay (black fade) on top of the screen.

**Notes:**

- Called from UI drawing phase by game view
- Only draws if transition state is not NONE
- Uses transition_alpha to control fade opacity

### System Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the scene system with game context.

**Parameters:**

- `context` - Game context providing access to other systems

**Notes:**

- Called automatically by SystemLoader
- Stores reference to game context

#### reset

`reset() -> None`

Reset scene manager state for new game.

**Notes:**

- Clears current scene and map
- Resets transition state
- Clears wall list
- Called when starting a new game

#### update

`update(delta_time: float) -> None`

Update transition state machine.

**Parameters:**

- `delta_time` - Time since last update in seconds

**Notes:**

- Called automatically by SystemLoader each frame
- Manages transition state machine progression
- Handles fade in/out alpha updates
- Triggers map loading during LOADING state

### Save/Load Support

#### get_save_state

`get_save_state() -> dict[str, Any]`

Return serializable state for saving.

**Returns:**

- Dictionary containing current map filename

**Example:**

```python
save_data = {
    "scene": scene_manager.get_save_state(),
    "player": player_manager.get_save_state(),
    # ... other save data
}
```

**Notes:**

- Only saves current_map filename
- Other scene state (entities, positions) saved by individual systems

#### restore_save_state

`restore_save_state(state: dict[str, Any]) -> None`

Restore saved scene state.

**Parameters:**

- `state` - Dictionary containing saved scene state

**Example:**

```python
scene_manager.restore_save_state(save_data["scene"])
```

**Notes:**

- Restores current_map filename
- Actual map loading happens through load_level()

## Map Loading Process

The SceneManager orchestrates a complex loading sequence to ensure all systems are updated correctly:

### 1. Cache Current Scene

Before loading a new map, the current scene state is cached:

```python
cache_manager.cache_scene(current_scene)
```

This preserves:

- NPC positions, visibility, and dialog levels
- Interactive object states
- Portal states
- Any other system-specific scene state

### 2. Load Tiled Map

The .tmx map file is loaded from the maps folder:

```python
map_path = asset_path(f"{SCENE_MAPS_FOLDER}/{map_file}", ASSETS_HANDLE)
tile_map = arcade.load_tilemap(map_path, scaling=SCENE_TILEMAP_SCALING)
arcade_scene = arcade.Scene.from_tilemap(tile_map)
```

### 3. Extract Collision Layers

Collision sprites are extracted from configured layer names:

```python
for layer_name in SCENE_COLLISION_LAYER_NAMES:
    if layer_name in arcade_scene:
        for sprite in arcade_scene[layer_name]:
            wall_list.append(sprite)
```

### 4. Load System Data from Tiled

Each system's `load_from_tiled()` method is called in dependency order:

- WaypointManager - Extracts waypoint positions
- PortalManager - Extracts portal trigger zones
- InteractionManager - Extracts interactive objects
- PlayerManager - Spawns player at waypoint or default position
- NPCManager - Spawns NPCs from object layer
- CameraManager - Initializes camera position

### 5. Apply Entity States

SaveManager applies any pending entity states from save data:

```python
save_manager.apply_entity_states()
```

This restores:

- NPC positions and visibility
- Player position and state
- Interactive object states

### 6. Load Dialogs

Scene-specific dialogs are loaded:

```python
npc_manager.load_scene_dialogs(current_scene)
```

Note: Scripts are loaded globally at system initialization, not per-scene. The `scene` field in script definitions controls which scene each script can execute in.

### 7. Restore Cached State

If returning to a previously visited scene, cached state is restored:

```python
cache_manager.restore_scene(current_scene)
```

This overrides entity states with the cached version, preserving:

- NPC movements since last visit
- Dialog progression
- Object interaction states

### 8. Sync Collision with Visibility

NPC visibility is synced with collision wall list:

```python
for npc_state in npc_manager.get_npcs().values():
    if not npc_state.sprite.visible and npc_state.sprite in wall_list:
        wall_list.remove(npc_state.sprite)
    elif npc_state.sprite.visible and npc_state.sprite not in wall_list:
        wall_list.append(npc_state.sprite)
```

### 9. Publish SceneStartEvent

Finally, SceneStartEvent is published to trigger scene-specific scripts:

```python
event_bus.publish(SceneStartEvent(current_scene))
```

## Transition State Machine

The SceneManager implements a state machine for smooth scene transitions:

```text
NONE (idle)
  ↓ request_transition()
FADING_OUT (alpha increasing 0.0 → 1.0)
  ↓ when alpha >= 1.0
LOADING (screen fully black, load map)
  ↓ immediate
FADING_IN (alpha decreasing 1.0 → 0.0)
  ↓ when alpha <= 0.0
NONE (idle)
```

### Transition Timing

- **FADING_OUT duration:** `1.0 / SCENE_TRANSITION_SPEED` seconds
- **LOADING duration:** Instant (single frame)
- **FADING_IN duration:** `1.0 / SCENE_TRANSITION_SPEED` seconds
- **Total duration:** `2.0 / SCENE_TRANSITION_SPEED` seconds

Example with default settings (SCENE_TRANSITION_SPEED = 3.0):

- Fade out: ~0.33 seconds
- Loading: instant
- Fade in: ~0.33 seconds
- **Total: ~0.67 seconds**

## Tiled Map Integration

### Map File Structure

Scene maps are .tmx files created in Tiled Map Editor:

```text
assets/
  maps/
    village.tmx
    forest.tmx
    castle.tmx
```

### Required Layers

**Tile Layers:**

- Background/ground layers (visual only)
- At least one collision layer matching `SCENE_COLLISION_LAYER_NAMES`

**Object Layers:**

- "Waypoints" - Spawn points and path targets
- "Portals" - Scene transition triggers
- "Interactions" - Interactive objects
- "NPCs" - Non-player characters

### Collision Layer Setup

Layers used for collision must be named according to `SCENE_COLLISION_LAYER_NAMES`:

```python
# Default collision layer names
SCENE_COLLISION_LAYER_NAMES = ["Walls", "Collision", "Objects", "Buildings"]
```

In Tiled:

1. Create a tile layer named "Walls" or "Collision"
2. Paint tiles where player should not pass
3. Tiles are automatically added to collision detection

### Multi-Layer Collision

You can use multiple layers for organization:

- "Walls" - Interior walls and boundaries
- "Buildings" - Exterior structures
- "Objects" - Decorative obstacles (trees, rocks)

All layers are combined into a single wall_list for collision detection.

## Scene Caching

The SceneManager works with CacheManager to preserve scene state across transitions:

### What Gets Cached

When leaving a scene:

- NPC positions, visibility, dialog levels
- Interactive object states
- Portal states
- Any custom system state

### When Caching Happens

```python
# Before loading new scene
cache_manager.cache_scene(current_scene)
```

### When Cache is Restored

```python
# After loading map and systems
cache_manager.restore_scene(current_scene)
```

### Cache vs Save

- **Cache:** Temporary state for scene transitions (in memory)
- **Save:** Persistent state for game saves (serialized to disk)

When loading a saved game:

1. Save state is restored first (provides base state)
2. If returning to a cached scene, cache overrides save state

## Events

### SceneStartEvent

Published when a new scene/map finishes loading.

**Attributes:**

- `scene_name: str` - Name of the scene that started (e.g., "village", "forest")

**Script Trigger Example:**

```json
{
    "trigger": {
        "event": "scene_start",
        "scene": "village"
    },
    "actions": [
        {"type": "dialog", "speaker": "Narrator", "text": ["Welcome to the village!"]},
        {"type": "play_music", "file": "village_theme.ogg"}
    ]
}
```

**Notes:**

- Fires after all systems are loaded and initialized
- Fires on every map transition and when starting new game
- The `scene` filter is optional (omit to trigger for any scene)
- Useful for:
  - Scene-specific music
  - Opening cutscenes
  - Tutorial messages
  - Quest state checks

**Timing:**

SceneStartEvent fires at the end of `load_level()`, after:

1. Map loaded
2. Systems initialized from Tiled
3. Entity states applied
4. Cached state restored
5. Collision synced

## Actions

### ChangeSceneAction

Transition to a different map/scene with fade effects.

**Type:** `change_scene`

**Parameters:**

- `target_map: str` - Filename of the map to load (e.g., "forest.tmx")
- `spawn_waypoint: str | None` - Optional waypoint name for player spawn

**Example:**

```json
{
    "type": "change_scene",
    "target_map": "forest.tmx",
    "spawn_waypoint": "village_entrance"
}
```

**Notes:**

- Triggers smooth transition through SceneManager.request_transition()
- Screen fades out, loads map, fades back in
- If spawn_waypoint not specified, uses map's default spawn
- Commonly used with portal_entered or dialog_closed events

**Use Cases:**

- Portal transitions with conditions
- Cutscene-driven scene changes
- Quest-triggered map transitions
- Conditional access to areas

**Example with Dialog:**

```json
{
    "portal_to_forest": {
        "scene": "village",
        "trigger": {
            "event": "portal_entered",
            "portal": "forest_gate"
        },
        "conditions": [
            {"check": "npc_interacted", "npc": "guard"}
        ],
        "actions": [
            {
                "type": "dialog",
                "speaker": "Narrator",
                "text": ["The guard waves you through..."]
            },
            {"type": "wait_for_dialog_close"},
            {
                "type": "change_scene",
                "target_map": "forest.tmx",
                "spawn_waypoint": "entrance"
            }
        ]
    }
}
```

## Usage Examples

### Basic Scene Transition

```python
# In a portal script or cutscene
context.scene_manager.request_transition("castle.tmx", "main_entrance")
```

### Conditional Portal

```json
{
    "castle_portal": {
        "scene": "village",
        "trigger": {
            "event": "portal_entered",
            "portal": "castle_gate"
        },
        "conditions": [
            {"check": "inventory_has_item", "item_id": "royal_seal"}
        ],
        "actions": [
            {
                "type": "change_scene",
                "target_map": "castle.tmx",
                "spawn_waypoint": "courtyard"
            }
        ]
    }
}
```

### Scene-Specific Initialization

```json
{
    "forest_intro": {
        "scene": "forest",
        "trigger": {
            "event": "scene_start"
        },
        "actions": [
            {"type": "play_music", "file": "forest_ambience.ogg"},
            {"type": "dialog", "speaker": "Narrator", "text": ["The forest is dark and mysterious..."]},
            {"type": "wait_for_dialog_close"},
            {"type": "reveal_npcs", "npcs": ["forest_spirit"]}
        ]
    }
}
```

### Multi-Scene Quest

```json
{
    "quest_village_complete": {
        "scene": "village",
        "trigger": {
            "event": "npc_interacted",
            "npc": "elder"
        },
        "conditions": [
            {"check": "quest_complete", "quest": "gather_herbs"}
        ],
        "actions": [
            {"type": "dialog", "speaker": "Elder", "text": ["You've done well. Now travel to the temple."]},
            {"type": "wait_for_dialog_close"},
            {"type": "set_quest_state", "quest": "visit_temple", "state": "active"},
            {"type": "change_scene", "target_map": "temple.tmx", "spawn_waypoint": "entrance"}
        ]
    }
}
```

### Dynamic Collision

```python
# Add an obstacle to block a path
boulder = arcade.Sprite("boulder.png", center_x=320, center_y=240)
context.scene_manager.add_to_wall_list(boulder)

# Later, remove it when player solves puzzle
context.scene_manager.remove_from_wall_list(boulder)
boulder.remove_from_sprite_lists()
```

### Check Transition State

```python
from pedre.systems.scene.base import TransitionState

# Disable pause during transitions
state = context.scene_manager.get_transition_state()
if state != TransitionState.NONE:
    print("Cannot pause during scene transition")
    return
```

## Integration with Other Systems

### CacheManager Integration

The CacheManager preserves scene state during transitions:

```python
# Before loading new scene
cache_manager.cache_scene(current_scene)

# After loading, restore cached state
cache_manager.restore_scene(current_scene)
```

**Notes:**

- Cache is transparent to SceneManager
- SceneManager calls CacheManager at appropriate times
- Preserves NPC positions, dialog levels, object states
- Cache is in-memory, separate from save files

### WaypointManager Integration

Waypoints are loaded and used for player spawning:

```python
# SceneManager loads waypoints from Tiled
waypoint_manager.load_from_tiled(tile_map, arcade_scene)

# PlayerManager uses waypoints for spawning
spawn_waypoint = scene_manager.get_next_spawn_waypoint()
if spawn_waypoint:
    waypoint_pos = waypoint_manager.get_waypoint(spawn_waypoint)
```

**Notes:**

- Waypoints loaded during map loading sequence
- Spawn waypoint set via `request_transition()`
- Cleared after player spawns

### PortalManager Integration

Portals are loaded from Tiled during scene setup:

```python
# SceneManager orchestrates portal loading
portal_manager.load_from_tiled(tile_map, arcade_scene)
```

**Notes:**

- Portals loaded from "Portals" object layer
- Portal events trigger scene transitions
- SceneManager handles the actual transition via `request_transition()`

### NPCManager Integration

NPCs are loaded and managed during scene transitions:

```python
# Load NPCs from Tiled
npc_manager.load_from_tiled(tile_map, arcade_scene)

# Load scene-specific dialogs
npc_manager.load_scene_dialogs(current_scene)
```

**Notes:**

- NPCs loaded from "NPCs" object layer
- Dialog files loaded per-scene
- NPC visibility synced with collision list

### PlayerManager Integration

Player is spawned at correct location during scene load:

```python
# PlayerManager loads player from Tiled
player_manager.load_from_tiled(tile_map, arcade_scene)

# Uses spawn waypoint if set
spawn_waypoint = scene_manager.get_next_spawn_waypoint()
```

**Notes:**

- Player loaded during map loading sequence
- Spawn waypoint overrides default position
- Player position restored from save data after load

### PhysicsManager Integration

Physics engine uses collision layers from scene:

```python
# SceneManager provides wall list
wall_list = scene_manager.get_wall_list()

# PhysicsManager creates engine with walls
physics_manager.invalidate()
```

**Notes:**

- Wall list extracted from collision layers
- Physics engine invalidated after scene load
- Dynamic sprites added/removed from wall list

### SaveManager Integration

Scene state is saved and restored:

```python
# Save current map filename
save_state = scene_manager.get_save_state()

# Restore and load saved map
scene_manager.restore_save_state(save_state)
scene_manager.load_level(save_state["current_map"])
```

**Notes:**

- Only map filename saved by SceneManager
- Entity states saved by individual systems
- Scene loading orchestrated by SceneManager

### ScriptManager Integration

Scripts are triggered by scene events:

```python
# SceneStartEvent published after scene loads
event_bus.publish(SceneStartEvent(current_scene))

# Scripts filter by scene
{
    "scene": "village",
    "trigger": {"event": "scene_start"},
    "actions": [...]
}
```

**Notes:**

- Scripts loaded globally at startup
- Scene field controls which scene script executes in
- SceneStartEvent triggers scene-specific initialization

## Troubleshooting

### Map Not Loading

If scenes fail to load:

1. **Check map path** - Verify .tmx file exists in `SCENE_MAPS_FOLDER`
2. **Verify file name** - Ensure filename matches exactly (case-sensitive)
3. **Review Tiled map** - Open .tmx in Tiled to check for errors
4. **Check logs** - Look for file not found or parsing errors
5. **Verify scaling** - Check `SCENE_TILEMAP_SCALING` is appropriate

### Collision Not Working

If player passes through walls:

1. **Check layer names** - Ensure collision layers match `SCENE_COLLISION_LAYER_NAMES`
2. **Verify wall list** - Check `get_wall_list()` contains sprites
3. **Review Tiled layers** - Ensure collision tiles are painted
4. **Check physics** - Verify PhysicsManager is using wall list
5. **Test visibility sync** - Ensure invisible NPCs removed from walls

### Transition Stuck

If transitions freeze or don't complete:

1. **Check transition state** - Use `get_transition_state()` to debug
2. **Review logs** - Look for errors during LOADING state
3. **Verify map exists** - Ensure target map file is valid
4. **Check transition speed** - Increase `SCENE_TRANSITION_SPEED` if too slow
5. **Test directly** - Use `load_level()` to bypass transition

### Wrong Spawn Location

If player spawns at incorrect position:

1. **Check waypoint** - Verify `spawn_waypoint` exists in target scene
2. **Review Player layer** - Check default spawn position in Tiled
3. **Verify spawn_at_portal** - Ensure player properties allow waypoint spawn
4. **Check waypoint manager** - Test `get_waypoint()` returns correct position
5. **Review logs** - Look for waypoint resolution warnings

### Scene State Not Persisting

If scene changes aren't remembered:

1. **Check caching** - Verify CacheManager is enabled and working
2. **Review cache calls** - Ensure `cache_scene()` called before transition
3. **Test restore** - Check `restore_scene()` called after loading
4. **Verify system support** - Ensure systems implement `cache_scene_state()`
5. **Check save/load** - Test that cache survives save/load cycle

### Objects Not Loading

If waypoints, portals, or NPCs don't appear:

1. **Check object layers** - Verify "Waypoints", "Portals", "NPCs" layers exist
2. **Review properties** - Ensure objects have required custom properties
3. **Check load order** - Verify systems' `load_from_tiled()` called in correct order
4. **Test individually** - Load map and check each object layer
5. **Review logs** - Look for parsing or validation errors

### Performance Issues

If scene transitions are slow:

1. **Reduce tile count** - Simplify maps or use larger tiles
2. **Optimize collision** - Use fewer collision sprites
3. **Increase speed** - Adjust `SCENE_TRANSITION_SPEED` for faster fades
4. **Profile loading** - Identify slow systems in load sequence
5. **Lazy load assets** - Load textures on demand rather than all at once

## Custom Scene Implementation

If you need to replace the scene system with a custom implementation, you can extend the `SceneBaseManager` abstract base class.

### SceneBaseManager

**Location:** [src/pedre/systems/scene/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/scene/base.py)

The `SceneBaseManager` class defines the minimum interface that any scene manager must implement.

#### Required Methods

Your custom scene manager must implement these abstract methods:

```python
from pedre.systems.scene.base import SceneBaseManager, TransitionState

class CustomSceneManager(SceneBaseManager):
    """Custom scene implementation."""

    name = "scene"
    dependencies = ["cache", "waypoint", "npc", "portal", "interaction", "player", "script"]

    def get_current_scene(self) -> str:
        """Get current scene name."""
        ...

    def get_next_spawn_waypoint(self) -> str:
        """Get next spawn waypoint."""
        ...

    def clear_next_spawn_waypoint(self) -> None:
        """Clear next spawn waypoint."""
        ...

    def get_wall_list(self) -> arcade.SpriteList | None:
        """Get collision wall list."""
        ...

    def remove_from_wall_list(self, sprite: arcade.Sprite) -> None:
        """Remove sprite from collision."""
        ...

    def add_to_wall_list(self, sprite: arcade.Sprite) -> None:
        """Add sprite to collision."""
        ...

    def load_level(self, map_file: str, *, initial: bool = False) -> None:
        """Load a new map level."""
        ...

    def get_transition_state(self) -> TransitionState:
        """Get current transition state."""
        ...

    def get_current_map(self) -> str:
        """Get current map filename."""
        ...

    def request_transition(self, map_file: str, spawn_waypoint: str | None = None) -> None:
        """Request scene transition."""
        ...
```

#### Registration

Register your custom scene manager using the `@SystemRegistry.register` decorator:

```python
from pedre.systems.registry import SystemRegistry
from pedre.systems.scene.base import SceneBaseManager

@SystemRegistry.register
class CustomSceneManager(SceneBaseManager):
    name = "scene"
    dependencies = ["cache"]

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom manager inherits from `BaseSystem` (via `SceneBaseManager`), so you must implement the standard system lifecycle methods: `setup()`, `reset()`, and optionally `update()` and `on_draw()`
- The `role` attribute is set to `"scene_manager"` in the base class
- Your implementation can use any map format or transition system
- Register your custom scene manager in your project's `INSTALLED_SYSTEMS` setting before the default `"pedre.systems.scene"` to replace it

**Example Custom Implementation:**

```python
# In myproject/systems/custom_scene.py
from pedre.systems.registry import SystemRegistry
from pedre.systems.scene.base import SceneBaseManager, TransitionState

@SystemRegistry.register
class ProceduralSceneManager(SceneBaseManager):
    """Scene manager that generates maps procedurally."""

    name = "scene"
    dependencies = []

    def __init__(self):
        self.current_scene = "procedural_0"
        self.wall_list = arcade.SpriteList()
        # ... rest of initialization ...

    def load_level(self, map_file: str, *, initial: bool = False) -> None:
        # Generate procedural map instead of loading .tmx
        self._generate_procedural_map(map_file)

    # ... implement other abstract methods ...
```

```python
# In myproject/settings.py
INSTALLED_SYSTEMS = [
    "myproject.systems.custom_scene",  # Load custom scene first
    "pedre.systems.camera",
    "pedre.systems.audio",
    # ... rest of systems (omit "pedre.systems.scene") ...
]
```

## See Also

- [CacheManager](cache.md) - Scene state caching
- [WaypointManager](waypoint.md) - Spawn points and pathfinding targets
- [PortalManager](portal.md) - Scene transition triggers
- [NPCManager](npc.md) - NPC loading and management
- [PlayerManager](player.md) - Player spawning and control
- [PhysicsManager](physics.md) - Collision detection
- [Configuration Guide](../guides/configuration.md)
- [Scripting Actions](../scripting/actions.md)
- [Scripting Events](../scripting/events.md)
