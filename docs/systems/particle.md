# ParticleManager

Visual effects and particle systems.

## Location

`src/pedre/systems/particle/manager.py`

## Initialization

```python
from pedre.systems.particle import ParticleManager

particle_manager = ParticleManager()
```

## Key Methods

### `emit_sparkles(x: float, y: float, count: int = 15, color: tuple = (255, 255, 100)) -> None`

Emit sparkle particles for interactions.

### `emit_hearts(x: float, y: float, count: int = 10, color: tuple = (255, 105, 180)) -> None`

Emit heart particles for affection/romance.

### `emit_burst(x: float, y: float, count: int = 20, color: tuple = (255, 200, 0)) -> None`

Emit a burst of particles for dramatic events.

### `emit_trail(x: float, y: float, count: int = 3, color: tuple = (200, 200, 255)) -> None`

Emit subtle trail particles for movement.

### `update(delta_time: float) -> None`

Update active particles (call every frame).

### `draw() -> None`

Draw all active particles (call in `on_draw()`).
