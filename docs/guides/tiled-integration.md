# Tiled Map Editor Integration

This guide covers everything you need to know about using [Tiled Map Editor](https://www.mapeditor.org/) with Pedre. Tiled is a powerful, free map editor that lets you design your game levels visually.

## Table of Contents

- [Installation](#installation)
- [Map Setup](#map-setup)
- [Required Layers](#required-layers)
- [Map Configuration](#map-configuration)
- [Player Character Setup](#player-character-setup)
- [Working with NPCs](#working-with-npcs)
- [Portals and Transitions](#portals-and-transitions)
- [Waypoints](#waypoints)
- [Interactive Objects](#interactive-objects)
- [Custom Properties](#custom-properties)

## Installation

1. Download Tiled from [mapeditor.org](https://www.mapeditor.org/)
2. Install following the instructions for your platform
3. Launch Tiled to verify installation

## Map Setup

### Creating a New Map

1. **File → New → New Map**

2. **Map Settings:**
      - **Orientation:** Orthogonal
      - **Tile layer format:** CSV (recommended)
      - **Tile render order:** Right Down
      - **Map size:** 25×20 tiles (or whatever size you need)
      - **Tile size:** 32×32 pixels (must match your tileset)

3. Click **Save As** and save to `assets/maps/your_map.tmx`

### Adding a Tileset

1. **Map → New Tileset**

2. **Tileset Settings:**
      - **Name:** Something descriptive (e.g., "terrain", "buildings")
      - **Type:** Based on Tileset Image
      - **Image:** Browse to your tileset PNG file
      - **Tile width:** 32 pixels
      - **Tile height:** 32 pixels
      - **Margin/Spacing:** Set if your tileset has borders

3. Click **Save As** and save to `assets/tilesets/your_tileset.tsx`

### Recommended Free Tilesets

- [Kenny.nl](https://www.kenney.nl/assets?q=2d) - Various game assets
- [OpenGameArt.org](https://opengameart.org/art-search-advanced?keys=&field_art_type_tid%5B%5D=9) - Community-created tilesets
- [itch.io](https://itch.io/game-assets/free/tag-tileset) - Free and paid tilesets

## Required Layers

The framework expects specific layer names. Create these layers in order:

### Tile Layers

#### Floor Layer

```text
Name: Floor
Type: Tile Layer
Purpose: Ground tiles, non-collision decorations
```

This is where you paint your ground terrain:

- Grass, dirt, stone floors
- Roads, paths
- Water (if non-solid)
- Decorative ground elements

#### Walls Layer

```text
Name: Walls
Type: Tile Layer
Purpose: Collidable wall tiles
```

Paint your solid obstacles here:

- Building walls
- Trees, rocks
- Fences
- Any tile that should block player movement

The framework automatically treats all tiles in this layer as solid collision objects.

#### Objects Layer

```text
Name: Objects
Type: Tile Layer
Purpose: Collidable objects (optional)
```

Use this for smaller collidable objects like furniture, rocks, or signposts.

#### Buildings Layer

```text
Name: Buildings
Type: Tile Layer
Purpose: Collidable building structures (optional)
```

Use this for larger structures.

#### Collision Layer (Optional)

```text
Name: Collision
Type: Tile Layer
Purpose: Invisible collision areas
```

Use this for:

- Invisible walls
- Collision boundaries
- Areas where you don't want a visual tile but need collision

**Tip:** Set this layer's opacity to 0.5 in Tiled so you can see it while editing.

### Object Layers

#### NPCs Layer

```text
Name: NPCs
Type: Object Layer
Purpose: NPC spawn points and configuration
```

See [Working with NPCs](#working-with-npcs) for details.

#### Portals Layer

```text
Name: Portals
Type: Object Layer
Purpose: Map transition zones
```

See [Portals and Transitions](#portals-and-transitions) for details.

#### Waypoints Layer

```text
Name: Waypoints
Type: Object Layer
Purpose: Named positions for scripting and spawning
```

See [Waypoints](#waypoints) for details.

#### Interactive Layer (Optional)

```text
Name: Interactive
Type: Object Layer
Purpose: Objects the player can interact with
```

See [Interactive Objects](#interactive-objects) for details.

### Layer Order

The order matters for rendering! From bottom to top:

```text
Floor            (bottom - drawn first)
Walls
Objects
Buildings
Collision
NPCs
Interactive
Portals
Waypoints        (top - drawn last)
```

## Map Configuration

Per-map settings — background music, camera target, and camera movement style — are defined in `assets/data/content/maps.json`, not as Tiled map properties.

Each entry is keyed by the scene name (TMX filename without extension, lowercased). All fields are optional; only add what you want to override from the defaults.

```json
{
  "village": {
    "music": "peaceful_village.ogg",
    "camera_follow": "player",
    "camera_smooth": true
  },
  "cutscene_tower": {
    "camera_follow": "npc:wizard"
  },
  "puzzle_room": {
    "camera_follow": "none"
  }
}
```

See [Maps Content Reference](../content/maps.md) for the full field reference, camera follow modes, and more examples.

## Player Character Setup

The player character is automatically created and managed by the framework, but you can configure its initial position and appearance.

### Player Spawn Position

The framework determines the player's spawn position based on the Player object configuration:

1. **Portal Waypoint** - If Player object has `spawn_at_portal=true` and a portal waypoint is set (from portal transition)
2. **Player Object Position** - Uses the Player object's position in the Player object layer

**Player Object Setup:**

The Player object must be placed as a **Point object** in the "Player" object layer and positioned where you want the player to spawn by default.

**Creating the Player Object:**

1. Select **Player** object layer (create if needed)
2. Click **Insert Point** (or press **I**)
3. Click where you want the player to spawn
4. Set required properties in Properties panel

**Portal Spawning (Optional):**

To make the player spawn at the Player object position instead of portal waypoints:

1. Select the Player object in Tiled
2. Add custom property: `spawn_at_portal` (boolean) = `false`
3. When entering maps via portals, player will spawn at the object position

### Portal Waypoints

When players transition through portals, they spawn at the target waypoint specified in the portal's `spawn_waypoint` property.

1. Select **Waypoints** object layer
2. Click **Insert Point** (or press **I**)
3. Click where you want the portal target to be
4. In Properties panel, set `name` to match the portal's `spawn_waypoint`

```text
Layer: Waypoints
Object: Point at (400, 300)

Properties:
  name: "from_village"
```

**Example Portal Setup:**

In village.tmx portal:

```text
Properties:
  target_map: "forest.tmx"
  spawn_waypoint: "from_village"
```

In forest.tmx waypoints:

```text
Point named "from_village" at spawn location
```

### Player Sprite Configuration

The player sprite is driven entirely by the **content registry**. Animation states, sprite sheet path, and frame layout are defined in `sprites.json`.

**How it works:**

1. The `PlayerPlugin` reads the Player object from Tiled to get the spawn position.
2. It looks up the sprite definition in the `sprites` content registry — first by the object's `sprite_id` property, then by the fallback ID `"player"`.
3. It creates an `AnimatedSprite` from that definition.

**Player Object Properties:**

| Property    | Type   | Required | Description                                                                       |
| ----------- | ------ | -------- | --------------------------------------------------------------------------------- |
| `sprite_id` | string | No       | ID of the sprite definition in `sprites.json`. Defaults to `"player"`             |

**Example Player Object (minimal):**

```text
Player Object Layer:
  - Point at (640, 480)
    Properties:
      (no properties needed if sprites.json defines a "player" entry)
```

**Example Player Object (with explicit sprite):**

```text
Player Object Layer:
  - Point at (640, 480)
    Properties:
      sprite_id: "princess"
```

**Corresponding `sprites.json` entry:**

```json
{
  "princess": {
    "sprite_sheet": "images/characters/princess.png",
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

See [Sprites Content Reference](../content/sprites.md) and [Sprites API](../api/sprites.md) for details on defining sprite states.

### Player Movement

The player is controlled via keyboard input:

- **Arrow Keys** - Move in 8 directions
- **WASD** - Alternative movement keys
- **SPACE** - Interact with NPCs and objects nearby

**Movement Configuration:**

Player movement and interaction speeds are controlled by game settings in your `settings.py` file. See [Configuration Guide](configuration.md#player-settings) for all available player and interaction settings including:

- `PLAYER_MOVEMENT_SPEED` - Player movement speed
- `INTERACTION_PLUGIN_DISTANCE` - Object interaction range
- `NPC_INTERACTION_DISTANCE` - NPC interaction range
- `PORTAL_INTERACTION_DISTANCE` - Portal activation range

### Player Collision

The player automatically collides with:

- Tiles in the **Walls** layer
- Tiles in the **Collision** layer
- Tiles in the **Buildings** layer
- NPCs (unless they're removed from collision with scripts)

The physics engine uses `arcade.PhysicsEngineSimple` for player-wall collision detection.

### Example: Complete Player Setup

**In Tiled (village.tmx):**

```text
Player Object Layer:
  - Point at (640, 480)
    Properties:
      sprite_id: "princess"   (optional — defaults to "player" if omitted)
      spawn_at_portal: false

Map Properties:
  music: "village_theme.ogg"
```

**In `assets/data/content/sprites.json`:**

```json
{
  "princess": {
    "sprite_sheet": "images/characters/princess.png",
    "frame_width": 64,
    "frame_height": 64,
    "states": {
      "idle": {
        "directional": true, "loop": true, "priority": 0,
        "directions": {
          "down": {"frames": 4, "row": 0},
          "up":   {"frames": 4, "row": 1},
          "right":{"frames": 4, "row": 2}
        }
      },
      "walk": {
        "directional": true, "loop": true, "priority": 1,
        "directions": {
          "down": {"frames": 6, "row": 3},
          "up":   {"frames": 6, "row": 4},
          "right":{"frames": 6, "row": 5}
        }
      }
    }
  }
}
```

**For Portal-Only Entry (forest.tmx):**

```text
Player Object Layer:
  - Point at (400, 300)
    (no extra properties needed if sprite is already defined in sprites.json)

Waypoints Layer:
  - Point named "from_village" at (100, 200)
```

**In Code (Game initialization):**

`settings.py`:

```python
# Configure your game
WINDOW_TITLE="My RPG"
SCREEN_WIDTH=1920
SCREEN_HEIGHT=1080
INITIAL_MAP="village.tmx"
```

`main.py`:

```python
from pedre import run_game

if __name__ == "__main__":
    run_game()
```

This will create a window with your custom settings and start the game.

- Spawn at Player object position (640, 480)
- Use default princess sprite sheet
- Be able to move with arrow keys
- Collide with walls and NPCs
- Interact with objects via SPACE key

**When entering via portal:** Player will spawn at the portal's target waypoint instead of the Player object position.

## Working with NPCs

NPCs are placed as **Point Objects** in the **NPCs** object layer. Like the player, NPC appearance is driven by the **content registry** — sprite sheets, animation states, scale, and visibility are defined in `npcs.json` and `sprites.json`.

### How NPC Loading Works

1. The `NPCPlugin` reads each Point object from the `NPCs` layer to get the name and spawn position.
2. It looks up the NPC definition in `npcs.json` by the object's `name` property.
3. The NPC definition references a `sprite_id` pointing to an entry in `sprites.json`.
4. An `AnimatedSprite` is created from the sprite definition, with `scale`, `tile_size`, and `initially_hidden` taken from the NPC definition.

### Adding an NPC

1. Select the **NPCs** object layer
2. Click **Insert Point** (or press **I**)
3. Click where you want the NPC to spawn
4. In the Properties panel, set the `name` property

### Tiled Object Properties

| Property    | Type   | Required | Description                                                              |
| ----------- | ------ | -------- | ------------------------------------------------------------------------ |
| `name`      | string | **Yes**  | NPC identifier — must match a key in `npcs.json` (case-insensitive)      |
| `sprite_id` | string | No       | Override the sprite ID from `npcs.json` for this specific object         |

All other appearance settings (`tile_size`, `scale`, `initially_hidden`) belong in `npcs.json`.

### NPC Content Registry Definitions

**`assets/data/content/npcs.json`:**

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
  }
}
```

**`assets/data/content/sprites.json`:**

```json
{
  "merchant_sprite": {
    "sprite_sheet": "images/characters/merchant.png",
    "frame_width": 64,
    "frame_height": 64,
    "states": {
      "idle": {
        "directional": true, "loop": true, "priority": 0,
        "directions": {
          "down": {"frames": 4, "row": 0},
          "up":   {"frames": 4, "row": 1},
          "right":{"frames": 4, "row": 2}
        }
      },
      "walk": {
        "directional": true, "loop": true, "priority": 1,
        "directions": {
          "down": {"frames": 6, "row": 3},
          "up":   {"frames": 6, "row": 4},
          "right":{"frames": 6, "row": 5}
        }
      }
    }
  },
  "wizard_sprite": {
    "sprite_sheet": "images/characters/wizard.png",
    "frame_width": 64,
    "frame_height": 64,
    "states": {
      "idle": {
        "directional": false, "loop": true, "priority": 0,
        "frames": 4, "row": 0
      },
      "appear": {
        "directional": false, "loop": false, "priority": 5,
        "on_complete": "idle", "frames": 9, "row": 1
      },
      "disappear": {
        "directional": false, "loop": false, "priority": 5,
        "on_complete": "hide", "auto_from": "appear"
      }
    }
  }
}
```

See [Sprites Content Reference](../content/sprites.md) and [Sprites API](../api/sprites.md) for the full sprite definition format, including `auto_from` states and directional auto-flip.

### Example NPC Setup in Tiled

**Minimal — all appearance config is in the registry:**

```text
Layer: NPCs
Object Type: Point
Position: (320, 240)

Properties:
  name: "merchant"
```

**Multiple NPCs:**

```text
NPCs Layer:
  - Point at (320, 240)  → name: "merchant"
  - Point at (640, 480)  → name: "guard"
  - Point at (800, 360)  → name: "elder"
```

Each NPC needs:

1. A unique `name` property matching a key in `npcs.json`
2. A corresponding entry in `npcs.json` referencing a `sprite_id` in `sprites.json`
3. Optional: Dialog entries in `assets/data/dialogs/{scene_name}_dialogs.json` if the NPC should be interactive

## Portals and Transitions

Portals are **Rectangle Objects** that trigger map transitions when the player enters them. The portal plugin uses an event-driven architecture where portal behavior is defined in JSON scripts.

### Creating a Portal

1. Select the **Portals** object layer
2. Click **Insert Rectangle** (or press **R**)
3. Draw a rectangle where the portal zone should be
4. Set the portal's `name` property

### Portal Properties

| Property | Type   | Required | Description                                        | Example       |
| -------- | ------ | -------- | -------------------------------------------------- | ------------- |
| `name`   | string | **Yes**  | Unique portal identifier (used in script triggers) | `"to_forest"` |

Portal behavior (destination, conditions, cutscenes) is defined in script files, not Tiled properties.

### Example Portal Setup

**In village.tmx:**

```text
Layer: Portals
Object: Rectangle at map edge (64, 0, 32, 64)

Properties:
  name: "to_forest"
```

**In forest.tmx:**

```text
Layer: Waypoints
Object: Point at entrance (100, 200)

Properties:
  name: "from_village"
```

**In scripts JSON:**

```json
{
  "to_forest_portal": {
    "trigger": {"event": "portal_entered", "portal": "to_forest"},
    "actions": [
      {"name": "change_scene", "target_map": "forest.tmx", "spawn_waypoint": "from_village"}
    ]
  }
}
```

### Portal Scripts

Portal transitions are handled through the script plugin using the `portal_entered` event and `change_scene` action.

**Simple Portal:**

```json
{
  "forest_portal": {
    "trigger": {"event": "portal_entered", "portal": "forest_entrance"},
    "actions": [
      {"name": "change_scene", "target_map": "Forest.tmx", "spawn_waypoint": "entrance"}
    ]
  }
}
```

**Conditional Portal:**

```json
{
  "tower_gate_open": {
    "trigger": {"event": "portal_entered", "portal": "tower_gate"},
    "conditions": [{"name": "npc_dialog_level", "npc": "guard", "gte": 2}],
    "actions": [
      {"name": "change_scene", "target_map": "Tower.tmx", "spawn_waypoint": "entrance"}
    ]
  },
  "tower_gate_locked": {
    "trigger": {"event": "portal_entered", "portal": "tower_gate"},
    "conditions": [{"name": "npc_dialog_level", "npc": "guard", "lt": 2}],
    "actions": [
      {"name": "dialog", "speaker": "Narrator", "text": ["The gate is locked..."]}
    ]
  }
}
```

**Portal with Cutscene:**

```json
{
  "dungeon_first_entry": {
    "trigger": {"event": "portal_entered", "portal": "dungeon_portal"},
    "run_once": true,
    "actions": [
      {"name": "dialog", "speaker": "Narrator", "text": ["A cold wind blows..."]},
      {"name": "wait_for_dialog_close"},
      {"name": "change_scene", "target_map": "Dungeon.tmx", "spawn_waypoint": "entrance"}
    ]
  },
  "dungeon_return": {
    "trigger": {"event": "portal_entered", "portal": "dungeon_portal"},
    "conditions": [{"name": "script_completed", "script": "dungeon_first_entry"}],
    "actions": [
      {"name": "change_scene", "target_map": "Dungeon.tmx", "spawn_waypoint": "entrance"}
    ]
  }
}
```

See [Scripting Events](scripting/events.md) and [Scripting Actions](scripting/actions.md) for more details.

## Waypoints

Waypoints are **Point Objects** that define named positions on the map.

### Creating a Waypoint

1. Select the **Waypoints** object layer
2. Click **Insert Point** (or press **I**)
3. Click where you want the waypoint
4. Set the `name` property

### Waypoint Uses

| Use Case                | Description                                                                      |
| ----------------------- | -------------------------------------------------------------------------------- |
| **Portal destinations** | Target location for map transitions (used with portal `spawn_waypoint` property) |
| **NPC movement**        | Destinations for pathfinding scripts                                             |

**Note:** Waypoints are simple named locations stored as Point objects. They only need a `name` property. The framework converts their pixel coordinates to tile coordinates and stores them in a dictionary for lookup by name.

### Example Waypoint Setup

```text
Layer: Waypoints

Points:
  - name: "from_village" at (100, 100)
  - name: "from_forest" at (750, 50)
  - name: "merchant_home" at (200, 450)
  - name: "well" at (600, 350)
  - name: "town_center" at (500, 400)
```

### Using Waypoints in Scripts

Reference waypoints by name in your scripts:

```json
{
  "name": "move_npc",
  "npcs": ["merchant"],
  "waypoint": "well"
}
```

The NPC will use A* pathfinding to navigate to the waypoint, avoiding walls.

## Interactive Objects

Interactive objects are shapes (rectangles, polygons, points) that trigger actions when the player presses SPACE nearby.

### Creating Interactive Objects

1. Select the **Interactive** object layer
2. Insert any shape type:
      - **Rectangle** - Area-based interactions (chests, doors)
      - **Point** - Single-point interactions (signs, items)
      - **Polygon** - Complex shape interactions
3. Set the object's properties

### Interactive Object Properties

| Property | Type   | Required | Description       | Example            |
| -------- | ------ | -------- | ----------------- | ------------------ |
| `name`   | string | **Yes**  | Unique identifier | `"treasure_chest"` |

## Custom Properties

You can add any custom properties to objects and reference them in scripts.

### Adding Custom Properties

1. Select an object
2. In Properties panel, click the **+** button
3. Choose property type:
      - **bool** - true/false
      - **int** - Integer numbers
      - **float** - Decimal numbers
      - **string** - Text
      - **color** - Color value
      - **file** - File path

### Example: Custom NPC with Additional Properties

```text
Layer: NPCs
Object: Point

Required Properties:
  name: "quest_giver"

Custom Properties:
  quest_id: "find_amulet"
  quest_stage: 1
  greeting_message: "Greetings, traveler!"
  relationship_level: 0
```

Appearance is defined in `npcs.json` / `sprites.json`.

You can add any custom properties you need to objects. These properties are stored in the object's `properties` dictionary and can be accessed in your game code or scripts to implement custom behavior, track state, or configure object-specific settings.

## Resources

- [Tiled Documentation](https://doc.mapeditor.org/)
- [Arcade Tilemap Guide](https://api.arcade.academy/en/latest/api/tilemap.html)
- [Free Tilesets](https://opengameart.org/)
- [Tiled Forum](https://discourse.mapeditor.org/)

---

**Next Steps:**

- [Scripting Guide](scripting/index.md) - Learn about event-driven actions
- [Plugins Reference](../plugins/index.md) - Individual plugin documentation
- [API Reference](../api/index.md) - API reference
