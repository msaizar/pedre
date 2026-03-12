# NPCs

NPC definitions describe each character's appearance and initial visibility. Spawn positions come from Point objects in the `NPCs` layer of your Tiled map.

**File:** `assets/data/content/npcs.json`

## Fields

| Field              | Type   | Required | Description                                                         |
| ------------------ | ------ | -------- | ------------------------------------------------------------------- |
| `sprite_id`        | string | **Yes**  | ID of the sprite definition in `sprites.json`                       |
| `scale`            | float  | No       | Render scale multiplier (default: `1.0`)                            |
| `tile_size`        | int    | No       | Tile size used to compute pixel dimensions (default: map tile size) |
| `initially_hidden` | bool   | No       | Start the NPC invisible (default: `false`)                          |

`sprite_id` is validated against the sprites registry at startup — a missing sprite ID raises an error.

## Example

```json
{
  "merchant": {
    "sprite_id": "merchant_sprite",
    "scale": 1.0,
    "tile_size": 64
  },
  "wizard": {
    "sprite_id": "wizard_sprite",
    "initially_hidden": true
  },
  "guard": {
    "sprite_id": "guard_sprite"
  }
}
```

## Placing NPCs in Tiled

Each NPC entry corresponds to a **Point object** in the `NPCs` object layer of your map. The object's `name` property must match the key in `npcs.json` (case-insensitive).

```text
Layer: NPCs (Object Layer)
  - Point at (320, 240)  →  name: "merchant"
  - Point at (640, 480)  →  name: "wizard"
```

The only Tiled property you need on an NPC object is `name`. All appearance settings live in `npcs.json`.

## See Also

- [Sprites](sprites.md) — defining sprite animations referenced by `sprite_id`
- [Tiled Integration](../guides/tiled-integration.md#working-with-npcs) — placing NPCs in maps
