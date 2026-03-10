# Sprites

Generic data-driven animated sprite for player and NPC characters.

## Location

[src/pedre/sprites/](https://github.com/msaizar/pedre/blob/main/src/pedre/sprites/)

## AnimatedSprite

A single sprite class that covers all character types. Animation states are defined via data (typically loaded from the content registry) rather than constructor parameters. The sprite runs a priority-based state machine: the highest-priority active state plays.

`"idle"` is the implicit base state — it is always active and has the lowest priority (0 by convention).

### Constructor

```python
from pedre.sprites import AnimatedSprite, AnimationStateConfig

sprite = AnimatedSprite(
    sprite_sheet_path="characters/player.png",
    tile_size=32,
    scale=2.0,
    center_x=320,
    center_y=240,
    states={
        "idle": AnimationStateConfig(
            name="idle", directional=True, loop=True, priority=0,
            directions={
                "down":  {"frames": 4, "row": 0},
                "up":    {"frames": 4, "row": 1},
                "right": {"frames": 4, "row": 2},
            },
        ),
        "walk": AnimationStateConfig(
            name="walk", directional=True, loop=True, priority=1,
            directions={
                "down":  {"frames": 6, "row": 3},
                "up":    {"frames": 6, "row": 4},
                "right": {"frames": 6, "row": 5},
            },
        ),
    },
)
```

**Parameters:**

- `sprite_sheet_path` (str) — Path to the sprite sheet PNG relative to assets
- `tile_size` (int) — Size of each frame in pixels; defaults to `settings.TILE_SIZE`
- `scale` (float) — Sprite scale multiplier; default `1.0`
- `center_x` (float) — Initial X position in world coordinates
- `center_y` (float) — Initial Y position in world coordinates
- `states` (dict[str, AnimationStateConfig]) — All animation states for this sprite

### Factory Method

The preferred way to create a sprite from content registry data:

```python
sprite_def = context.content_registry.get_sub_registry("sprites").get("player")
sprite = AnimatedSprite.from_definition(
    sprite_def,
    center_x=320,
    center_y=240,
    scale=2.0,
)
```

`from_definition` reads `sprite_sheet`, `frame_width`, and `states` from the definition dict and builds `AnimationStateConfig` objects automatically.

### Methods

#### request_state

`request_state(name: str) -> None`

Activate a named animation state. The state with the highest priority among all active states plays.

- For looping states (e.g. `"walk"`), the state stays active until `release_state()` is called.
- For one-shot states (e.g. `"appear"`), it is automatically removed when the animation completes.

```python
sprite.request_state("walk")
```

#### release_state

`release_state(name: str) -> None`

Deactivate a looping state. Has no effect on `"idle"` (always active).

```python
sprite.release_state("walk")
```

#### set_direction

`set_direction(direction: str) -> None`

Change the facing direction, resetting the current animation frame.

- `direction`: one of `"up"`, `"down"`, `"left"`, `"right"`

```python
sprite.set_direction("up")
```

#### update_animation

`update_animation(delta_time: float) -> None`

Advance the animation state machine. Called automatically by Arcade's update loop.

```python
sprite.update_animation(delta_time)
```

#### is_state_complete

`is_state_complete(name: str) -> bool`

Returns `True` if a one-shot state has finished its animation.

```python
if sprite.is_state_complete("appear"):
    # Appearance animation done
```

#### has_state

`has_state(name: str) -> bool`

Returns `True` if the sprite has a state with this name defined.

#### reset_state

`reset_state(name: str) -> None`

Reset the completion flag for a one-shot state so it can be re-triggered.

#### mark_state_complete

`mark_state_complete(name: str) -> None`

Force-mark a one-shot state as complete (used when restoring saved game state).

### Attributes

- `current_direction: str` — Current facing direction (`"up"`, `"down"`, `"left"`, `"right"`)
- `current_frame: int` — Current frame index in the active animation
- `animation_speed: float` — Seconds between frames (default `0.15`)
- `animation_textures: dict[str, list[arcade.Texture]]` — Loaded textures keyed by state/direction

---

## AnimationStateConfig

Dataclass describing a single animation state.

```python
from pedre.sprites import AnimationStateConfig
```

### Fields

| Field | Type | Description |
| ----- | ---- | ----------- |
| `name` | str | State name (e.g. `"idle"`, `"walk"`, `"appear"`) |
| `directional` | bool | If `True`, state has per-direction variants (`_up/_down/_left/_right`) |
| `loop` | bool | If `True`, animation loops; if `False`, plays once then fires `on_complete` |
| `priority` | int | Higher value preempts lower-priority active states |
| `on_complete` | str \| None | What to do when a one-shot animation finishes: `"idle"` (return to idle) or `"hide"` (hide sprite then return to idle) |
| `frames` | int \| None | Frame count for non-directional states |
| `row` | int \| None | Sprite sheet row for non-directional states |
| `directions` | dict \| None | Per-direction data: `{"up": {"frames": N, "row": R}, ...}` |
| `auto_from` | str \| None | Generate this state by reversing frames from another state (e.g. `"disappear"` from `"appear"`) |
| `reverse_load` | bool | Load frames in reverse order from the sheet |

### Directional States

For directional states, define each direction under `directions`. A missing `"left"` is auto-generated by horizontally flipping `"right"`, and vice versa.

```json
"walk": {
  "directional": true,
  "loop": true,
  "priority": 1,
  "directions": {
    "down":  {"frames": 6, "row": 0},
    "up":    {"frames": 6, "row": 1},
    "right": {"frames": 6, "row": 2}
  }
}
```

### Non-Directional States

For non-directional states, define `frames` and `row` at the top level.

```json
"appear": {
  "directional": false,
  "loop": false,
  "priority": 5,
  "on_complete": "idle",
  "frames": 9,
  "row": 8
}
```

### Auto-Generated States

Use `auto_from` to generate a state by reversing another state's frames. Useful for disappear/appear pairs:

```json
"disappear": {
  "directional": false,
  "loop": false,
  "priority": 5,
  "on_complete": "hide",
  "auto_from": "appear"
}
```

---

## Sprite Sheet Format

Frames are laid out in rows. Each row contains frames for one animation (and direction, for directional states). All frames must be the same square dimensions (`tile_size × tile_size`).

```text
Row 0: Walk Down   [frame 0] [frame 1] ... [frame 5]
Row 1: Walk Up     [frame 0] [frame 1] ... [frame 5]
Row 2: Walk Right  [frame 0] [frame 1] ... [frame 5]
Row 3: Idle Down   [frame 0] [frame 1] [frame 2] [frame 3]
...
```

Left-facing animations can be omitted — the sprite will auto-generate them by flipping the right-facing row.

## See Also

- [Sprites Content Reference](../content/sprites.md) — Full sprites.json schema
- [Custom Content Types](../extending/custom-content.md) — How the content registry works
- [Player Plugin](../plugins/player.md) — PlayerPlugin documentation
- [NPC Plugin](../plugins/npc.md) — NPCPlugin documentation
- [Tiled Integration](../guides/tiled-integration.md) — Setting up sprites in Tiled
