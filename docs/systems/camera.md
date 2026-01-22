# CameraManager

Smooth camera following with optional bounds.

## Location

`src/pedre/systems/camera/manager.py`

## Initialization

```python
from pedre.systems.camera import CameraManager

camera_manager = CameraManager(
    camera=arcade.Camera(window.width, window.height),
    smoothing=0.1  # 0.0 (instant) to 1.0 (very smooth)
)
```

## Key Methods

### `smooth_follow(target_x: float, target_y: float) -> None`

Smoothly move camera towards target position.

**Parameters:**

- `target_x` - Target X coordinate (e.g. player.center_x)
- `target_y` - Target Y coordinate (e.g. player.center_y)

**Example:**

```python
camera_manager.smooth_follow(player.center_x, player.center_y)
```

### `set_bounds(min_x: float, min_y: float, max_x: float, max_y: float) -> None`

Set camera movement boundaries.

**Parameters:**

- `min_x`, `min_y` - Minimum camera position
- `max_x`, `max_y` - Maximum camera position

**Example:**

```python
# Keep camera within map bounds
camera_manager.set_bounds(
    min_x=0,
    min_y=0,
    max_x=map_width - window.width,
    max_y=map_height - window.height
)
```

### `use() -> None`

Activate this camera for rendering. Call this before drawing world objects.

**Example:**

```python
camera_manager.use()
# Draw world objects...
```

### `shake(intensity: float = 10.0, duration: float = 0.5) -> None`

(Placeholder) Add camera shake effect. Currently not implemented.

**Example:**

```python
def on_update(self, delta_time):
    self.camera_manager.update(delta_time)
    self.camera_manager.camera.use()  # Activate camera
```
