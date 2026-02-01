# CameraPlugin

Manages camera movement with smooth following and boundary constraints.

## Location

- Implementation: [src/pedre/plugins/camera/plugin.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/camera/plugin.py)
- Base class: [src/pedre/plugins/camera/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/camera/base.py)
- Actions: [src/pedre/plugins/camera/actions.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/camera/actions.py)

## Configuration

The CameraPlugin uses the following settings from `pedre.conf.settings`:

### Movement Settings

- `CAMERA_LERP_SPEED` - Camera interpolation speed (0.0 to 1.0, default: `0.1`)

This can be overridden in your project's `settings.py`:

```python
# Custom camera settings
CAMERA_LERP_SPEED = 0.2  # More responsive camera
```

## Public API

### Camera Following

#### smooth_follow

`smooth_follow(target_x: float, target_y: float) -> None`

Smoothly move camera towards target position using linear interpolation.

**Parameters:**

- `target_x` - Target X coordinate in world space (e.g., `player.center_x`)
- `target_y` - Target Y coordinate in world space (e.g., `player.center_y`)

**Example:**

```python
# Follow player with smooth interpolation
camera_plugin.smooth_follow(player.center_x, player.center_y)
```

**Notes:**

- Uses lerp speed from `CAMERA_LERP_SPEED` setting
- Automatically applies boundary constraints if enabled
- Call this every frame in your update loop for continuous following

#### instant_follow

`instant_follow(target_x: float, target_y: float) -> None`

Instantly move camera to target position without interpolation.

**Parameters:**

- `target_x` - Target X coordinate in world space
- `target_y` - Target Y coordinate in world space

**Example:**

```python
# Teleport camera to spawn point
camera_plugin.instant_follow(spawn_x, spawn_y)
```

**Notes:**

- Useful for scene transitions and initial positioning
- Still respects boundary constraints if enabled

#### set_follow_player

`set_follow_player(*, smooth: bool = True) -> None`

Set camera to automatically follow the player sprite.

**Parameters:**

- `smooth` - If `True`, use `smooth_follow()`. If `False`, use `instant_follow()` (default: `True`)

**Example:**

```python
# Enable smooth player following
camera_plugin.set_follow_player()

# Enable instant player following (no interpolation)
camera_plugin.set_follow_player(smooth=False)
```

**Notes:**

- The camera will automatically track player position every frame
- Called automatically when loading maps with `camera_follow: "player"` property

#### set_follow_npc

`set_follow_npc(npc_name: str, *, smooth: bool = True) -> None`

Set camera to automatically follow a specific NPC sprite.

**Parameters:**

- `npc_name` - Name of the NPC to follow
- `smooth` - If `True`, use `smooth_follow()`. If `False`, use `instant_follow()` (default: `True`)

**Example:**

```python
# Follow NPC during cutscene
camera_plugin.set_follow_npc("boss", smooth=True)
```

**Notes:**

- NPC must exist in the current scene
- Useful for cutscenes and cinematic sequences

#### stop_follow

`stop_follow() -> None`

Stop camera following, keeping it at its current position.

**Example:**

```python
# Static camera for cutscene
camera_plugin.stop_follow()
```

**Notes:**

- Camera will remain at its current position until following is re-enabled
- Useful for fixed camera shots

### Boundary Management

#### set_bounds

`set_bounds(map_width: float, map_height: float, viewport_width: float, viewport_height: float) -> None`

Set camera movement boundaries based on map and viewport dimensions.

**Parameters:**

- `map_width` - Total width of the map in pixels (e.g., `tile_map.width * tile_map.tile_width`)
- `map_height` - Total height of the map in pixels (e.g., `tile_map.height * tile_map.tile_height`)
- `viewport_width` - Width of the viewport in pixels (e.g., `window.width`)
- `viewport_height` - Height of the viewport in pixels (e.g., `window.height`)

**Example:**

```python
# Set bounds for a 50x40 tile map (32px tiles) on 1024x768 window
camera_plugin.set_bounds(
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

#### use

`use() -> None`

Activate this camera for rendering world objects.

**Example:**

```python
def on_draw(self):
    self.clear()

    # Activate camera for world rendering
    camera_plugin.use()

    # Draw world objects
    self.npc_list.draw()
    self.player_list.draw()
```

**Notes:**

- Must be called before drawing any world objects
- UI elements typically use a separate camera

#### set_camera

`set_camera(camera: arcade.camera.Camera2D) -> None`

Set the camera to manage.

**Parameters:**

- `camera` - The arcade Camera2D to manage

**Notes:**

- Used when the camera needs to be set or replaced after initialization

### Save/Load Support

#### get_save_state

`get_save_state() -> dict[str, Any]`

Return serializable state for saving.

**Returns:**

- Dictionary containing lerp speed, follow mode, follow target NPC, and smooth setting

**Example:**

```python
save_data = {
    "camera": camera_plugin.get_save_state(),
    # ... other save data
}
```

#### restore_save_state

`restore_save_state(state: dict[str, Any]) -> None`

Restore state from save data.

**Parameters:**

- `state` - Previously saved state dictionary

**Example:**

```python
camera_plugin.restore_save_state(save_data["camera"])
```

**Notes:**

- Restores lerp speed, follow mode, follow target, and smooth setting
- Missing keys fall back to defaults

### Plugin Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the camera plugin with game context.

**Parameters:**

- `context` - Game context providing access to other plugins

**Notes:**

- Called automatically by PluginLoader
- Stores reference to game context

#### cleanup

`cleanup() -> None`

Clean up camera resources when the scene unloads.

**Notes:**

- Clears camera, bounds, and follow configuration
- Called automatically by PluginLoader

#### update

`update(delta_time: float) -> None`

Update camera position based on follow mode.

**Parameters:**

- `delta_time` - Time since last update in seconds

**Notes:**

- Called automatically every frame by PluginLoader
- Follows the player or NPC depending on current follow mode
- Uses smooth or instant follow based on configuration

### Integration Methods

#### load_from_tiled

`load_from_tiled(tile_map: arcade.TileMap, arcade_scene: arcade.Scene) -> None`

Load camera configuration from a Tiled map and create the camera.

**Parameters:**

- `tile_map` - Loaded TileMap with properties
- `arcade_scene` - Scene created from tile_map (unused)

**Notes:**

- Automatically called by the scene plugin when loading maps
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

#### apply_follow_config

`apply_follow_config() -> None`

Apply camera following configuration loaded from Tiled.

**Notes:**

- Called by ScenePlugin after camera is created and set
- Applies the configuration stored by `load_from_tiled()`

#### get_follow_config

`get_follow_config() -> dict[str, Any] | None`

Get the stored follow configuration.

**Returns:**

- Dictionary with follow mode configuration, or `None` if not loaded

## Actions

### FollowPlayerAction

Make camera follow the player sprite continuously.

**Type:** `follow_player`

**Parameters:**

- `smooth: bool` - Use smooth interpolation (default: `true`)

**Example:**

```json
{
    "type": "follow_player"
}
```

```json
{
    "type": "follow_player",
    "smooth": false
}
```

**Notes:**

- Action completes immediately after setting the follow mode
- Camera movement happens in `CameraPlugin.update()` every frame

### FollowNPCAction

Make camera follow a specific NPC sprite continuously.

**Type:** `follow_npc`

**Parameters:**

- `npc: str` - Name of NPC to follow
- `smooth: bool` - Use smooth interpolation (default: `true`)

**Example:**

```json
{
    "type": "follow_npc",
    "npc": "martin"
}
```

```json
{
    "type": "follow_npc",
    "npc": "boss_enemy",
    "smooth": false
}
```

**Notes:**

- NPC must exist in the current scene
- Logs a warning if NPC is not found
- Action completes immediately after setting the follow mode

### StopCameraFollowAction

Stop camera following, keep at current position.

**Type:** `stop_camera_follow`

**Parameters:** None

**Example:**

```json
{
    "type": "stop_camera_follow"
}
```

**Notes:**

- Camera remains at its current position
- Action completes immediately

## Custom Camera Implementation

If you need to replace the camera plugin with a custom implementation (e.g., for advanced camera effects or a different camera backend), you can extend the `CameraBasePlugin` abstract base class.

### CameraBasePlugin

**Location:** [src/pedre/plugins/camera/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/camera/base.py)

The `CameraBasePlugin` class defines the minimum interface that any camera plugin must implement. All methods are abstract and must be implemented by your custom class.

#### Required Methods

Your custom camera plugin must implement these abstract methods:

```python
from pedre.plugins.camera.base import CameraBasePlugin
import arcade

class CustomCameraPlugin(CameraBasePlugin):
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

Register your custom camera plugin using the `@PluginRegistry.register` decorator:

```python
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.camera.base import CameraBasePlugin

@PluginRegistry.register
class CustomCameraPlugin(CameraBasePlugin):
    name = "camera"
    dependencies = ["player", "npc"]

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom plugin inherits from `BasePlugin` (via `CameraBasePlugin`), so you must implement the standard plugin lifecycle methods: `setup()`, `cleanup()`, and `update()`
- The `role` attribute is set to `"camera_plugin"` in the base class
- Your implementation can use any camera system, not just Arcade's Camera2D
- Additional methods beyond the required interface can be added as needed
- Register your custom camera plugin in your project's `INSTALLED_PLUGINS` setting before the default `"pedre.plugins.camera"` to replace it

**Example Custom Implementation:**

```python
# In myproject/plugins/custom_camera.py
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.camera.base import CameraBasePlugin

@PluginRegistry.register
class AdvancedCameraPlugin(CameraBasePlugin):
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
INSTALLED_PLUGINS = [
    "myproject.plugins.custom_camera",  # Load custom camera first
    "pedre.plugins.audio",
    "pedre.plugins.debug",
    # ... rest of plugins (omit "pedre.plugins.camera") ...
]
```

## Usage Examples

### Cutscene Focusing on NPC

```json
[
    {"type": "follow_npc", "npc": "boss"},
    {"type": "dialog", "speaker": "Boss", "text": ["You cannot defeat me!"]},
    {"type": "wait_for_dialog_close"},
    {"type": "follow_player"}
]
```

### Static Camera Shot

```json
[
    {"type": "stop_camera_follow"},
    {"type": "dialog", "speaker": "Narrator", "text": ["Meanwhile..."]},
    {"type": "wait_for_dialog_close"},
    {"type": "follow_player"}
]
```

### NPC Movement with Camera Follow

```json
[
    {"type": "follow_npc", "npc": "martin"},
    {"type": "move_npc", "npcs": ["martin"], "waypoint": "destination"},
    {"type": "wait_for_movement", "npc": "martin"},
    {"type": "dialog", "speaker": "Martin", "text": ["I've arrived!"]},
    {"type": "wait_for_dialog_close"},
    {"type": "follow_player"}
]
```

### Programmatic Camera Control

```python
# Set up camera for a new scene
camera_plugin.set_follow_player(smooth=True)

# Teleport camera for scene transition
camera_plugin.instant_follow(spawn_x, spawn_y)

# Set bounds for the map
camera_plugin.set_bounds(
    map_width=1600,
    map_height=1200,
    viewport_width=1024,
    viewport_height=768
)
```

## See Also

- [NPCPlugin](npc.md) - NPC sprites that can be followed
- [PlayerPlugin](player.md) - Player sprite tracking
- [ScenePlugin](scene.md) - Scene transitions and map loading
- [ScriptPlugin](script.md) - Event-driven scripting
- [Configuration Guide](../guides/configuration.md)
