# Sprites

Sprites define animated characters and objects using sprite sheets. They are referenced by `sprite_id` in NPC, Player, and other definitions.

**File:** `assets/data/content/sprites.json`

## Top-Level Fields

| Field          | Type   | Required | Description                                          |
| -------------- | ------ | -------- | ---------------------------------------------------- |
| `sprite_sheet` | string | **Yes**  | Path to the sprite sheet image (relative to assets/) |
| `frame_width`  | int    | **Yes**  | Width of a single frame in pixels                    |
| `frame_height` | int    | **Yes**  | Height of a single frame in pixels                   |
| `states`       | object | **Yes**  | Dictionary of animation states (see below)           |

## State Fields

Each key in `states` is a state name (e.g. `"idle"`, `"walk"`). Each state object has:

| Field          | Type   | Required | Description                                                                         |
| -------------- | ------ | -------- | ----------------------------------------------------------------------------------- |
| `directional`  | bool   | **Yes**  | Whether the state has per-direction animations                                      |
| `loop`         | bool   | **Yes**  | Whether the animation loops                                                         |
| `priority`     | int    | **Yes**  | Higher priority states override lower ones (e.g. `walk` at 1 overrides `idle` at 0) |
| `auto_from`    | string | No       | Inherit frame data from another state name (see [Auto States](#auto-states)).       |
| `on_complete`  | string | No       | What happens when a non-looping animation finishes: `"idle"` or `"hide"`            |

### Directional States (`directional: true`)

Requires a `directions` object. Each key is a direction name (e.g. `"down"`, `"up"`, `"right"`); left is automatically mirrored from right.

| Field     | Type | Required | Description                         |
| --------- | ---- | -------- | ----------------------------------- |
| `frames`  | int  | **Yes**  | Number of frames for this direction |
| `row`     | int  | **Yes**  | Sprite sheet row (0-indexed)        |

### Non-Directional States (`directional: false`)

Frame data sits directly on the state object:

| Field    | Type | Required | Description                  |
| -------- | ---- | -------- | ---------------------------- |
| `frames` | int  | **Yes**  | Number of frames             |
| `row`    | int  | **Yes**  | Sprite sheet row (0-indexed) |

## Auto States

Setting `auto_from` on a state makes it inherit all frame data from the named state, but plays it in reverse. This is used to create a reverse animation (e.g. `disappear` as the reverse of `appear`) without duplicating frame data.

States with `auto_from` must not define `frames`, `row`, or `directions` — those come from the source state.

## Examples

### Directional Character (idle + walk)

```json
{
  "hero": {
    "sprite_sheet": "images/characters/hero.png",
    "frame_width": 64,
    "frame_height": 64,
    "states": {
      "idle": {
        "directional": true,
        "loop": true,
        "priority": 0,
        "directions": {
          "down":  {"frames": 4, "row": 0},
          "up":    {"frames": 4, "row": 1},
          "right": {"frames": 4, "row": 2}
        }
      },
      "walk": {
        "directional": true,
        "loop": true,
        "priority": 1,
        "directions": {
          "down":  {"frames": 6, "row": 3},
          "up":    {"frames": 6, "row": 4},
          "right": {"frames": 6, "row": 5}
        }
      }
    }
  }
}
```

### Non-Directional with Appear/Disappear (auto_from)

```json
{
  "wizard": {
    "sprite_sheet": "images/characters/wizard.png",
    "frame_width": 64,
    "frame_height": 64,
    "states": {
      "idle": {
        "directional": false,
        "loop": true,
        "priority": 0,
        "frames": 4,
        "row": 0
      },
      "appear": {
        "directional": false,
        "loop": false,
        "priority": 5,
        "on_complete": "idle",
        "frames": 9,
        "row": 1
      },
      "disappear": {
        "directional": false,
        "loop": false,
        "priority": 5,
        "on_complete": "hide",
        "auto_from": "appear"
      }
    }
  }
}
```

Here `disappear` plays `appear`'s frames in reverse, then hides the sprite.

## See Also

- [NPCs](npcs.md) — reference sprites via `sprite_id`
- [Players](players.md) — reference sprites via `sprite_id`
- [Sprites API](../api/sprites.md) — runtime API for animated sprites
