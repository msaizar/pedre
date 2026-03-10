# Maps

Map definitions let you override per-map behavior — music, camera following, and camera movement style. All fields are optional; only define what you want to change from the defaults.

**File:** `assets/data/content/maps.json`

## Keys

Each top-level key is the **scene name**: the TMX filename without its extension, lowercased.

For example, `Village.tmx` → `"village"`, `DungeonLevel1.tmx` → `"dungeonlevel1"`.

## Fields

| Field           | Type   | Required | Default    | Description                                                              |
| --------------- | ------ | -------- | ---------- | ------------------------------------------------------------------------ |
| `music`         | string | No       | None       | Background music file, relative to `assets/audio/music/`                 |
| `camera_follow` | string | No       | `"player"` | What the camera tracks (see [Camera Follow Modes](#camera-follow-modes)) |
| `camera_smooth` | bool   | No       | `true`     | Smooth lerp (`true`) or instant snap (`false`)                           |

## Camera Follow Modes

The `camera_follow` field accepts:

- **`"player"`** — Camera follows the player sprite (default if omitted)
- **`"npc:<name>"`** — Camera follows a specific NPC by name (e.g. `"npc:merchant"`)
- **`"none"`** — Static camera, no following

If `camera_follow` names an NPC that doesn't exist on the current map, the camera falls back to following the player.

## Camera Smoothing

- **`true`** (default) — Camera interpolates toward the target each frame (cinematic feel)
- **`false`** — Camera instantly snaps to the target position (no lag)

## Example

```json
{
  "village": {
    "music": "peaceful_village.ogg",
    "camera_follow": "player",
    "camera_smooth": true
  },
  "beach": {
    "music": "beach_waves.ogg"
  },
  "cutscene_tower": {
    "camera_follow": "npc:wizard",
    "camera_smooth": true
  },
  "puzzle_room": {
    "camera_follow": "none"
  },
  "arena": {
    "camera_follow": "player",
    "camera_smooth": false
  }
}
```

## Notes

- You can change camera following at runtime using camera actions in scripts: `FollowPlayerAction`, `FollowNPCAction`, `StopCameraFollowAction`.
- Entries are optional — maps with no entry in `maps.json` use the defaults (follow player, smooth camera, no music).

## See Also

- [Tiled Integration](../guides/tiled-integration.md) — how maps are structured in Tiled
- [Camera Plugin](../plugins/camera.md) — runtime camera behavior
