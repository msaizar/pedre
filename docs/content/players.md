# Players

Player definitions describe the player character's appearance and optional default spawn positions.

**File:** `assets/data/content/players.json`

## Fields

| Field               | Type            | Required | Description                                                                     |
| ------------------- | --------------- | -------- | ------------------------------------------------------------------------------- |
| `sprite_id`         | string          | **Yes**  | ID of the sprite definition in `sprites.json`                                   |
| `spawn_at_position` | list of strings | No       | Map names where the player spawns at its position after a scene transition      |

`sprite_id` is validated against the sprites registry at startup — a missing sprite ID raises an error.

## Example

```json
{
  "player": {
    "sprite_id": "hero",
    "spawn_at_position": ["village"]
  }
}
```

A minimal definition with only the required field:

```json
{
  "player": {
    "sprite_id": "hero"
  }
}
```

## Player Sprite Lookup

The `PlayerPlugin` looks up the player definition in two steps:

1. If the Player object in Tiled has a `sprite_id` property, that sprite ID is used directly.
2. Otherwise, it looks for a player definition in `players.json` — first by the object's `name` property, then by the fallback key `"player"`.

This means you can have a single `"player"` entry in `players.json` as the default, or define multiple player characters keyed by different names.

## Placing the Player in Tiled

The player's spawn position comes from a **Point object** in the `Player` object layer. The object's `name` is used to look up the definition in `players.json`.

```text
Layer: Player (Object Layer)
  - Point at (640, 480)
    Properties:
      name: "player"      (matches key in players.json)
```

When the player enters a map via a portal, the spawn position is determined by the portal's target waypoint instead of the object position.

## See Also

- [Sprites](sprites.md) — defining sprite animations referenced by `sprite_id`
- [Tiled Integration](../guides/tiled-integration.md#player-character-setup) — player spawn and portal behavior
