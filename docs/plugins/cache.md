# CacheManager

Manages scene state cache to preserve system states when the player transitions between scenes.

## Location

- Implementation: [src/pedre/systems/cache/manager.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/cache/manager.py)
- Base class: [src/pedre/systems/cache/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/cache/base.py)

## Overview

The CacheManager is a central system that manages in-memory state preservation across scene transitions. When a player leaves a scene, the CacheManager collects and stores the state of all systems for that scene. When the player returns to the scene, the CacheManager restores those states, allowing NPCs, objects, and other systems to resume from where they left off.

This system works by calling `cache_scene_state()` and `restore_scene_state()` on all registered systems, making scene transitions seamless while preserving game state.

## Configuration

The CacheManager itself has no configuration settings. It operates automatically by coordinating with other systems through the `BaseSystem` interface.

## Public API

### Scene Caching

#### cache_scene

`cache_scene(scene_name: str) -> None`

Cache all system states for a scene when the player is leaving.

**Parameters:**

- `scene_name` - Name of the scene being left

**Example:**

```python
# Typically called automatically during scene transitions
cache_manager.cache_scene("village")
```

**Notes:**

- Iterates through all systems in the game context
- Calls `cache_scene_state(scene_name)` on each system
- Only stores non-empty state dictionaries
- Automatically called by SceneManager during transitions

#### restore_scene

`restore_scene(scene_name: str) -> bool`

Restore cached system states for a scene when the player is returning.

**Parameters:**

- `scene_name` - Name of the scene being entered

**Returns:**

- `True` if cached state was found and restored, `False` if no cache exists

**Example:**

```python
# Typically called automatically during scene transitions
restored = cache_manager.restore_scene("village")
if restored:
    print("Scene state restored from cache")
else:
    print("No cached state, loading fresh scene")
```

**Notes:**

- Iterates through all systems in the game context
- Calls `restore_scene_state(scene_name, state)` on each system with cached state
- Returns `False` if scene has never been cached before
- Automatically called by SceneManager during transitions

#### has_cached_state

`has_cached_state(scene_name: str) -> bool`

Check if a scene has cached state.

**Parameters:**

- `scene_name` - Name of the scene to check

**Returns:**

- `True` if cached state exists for the scene

**Example:**

```python
if cache_manager.has_cached_state("village"):
    print("Village scene has been visited before")
else:
    print("First time visiting village")
```

**Notes:**

- Useful for checking if a scene has been previously visited
- Returns `False` for scenes that have never been cached
- Does not validate the contents of cached state

#### clear

`clear() -> None`

Clear all cached state.

**Example:**

```python
# Clear all cached scene data when starting a new game
cache_manager.clear()
```

**Notes:**

- Removes cached state for all scenes
- Called automatically when starting a new game via `reset()`
- Use when you want to reset scene states to initial conditions

### Save/Load Support

#### get_save_state

`get_save_state() -> dict[str, Any]`

Return serializable state for saving.

**Returns:**

- Dictionary mapping scene names to their cached system states

**Example:**

```python
save_data = {
    "player_position": (x, y),
    "cache": cache_manager.get_save_state(),
    # ... other save data
}
```

**Notes:**

- Returns a shallow copy of the cache
- Includes all cached scene states
- Compatible with JSON serialization

#### restore_save_state

`restore_save_state(state: dict[str, Any]) -> None`

Restore cache state from save file data.

**Parameters:**

- `state` - Previously serialized cache state from `get_save_state()`

**Example:**

```python
cache_manager.restore_save_state(save_data["cache"])
```

**Notes:**

- Replaces current cache with saved state
- Restores all previously cached scenes
- Called automatically by SaveManager when loading a game

### System Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the cache system with game context.

**Parameters:**

- `context` - Game context providing access to other systems

**Notes:**

- Called automatically by SystemLoader
- Stores reference to game context

#### reset

`reset() -> None`

Reset cache for new game.

**Notes:**

- Clears all cached scene state
- Called when starting a new game
- Equivalent to calling `clear()`

## How Systems Participate in Caching

### System Requirements

For a system to participate in scene caching, it must implement two methods from the `BaseSystem` interface:

```python
def cache_scene_state(self, scene_name: str) -> dict[str, Any]:
    """Return state to cache when leaving a scene.

    Args:
        scene_name: Name of the scene being cached.

    Returns:
        Dictionary containing state to preserve, or empty dict if nothing to cache.
    """
    # Return state specific to this scene
    return {}

def restore_scene_state(self, scene_name: str, state: dict[str, Any]) -> None:
    """Restore cached state when returning to a scene.

    Args:
        scene_name: Name of the scene being restored.
        state: Previously cached state for this scene.
    """
    # Restore the cached state
    pass
```

### Example: NPC System Caching

The NPCManager caches NPC positions, visibility, and dialog levels:

```python
def cache_scene_state(self, scene_name: str) -> dict[str, Any]:
    """Cache NPC entity state for scene transitions."""
    npc_states = {}
    for npc_name, npc in self._npcs.items():
        npc_states[npc_name] = {
            "position": (npc.sprite.center_x, npc.sprite.center_y),
            "visible": npc.sprite.visible,
            "dialog_level": npc.dialog_level,
            # ... other state
        }
    return {"npcs": npc_states}

def restore_scene_state(self, scene_name: str, state: dict[str, Any]) -> None:
    """Restore NPC entity state after scene transition."""
    npc_states = state.get("npcs", {})
    for npc_name, npc_state in npc_states.items():
        npc = self.get_npc_by_name(npc_name)
        if npc:
            x, y = npc_state["position"]
            npc.sprite.center_x = x
            npc.sprite.center_y = y
            npc.sprite.visible = npc_state["visible"]
            npc.dialog_level = npc_state["dialog_level"]
```

### Cache vs Save State

The cache system differs from the save system:

**Cache System:**

- **Purpose**: Preserve scene state during session
- **Scope**: Per-scene state (NPC positions, object states in specific scenes)
- **Lifetime**: Current game session only
- **Called by**: SceneManager during scene transitions
- **Methods**: `cache_scene_state()` / `restore_scene_state()`

**Save System:**

- **Purpose**: Persist game state across sessions
- **Scope**: Global game state (inventory, flags, story progress)
- **Lifetime**: Persists to disk, survives game restarts
- **Called by**: SaveManager during save/load
- **Methods**: `get_save_state()` / `restore_save_state()` / `apply_entity_state()`

**Example Distinction:**

```python
# NPCManager caching (per-scene)
def cache_scene_state(self, scene_name: str) -> dict[str, Any]:
    # Only cache NPC entity state for this specific scene
    return {"npcs": {name: npc_entity_state for name, npc in self._npcs.items()}}

# NPCManager saving (global)
def get_save_state(self) -> dict[str, Any]:
    # Save global state: interaction history, dialog levels across ALL scenes
    return {
        "interaction_history": self._interaction_history,
        "npcs": {name: npc_full_state for name, npc in self._npcs.items()}
    }
```

## Usage Examples

### Basic Scene Transition

The cache system is typically used automatically during scene transitions:

```python
# When leaving a scene
def transition_to_new_scene(old_scene: str, new_scene: str):
    # Cache current scene state
    cache_manager.cache_scene(old_scene, context)

    # Load new scene
    scene_manager.load_level(new_scene)

    # Try to restore cached state if returning to a known scene
    cache_manager.restore_scene(new_scene, context)
```

### Checking First-Time Visit

```python
# Trigger special events on first visit
scene_name = "haunted_house"
if not cache_manager.has_cached_state(scene_name):
    # First time visiting - trigger introduction cutscene
    script_manager.run_script("haunted_house_intro")
```

### Manual Cache Management

```python
# Manually clear cache for specific gameplay reasons
def reset_village():
    """Reset village to initial state."""
    # Clear cached state for village
    cache_manager.clear()

    # Reload the scene fresh
    scene_manager.load_level("village.tmx")
```

### Save Integration

The cache system integrates with the save system to persist scene states:

```python
# During save
def save_game(slot: int):
    save_data = {
        "version": 1,
        "timestamp": time.time(),
        "cache": cache_manager.get_save_state(),  # Includes all scene caches
        # ... other systems
    }
    write_save_file(slot, save_data)

# During load
def load_game(slot: int):
    save_data = read_save_file(slot)
    cache_manager.restore_save_state(save_data["cache"])  # Restores all scene caches
    # ... restore other systems
```

## Custom Cache Implementation

If you need to replace the cache system with a custom implementation, you can extend the `CacheBaseManager` abstract base class.

### CacheBaseManager

**Location:** [src/pedre/systems/cache/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/systems/cache/base.py)

The `CacheBaseManager` class defines the minimum interface that any cache manager must implement.

#### Required Methods

Your custom cache manager must implement these abstract methods:

```python
from pedre.systems.cache.base import CacheBaseManager

class CustomCacheManager(CacheBaseManager):
    """Custom cache implementation."""

    name = "cache"
    dependencies = []

    def cache_scene(self, scene_name: str) -> None:
        """Cache all system states for a scene."""
        ...

    def restore_scene(self, scene_name: str) -> bool:
        """Restore cached system states for a scene."""
        ...
```

#### Registration

Register your custom cache manager using the `@SystemRegistry.register` decorator:

```python
from pedre.systems.registry import SystemRegistry
from pedre.systems.cache.base import CacheBaseManager

@SystemRegistry.register
class DatabaseCacheManager(CacheBaseManager):
    """Cache manager that stores state in a database."""

    name = "cache"
    dependencies = []

    def __init__(self):
        self.db = Database()

    def cache_scene(self, scene_name: str) -> None:
        # Store in database instead of memory
        for system in self.context.get_systems().values():
            state = system.cache_scene_state(scene_name)
            if state:
                self.db.store(scene_name, system.name, state)

    def restore_scene(self, scene_name: str) -> bool:
        # Restore from database
        if not self.db.has_scene(scene_name):
            return False

        for system in self.context.get_systems().values():
            state = self.db.load(scene_name, system.name)
            if state:
                system.restore_scene_state(scene_name, state)
        return True
```

```python
# In myproject/settings.py
INSTALLED_SYSTEMS = [
    "myproject.systems.custom_cache",  # Load custom cache first
    "pedre.systems.scene",
    "pedre.systems.player",
    # ... rest of systems (omit "pedre.systems.cache") ...
]
```

#### Notes on Custom Implementation

- Your custom manager inherits from `BaseSystem` (via `CacheBaseManager`), so you must implement the standard system lifecycle methods: `setup()`, `cleanup()`, and `reset()`
- The `role` attribute is set to `"cache_manager"` in the base class
- Your implementation can use any storage mechanism (database, files, network)
- Register your custom cache manager in your project's `INSTALLED_SYSTEMS` setting before the default `"pedre.systems.cache"` to replace it

## Internal Structure

### Cache Data Structure

The cache is stored as a nested dictionary:

```python
{
    "scene_name": {
        "system_name": {
            # System-specific cached state
        },
        # ... other systems
    },
    # ... other scenes
}
```

### Example Cache State

```python
{
    "village": {
        "npc": {
            "npcs": {
                "merchant": {
                    "position": (320.0, 480.0),
                    "visible": True,
                    "dialog_level": 2
                },
                "guard": {
                    "position": (640.0, 480.0),
                    "visible": True,
                    "dialog_level": 0
                }
            }
        },
        "interaction": {
            "interacted_objects": ["chest_1", "sign_1"]
        }
    },
    "forest": {
        "npc": {
            "npcs": {
                "spirit": {
                    "position": (800.0, 600.0),
                    "visible": False,
                    "dialog_level": 0
                }
            }
        }
    }
}
```

## Best Practices

### What to Cache

**Do cache:**

- NPC positions within a scene
- Object interaction states (doors opened, chests looted)
- Entity visibility states
- Temporary scene-specific flags

**Don't cache:**

- Global game state (inventory, player stats)
- Story progression flags
- Achievement/unlock states
- Audio settings

### Cache Clearing

Cache should be cleared when:

- Starting a new game
- Resetting to checkpoint
- Specific gameplay events require scene reset

Cache should NOT be cleared when:

- Saving the game
- Switching between scenes normally
- Pausing/unpausing

### Performance Considerations

- Cache operations are in-memory and very fast
- Each scene transition involves two cache operations (save old, restore new)
- Cache size grows with number of visited scenes
- Consider clearing cache for distant/old scenes in very large games

## See Also

- [SceneManager](scene.md) - Uses cache during scene transitions
- [SaveManager](save.md) - Persists cache to disk
- [NPCManager](npc.md) - Example system that uses caching
- [Configuration Guide](../guides/configuration.md)
