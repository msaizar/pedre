# ParticleManager

Visual effects and particle systems.

## Location

`src/pedre/systems/particle.py`

## Initialization

```python
from pedre.systems.particle import ParticleManager

particle_manager = ParticleManager()
```

## Key Methods

### `emit_particles(x: float, y: float, effect: str = "sparkle", duration: float = 1.0) -> None`

Spawn particles at a location.

**Parameters:**

- `x`, `y` - Position to spawn particles
- `effect` - Effect type (e.g., "sparkle", "smoke", "stars")
- `duration` - How long particles last in seconds

**Example:**

```python
# Sparkle effect when collecting item
particle_manager.emit_particles(
    x=item.center_x,
    y=item.center_y,
    effect="sparkle",
    duration=2.0
)
```

### `update(delta_time: float) -> None`

Update active particles (call every frame).

### `draw() -> None`

Draw all active particles (call in `on_draw()`).
