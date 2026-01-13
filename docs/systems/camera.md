# CameraManager

Smooth camera following with optional bounds.

## Location

`src/pedre/systems/camera.py`

## Initialization

```python
from pedre.systems.camera import CameraManager

camera_manager = CameraManager(
    camera=arcade.Camera(window.width, window.height),
    smoothing=0.1  # 0.0 (instant) to 1.0 (very smooth)
)
```

## Key Methods

### `follow_sprite(sprite: arcade.Sprite) -> None`

Set the camera to follow a sprite.

**Parameters:**

- `sprite` - Sprite to follow (usually the player)

**Example:**

```python
camera_manager.follow_sprite(self.player)
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

### `update(delta_time: float) -> None`

Update camera position (call every frame).

**Parameters:**

- `delta_time` - Time since last update in seconds

**Example:**

```python
def on_update(self, delta_time):
    self.camera_manager.update(delta_time)
    self.camera_manager.camera.use()  # Activate camera
```
