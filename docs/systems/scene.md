# SceneManager

Manages scene transitions, map loading, and lifecycle.

## Location

`src/pedre/systems/scene/manager.py`

## Initialization

```python
from pedre.systems.scene import SceneManager

scene_manager = SceneManager()
# SceneManager is typically initialized by SystemLoader
```

## Key Methods

### `load_level(map_file: str, spawn_waypoint: str | None, context: GameContext) -> None`

Immediately loads a new map level. In most cases, you should use `request_transition` for a smooth visual transition.

**Parameters:**

- `map_file` - Filename of the .tmx map to load (e.g. "village.tmx")
- `spawn_waypoint` - Optional waypoint name to spawn the player at
- `context` - The GameContext

### `request_transition(map_file: str, spawn_waypoint: str | None = None) -> None`

Requests a smooth visual transition (fade out -> load -> fade in) to a new map.

**Parameters:**

- `map_file` - Filename of the .tmx map to load
- `spawn_waypoint` - Optional waypoint name to spawn the player at

**Example:**

```python
# Transition to the forest map, spawning at the "village_entrance" waypoint
scene_manager.request_transition("forest.tmx", "village_entrance")
```

### `draw_overlay() -> None`

Draws the transition overlay (black fade) on top of the screen. This is typically called by the main game loop during the UI drawing phase.

## Transition States

The SceneManager handles the following transition states:

- `NONE` - No transition in progress
- `FADING_OUT` - Screen fading to black
- `LOADING` - Map is being loaded (hidden)
- `FADING_IN` - Screen fading back in
