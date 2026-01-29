# CameraManager

Manages camera movement with smooth following and boundary constraints.

## Location

- Implementation: `src/pedre/systems/camera/manager.py`
- Base class: `src/pedre/systems/camera/base.py`

## Configuration

The CameraManager uses the following settings from `pedre.conf.settings`:

- `CAMERA_LERP_SPEED` - Camera interpolation speed (0.0 to 1.0, default: 0.1)

This can be overridden in your project's `settings.py`:

```python
# Custom camera settings
CAMERA_LERP_SPEED = 0.2  # More responsive camera
```

## Public API

### Camera Following

#### `smooth_follow(target_x: float, target_y: float) -> None`

Smoothly move camera towards target position using linear interpolation.

**Parameters:**

- `target_x` - Target X coordinate in world space (e.g., `player.center_x`)
- `target_y` - Target Y coordinate in world space (e.g., `player.center_y`)

**Example:**

```python
# Follow player with smooth interpolation
camera_manager.smooth_follow(player.center_x, player.center_y)
```

**Notes:**

- Uses lerp speed from `CAMERA_LERP_SPEED` setting
- Automatically applies boundary constraints if enabled
- Call this every frame in your update loop for continuous following

#### `instant_follow(target_x: float, target_y: float) -> None`

Instantly move camera to target position without interpolation.

**Parameters:**

- `target_x` - Target X coordinate in world space
- `target_y` - Target Y coordinate in world space

**Example:**

```python
# Teleport camera to spawn point
camera_manager.instant_follow(spawn_x, spawn_y)
```

**Notes:**

- Useful for scene transitions and initial positioning
- Still respects boundary constraints if enabled

#### `set_follow_player(*, smooth: bool = True) -> None`

Set camera to automatically follow the player sprite.

**Parameters:**

- `smooth` - If `True`, use `smooth_follow()`. If `False`, use `instant_follow()` (default: `True`)

**Example:**

```python
# Enable smooth player following
camera_manager.set_follow_player()

# Enable instant player following (no interpolation)
camera_manager.set_follow_player(smooth=False)
```

**Notes:**

- The camera will automatically track player position every frame
- Called automatically when loading maps with `camera_follow: "player"` property

#### `set_follow_npc(npc_name: str, *, smooth: bool = True) -> None`

Set camera to automatically follow a specific NPC sprite.

**Parameters:**

- `npc_name` - Name of the NPC to follow
- `smooth` - If `True`, use `smooth_follow()`. If `False`, use `instant_follow()` (default: `True`)

**Example:**

```python
# Follow NPC during cutscene
camera_manager.set_follow_npc("boss", smooth=True)
```

**Notes:**

- NPC must exist in the current scene
- Useful for cutscenes and cinematic sequences

#### `stop_follow() -> None`

Stop camera following, keeping it at its current position.

**Example:**

```python
# Static camera for cutscene
camera_manager.stop_follow()
```

**Notes:**

- Camera will remain at its current position until following is re-enabled
- Useful for fixed camera shots

### Boundary Management

#### `set_bounds(map_width: float, map_height: float, viewport_width: float, viewport_height: float) -> None`

Set camera movement boundaries based on map and viewport dimensions.

**Parameters:**

- `map_width` - Total width of the map in pixels (e.g., `tile_map.width * tile_map.tile_width`)
- `map_height` - Total height of the map in pixels (e.g., `tile_map.height * tile_map.tile_height`)
- `viewport_width` - Width of the viewport in pixels (e.g., `window.width`)
- `viewport_height` - Height of the viewport in pixels (e.g., `window.height`)

**Example:**

```python
# Set bounds for a 50x40 tile map (32px tiles) on 1024x768 window
camera_manager.set_bounds(
    map_width=50 * 32,      # 1600 pixels
    map_height=40 * 32,     # 1280 pixels
    viewport_width=1024,
    viewport_height=768
)
```

**Notes:**

- Prevents camera from showing areas outside the map
- Automatically handles small maps (smaller than viewport) by centering them
- Called automatically when loading maps via `load_from_tiled()`

### Rendering

#### `use() -> None`

Activate this camera for rendering world objects.

**Example:**

```python
def on_draw(self):
    self.clear()

    # Activate camera for world rendering
    camera_manager.use()

    # Draw world objects
    self.npc_list.draw()
    self.player_list.draw()
```

**Notes:**

- Must be called before drawing any world objects
- UI elements typically use a separate camera

### Integration Methods

#### `load_from_tiled(tile_map: arcade.TileMap, arcade_scene: arcade.Scene) -> None`

Load camera configuration from a Tiled map and create the camera.

**Parameters:**

- `tile_map` - Loaded TileMap with properties
- `arcade_scene` - Scene created from tile_map (unused)

**Notes:**

- Automatically called by the scene system when loading maps
- Reads camera properties from the map and applies configuration
- Creates the camera with correct initial position and bounds

**Tiled Configuration:**

1. Click on the map name in Layers panel (deselect any layers)
2. Open Properties panel (View → Properties)
3. Add custom properties as needed

**Supported Properties:**

- `camera_follow` (string): `"player"`, `"npc:<name>"`, or `"none"` (default: `"player"`)
- `camera_smooth` (bool): `true` for smooth following, `false` for instant (default: `true`)

**Examples:**

```yaml
camera_follow: "player"           # Follow player (default)
camera_follow: "npc:merchant"     # Follow NPC named merchant
camera_follow: "none"             # Static camera
camera_smooth: false              # Instant following (no interpolation)
```

## Camera Actions

The camera system provides script actions for camera control during cutscenes and gameplay.

### `follow_player`

Make camera follow player sprite continuously.

**Parameters:**

- `smooth` (bool, optional) - Use smooth interpolation (default: `true`)

**Example:**

```json
{
    "type": "follow_player"
}
```

### `follow_npc`

Make camera follow a specific NPC sprite continuously.

**Parameters:**

- `npc` (string, required) - Name of NPC to follow
- `smooth` (bool, optional) - Use smooth interpolation (default: `true`)

**Example:**

```json
{
    "type": "follow_npc",
    "npc": "martin"
}
```

### `stop_camera_follow`

Stop camera following, keep at current position.

**Example:**

```json
{
    "type": "stop_camera_follow"
}
```

### Common Patterns

**Cutscene focusing on NPC:**

```json
[
    {"type": "follow_npc", "npc": "boss"},
    {"type": "dialog", "speaker": "boss", "text": ["You cannot defeat me!"]},
    {"type": "wait_for_dialog_close"},
    {"type": "follow_player"}
]
```

**Static camera shot:**

```json
[
    {"type": "stop_camera_follow"},
    {"type": "dialog", "speaker": "narrator", "text": ["Meanwhile..."]},
    {"type": "wait_for_dialog_close"},
    {"type": "follow_player"}
]
```

## Custom Camera Implementation

If you need to replace the camera system with a custom implementation (e.g., for advanced camera effects or a different camera backend), you can extend the `CameraBaseManager` abstract base class.

### CameraBaseManager

**Location:** `src/pedre/systems/camera/base.py`

The `CameraBaseManager` class defines the minimum interface that any camera manager must implement. All methods are abstract and must be implemented by your custom class.

#### Required Methods

Your custom camera manager must implement these abstract methods:

```python
from pedre.systems.camera.base import CameraBaseManager
import arcade

class CustomCameraManager(CameraBaseManager):
    """Custom camera implementation."""

    name = "camera"
    dependencies = ["player", "npc"]

    def use(self) -> None:
        """Activate this camera for rendering."""
        ...

    def set_follow_player(self, *, smooth: bool = True) -> None:
        """Set camera to follow the player."""
        ...

    def stop_follow(self) -> None:
        """Stop camera following, keeping it at current position."""
        ...

    def set_follow_npc(self, npc_name: str, *, smooth: bool = True) -> None:
        """Set camera to follow a specific NPC."""
        ...
```

#### Registration

Register your custom camera manager using the `@SystemRegistry.register` decorator:

```python
from pedre.systems.registry import SystemRegistry
from pedre.systems.camera.base import CameraBaseManager

@SystemRegistry.register
class CustomCameraManager(CameraBaseManager):
    name = "camera"
    dependencies = ["player", "npc"]

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom manager inherits from `BaseSystem` (via `CameraBaseManager`), so you must implement the standard system lifecycle methods: `setup()`, `cleanup()`, and `update()`
- The `role` attribute is set to `"camera_manager"` in the base class
- Your implementation can use any camera system, not just Arcade's Camera2D
- Additional methods beyond the required interface can be added as needed
- Register your custom camera manager in your project's `INSTALLED_SYSTEMS` setting before the default `"pedre.systems.camera"` to replace it

**Example Custom Implementation:**

```python
# In myproject/systems/custom_camera.py
from pedre.systems.registry import SystemRegistry
from pedre.systems.camera.base import CameraBaseManager

@SystemRegistry.register
class AdvancedCameraManager(CameraBaseManager):
    """Camera with zoom and screen shake effects."""

    name = "camera"
    dependencies = ["player", "npc"]

    def __init__(self):
        self.camera = None
        self.zoom_level = 1.0
        self.shake_intensity = 0.0
        # ... rest of initialization ...

    def use(self) -> None:
        # Custom rendering with zoom and shake
        if self.camera:
            self.apply_zoom()
            self.apply_shake()
            self.camera.use()

    def set_zoom(self, zoom: float) -> None:
        """Custom method for zoom control."""
        self.zoom_level = zoom

    # ... implement other abstract methods ...
```

```python
# In myproject/settings.py
INSTALLED_SYSTEMS = [
    "myproject.systems.custom_camera",  # Load custom camera first
    "pedre.systems.audio",
    "pedre.systems.debug",
    # ... rest of systems (omit "pedre.systems.camera") ...
]
```
