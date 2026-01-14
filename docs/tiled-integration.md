# Tiled Map Editor Integration

This guide covers everything you need to know about using [Tiled Map Editor](https://www.mapeditor.org/) with Arcade Tiled RPG. Tiled is a powerful, free map editor that lets you design your game levels visually.

## Table of Contents

- [Installation](#installation)
- [Map Setup](#map-setup)
- [Required Layers](#required-layers)
- [Map Properties](#map-properties)
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
Collision
NPCs
Interactive
Portals
Waypoints        (top - drawn last)
```

## Map Properties

Set properties on the map itself (not layers) to configure map behavior.

### How to Set Map Properties

1. Click on the map name in the Layers panel (deselect any layers)
2. Open the Properties panel (View → Properties)
3. Click the **+** button to add custom properties

### Available Map Properties

| Property | Type | Required | Description | Example |
| -------- | ---- | -------- | ----------- | ------- |
| `music` | string | No | Background music file (relative to assets/audio/music/) | `"village_theme.mp3"` |
| `show_all_npcs` | bool | No | Force all NPCs to be visible | `true` |
| `show_npcs` | string | No | Comma-separated list of NPCs to show | `"merchant,guard,elder"` |

### Example Map Property Configuration

```text
music: "peaceful_village.ogg"
show_npcs: "merchant,blacksmith"
```

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

To make the player spawn at portal waypoints instead of the Player object position:

1. Select the Player object in Tiled
2. Add custom property: `spawn_at_portal` (boolean) = `true`
3. When entering maps via portals, player will spawn at the target waypoint
4. If no portal waypoint exists, falls back to Player object position

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

The framework uses the `AnimatedPlayer` class which loads sprite sheets with directional animations.

**Example Player Sprite:**

```text
File: assets/images/characters/princess.png
Tile Size: 64×64 pixels
Columns: 12 animation frames
Scale: 1.0
```

**Note:** The framework does not provide a default player sprite. You must specify the `sprite_sheet` property in your Player object in Tiled.

**Sprite Sheet Layout:**

The player sprite sheet can have:

- **4 directions:** Up, Down, Left, Right
- **2 animation states:** Idle and walking
- **Multiple frames:** 12 columns for smooth animation
- **Consistent size:** All frames must be the same dimensions

**Required Player Object Properties:**

| Property | Type | Default | Description |
| -------- | ---- | ------- | ----------- |
| `sprite_sheet` | string | **Yes** | Path to sprite sheet (relative to assets/) |
| `tile_size` | int | 64 | Size of each sprite frame in pixels |

**Animation Properties (Optional):**

| Property | Type | Default | Description |
| -------- | ---- | ------- | ----------- |
| `idle_up_frames`, `idle_down_frames`, `idle_left_frames`, `idle_right_frames` | int | None | Idle frames per direction |
| `idle_up_row`, `idle_down_row`, `idle_left_row`, `idle_right_row` | int | None | Row index per direction |
| `walk_up_frames`, `walk_down_frames`, `walk_left_frames`, `walk_right_frames` | int | None | Walk frames per direction |
| `walk_up_row`, `walk_down_row`, `walk_left_row`, `walk_right_row` | int | None | Row index per direction |

**4-Directional Example:**

```text
Player Object Properties:
  sprite_sheet: "images/characters/warrior.png"
  tile_size: 64
  idle_up_frames: 6
  idle_up_row: 0
  idle_down_frames: 6
  idle_down_row: 1
  idle_left_frames: 6
  idle_left_row: 2
  idle_right_frames: 6
  idle_right_row: 3
  walk_up_frames: 8
  walk_up_row: 4
  walk_down_frames: 8
  walk_down_row: 5
  walk_left_frames: 8
  walk_left_row: 6
  walk_right_frames: 8
  walk_right_row: 7
```

### Player Movement

The player is controlled via keyboard input:

- **Arrow Keys** - Move in 8 directions
- **WASD** - Alternative movement keys
- **SPACE** - Interact with NPCs and objects nearby

**Movement Configuration:**

Player movement and interaction speeds are controlled by game settings. These can be configured when creating your GameSettings:

| Property | Default | Description |
| -------- | ------- | ----------- |
| `player_movement_speed` | 3 | Player movement speed (pixels per frame) |
| `tile_size` | 32 | Size of each game tile (pixels) |
| `interaction_manager_distance` | 50 | Distance for object interaction (pixels, ~1.5 tiles) |
| `npc_interaction_distance` | 50 | Distance for NPC interaction (pixels, ~1.5 tiles) |
| `portal_interaction_distance` | 50 | Distance for portal activation (pixels, ~1.5 tiles) |
| `waypoint_threshold` | 2 | Distance threshold for reaching waypoints (pixels) |

### Player Collision

The player automatically collides with:

- Tiles in the **Walls** layer
- Tiles in the **Collision** layer
- NPCs (unless they're removed from collision with scripts)

The physics engine uses `arcade.PhysicsEngineSimple` for player-wall collision detection.

### Example: Complete Player Setup

**In Tiled (village.tmx):**

```text
Player Object Layer:
  - Point at (640, 480)
    Properties:
      sprite_sheet: "images/characters/princess.png"
      tile_size: 64
      idle_up_frames: 4
      idle_up_row: 0
      idle_down_frames: 4
      idle_down_row: 1
      idle_left_frames: 4
      idle_left_row: 2
      idle_right_frames: 4
      idle_right_row: 3
      walk_up_frames: 6
      walk_up_row: 4
      walk_down_frames: 6
      walk_down_row: 5
      walk_left_frames: 6
      walk_left_row: 6
      walk_right_frames: 6
      walk_right_row: 7
      spawn_at_portal: false

Map Properties:
  music: "village_theme.ogg"
```

**For Portal-Only Entry (forest.tmx):**

```text
Player Object Layer:
  - Point at (400, 300)
    Properties:
      sprite_sheet: "images/characters/princess.png"
      tile_size: 64
      idle_up_frames: 4
      idle_up_row: 0
      idle_down_frames: 4
      idle_down_row: 1
      idle_left_frames: 4
      idle_left_row: 2
      idle_right_frames: 4
      idle_right_row: 3
      walk_up_frames: 6
      walk_up_row: 4
      walk_down_frames: 6
      walk_down_row: 5
      walk_left_frames: 6
      walk_left_row: 6
      walk_right_frames: 6
      walk_right_row: 7
      spawn_at_portal: true

Waypoints Layer:
  - Point named "from_village" at (100, 200)
```

**In Code (Game initialization):**

```python
from pedre import GameSettings, run_game

# Configure your game
settings = GameSettings(
    window_title="My RPG",
    screen_width=1920,
    screen_height=1080,
    initial_map="village.tmx"
)

if __name__ == "__main__":
    run_game(settings)
```

This will create a window with your custom settings and start the game.

- Spawn at Player object position (640, 480)
- Use default princess sprite sheet
- Be able to move with arrow keys
- Collide with walls and NPCs
- Interact with objects via SPACE key

**When entering via portal:** Player will spawn at the portal's target waypoint instead of the Player object position.

## Working with NPCs

NPCs are placed as **Point Objects** in the **NPCs** object layer.

### Adding an NPC

1. Select the **NPCs** object layer
2. Click **Insert Point** button (or press **I**)
3. Click on the map where you want to NPC
4. In Properties panel, set the NPC's properties

### Required NPC Properties

| Property | Type | Required | Description |
| -------- | ---- | -------- | ----------- |
| `name` | string | **Yes** | Unique identifier for this NPC |
| `sprite_sheet` | string | **Yes** | Path to sprite sheet (relative to assets/) |

### Optional NPC Properties

| Property | Type | Default | Description |
| -------- | ---- | ------- | ----------- |
| `tile_size` | int | `64` | Size of each sprite frame in pixels |
| `columns` | int | `12` | Total number of columns in the sprite sheet |
| `scale` | float | `1.0` | Sprite scale multiplier for rendering |
| `initially_hidden` | bool | `false` | Whether NPC starts hidden (if map property set) |
| `dialog_level` | int | `0` | Starting conversation level |
| `animation` | string | `"idle"` | Starting animation state |

### NPC Sprite Sheets

NPC sprite sheets support 4-directional animation with flexible layout. Specify properties for each animation state and direction.

**Sprite Sheet Format:**

- **Any number of rows** (for different directions and animation types)
- **Any number of columns** (animation frames per row)
- **Consistent tile size** across all frames (e.g., 64×64)
- **Animation states**: idle, walk
- **Directions**: up, down, left, right
- **Optional special animations**: appear, disappear, interact

**4-Directional Animation Properties:**

| Property | Type | Description |
| -------- | ---- | ----------- |
| `idle_up_frames`, `idle_down_frames`, `idle_left_frames`, `idle_right_frames` | int | Idle frames per direction |
| `idle_up_row`, `idle_down_row`, `idle_left_row`, `idle_right_row` | int | Row index per direction |
| `walk_up_frames`, `walk_down_frames`, `walk_left_frames`, `walk_right_frames` | int | Walk frames per direction |
| `walk_up_row`, `walk_down_row`, `walk_left_row`, `walk_right_row` | int | Row index per direction |

**Optional Special Animation Properties:**

| Property | Type | Description |
| -------- | ---- | ----------- |
| `appear_frames` | int | Number of frames for appear/disappear animation |
| `appear_row` | int | Row index for appear/disappear frames (same row used for both) |
| `interact_up_frames` | int | Number of frames for up-facing interact animation |
| `interact_up_row` | int | Row index for up-facing interact animation |
| `interact_down_frames` | int | Number of frames for down-facing interact animation |
| `interact_down_row` | int | Row index for down-facing interact animation |
| `interact_left_frames` | int | Number of frames for left-facing interact animation |
| `interact_left_row` | int | Row index for left-facing interact animation |
| `interact_right_frames` | int | Number of frames for right-facing interact animation |
| `interact_right_row` | int | Row index for right-facing interact animation |

**Note:**

- Specify only the animation properties you need for each direction. The framework will only load the specified animations.
- If `interact_left` is not specified but `interact_right` exists, the left animation will be auto-generated by flipping the right frames horizontally.

### Example NPC Setup

**Basic NPC with 4-directional animations:**

```text
Layer: NPCs
Object Type: Point
Position: (320, 240)

Custom Properties:
  name: "merchant"
  sprite_sheet: "images/characters/merchant.png"
  tile_size: 64
  idle_up_frames: 4
  idle_up_row: 0
  idle_down_frames: 4
  idle_down_row: 1
  idle_left_frames: 4
  idle_left_row: 2
  idle_right_frames: 4
  idle_right_row: 3
  walk_up_frames: 6
  walk_up_row: 4
  walk_down_frames: 6
  walk_down_row: 5
  walk_left_frames: 6
  walk_left_row: 6
  walk_right_frames: 6
  walk_right_row: 7
  initially_hidden: false
  dialog_level: 0
```

**NPC with special animations:**

```text
Layer: NPCs
Object Type: Point
Position: (640, 480)

Custom Properties:
  name: "wizard"
  sprite_sheet: "images/characters/wizard.png"
  tile_size: 64
  idle_down_frames: 4
  idle_down_row: 0
  walk_down_frames: 6
  walk_down_row: 1
  appear_frames: 9
  appear_row: 8
  interact_down_frames: 5
  interact_down_row: 9
  initially_hidden: true
```

### Multiple NPCs

You can have as many NPCs as you want on a single map:

```text
NPCs Layer:
  - Point named "merchant" at (320, 240)
  - Point named "guard" at (640, 480)
  - Point named "elder" at (800, 360)
  - Point named "child" at (200, 500)
```

Each NPC needs:

1. Unique `name` property
2. `sprite_sheet` property pointing to the sprite sheet file
3. Animation properties (idle/walk frames and rows for each direction you want to support)
4. Optional: Dialog entries in `assets/dialogs/{scene_name}_dialogs.json` if the NPC should be interactive

## Portals and Transitions

Portals are **Rectangle Objects** that trigger map transitions when the player enters them.

### Creating a Portal

1. Select the **Portals** object layer
2. Click **Insert Rectangle** (or press **R**)
3. Draw a rectangle where the portal zone should be
4. Set the portal's properties

### Required Portal Properties

| Property | Type | Description | Example |
| -------- | ---- | ----------- | ------- |
| `name` | string | Unique portal identifier | `"to_forest"` |
| `target_map` | string | Destination map file (relative to assets/maps/) | `"forest.tmx"` |

### Optional Portal Properties

| Property | Type | Description | Example |
| -------- | ---- | ----------- | ------- |
| `spawn_waypoint` | string | Waypoint name in destination map where player spawns | `"from_village"` |
| `condition_type` | string | Type of activation condition | `"npc_disappeared"` |
| `condition_value` | string | Value for the condition (e.g., NPC name) | `"guard"` |

### Example Portal Setup

**In village.tmx:**

```text
Layer: Portals
Object: Rectangle at map edge (64, 0, 32, 64)

Properties:
  name: "to_forest"
  target_map: "forest.tmx"
  spawn_waypoint: "from_village"
```

**In forest.tmx:**

```text
Layer: Waypoints
Object: Point at entrance (100, 200)

Properties:
  name: "from_village"
```

**Note:** If `spawn_waypoint` is not specified, the player will spawn at the default location in the target map.

### Conditional Portals

You can make portals that only activate when conditions are met.

**Available Condition Types:**

| Condition Type | Description | condition_value |
| -------------- | ----------- | --------------- |
| `npc_disappeared` | Portal activates after specified NPC completes disappear animation | NPC name |

**Example: Portal that opens after NPC disappears:**

```text
Properties:
  name: "to_castle"
  target_map: "castle.tmx"
  spawn_waypoint: "entrance"
  condition_type: "npc_disappeared"
  condition_value: "guard"
```

The player won't be able to use this portal until the NPC named "guard" has completed its disappear animation.

## Waypoints

Waypoints are **Point Objects** that define named positions on the map.

### Creating a Waypoint

1. Select the **Waypoints** object layer
2. Click **Insert Point** (or press **I**)
3. Click where you want the waypoint
4. Set the `name` property

### Waypoint Uses

| Use Case | Description |
| -------- | ----------- |
| **Portal destinations** | Target location for map transitions (used with portal `spawn_waypoint` property) |
| **NPC movement** | Destinations for pathfinding scripts |

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
  "type": "move_npc",
  "params": {
    "npc_name": "merchant",
    "waypoint": "well"
  }
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

| Property | Type | Required | Description | Example |
| -------- | ---- | -------- | ----------- | ------- |
| `name` | string | **Yes** | Unique identifier | `"treasure_chest"` |
| `interaction_type` | string | **Yes** | Interaction type | `"message"`, `"toggle"` |
| `message` | string | No | Text to display (for type="message") | `"Welcome to Riverside Village!"` |
| `title` | string | No | Dialog title (for type="message") | `"Village Sign"` |
| `state` | string | No | Initial state (for type="toggle") | `"off"` |

### Interaction Types

#### Message

Displays text in a dialog box when interacted with:

```text
Properties:
  name: "village_sign"
  interaction_type: "message"
  title: "Village Sign"
  message: "Welcome to Riverside Village!"
```

**Note:** If `title` is not specified, it defaults to "Info". If `message` is not specified, it defaults to "...".

#### Toggle

Toggles the object's state between "on" and "off":

```text
Properties:
  name: "secret_switch"
  interaction_type: "toggle"
  state: "off"
```

**How it works:**

- Each interaction toggles the `state` property between "on" and "off"
- The state change is logged and can be checked in game code
- Use this for switches, levers, buttons, and other two-state objects
- Game code can query the object's state to trigger visual changes or game logic

**Example usage in scripts:**

After the player interacts with the toggle, you can check its state and perform actions accordingly (e.g., opening doors, changing sprites, triggering events).

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

Built-in Properties:
  name: "quest_giver"
  sprite_sheet: "images/characters/elder.png"
  tile_size: 64
  idle_down_frames: 4
  idle_down_row: 0

Custom Properties:
  quest_id: "find_amulet"
  quest_stage: 1
  greeting_message: "Greetings, traveler!"
  relationship_level: 0
```

You can add any custom properties you need to objects. These properties are stored in the object's `properties` dictionary and can be accessed in your game code or scripts to implement custom behavior, track state, or configure object-specific settings.

## Resources

- [Tiled Documentation](https://doc.mapeditor.org/)
- [Arcade Tilemap Guide](https://api.arcade.academy/en/latest/api/tilemap.html)
- [Free Tilesets](https://opengameart.org/)
- [Tiled Forum](https://discourse.mapeditor.org/)

---

**Next Steps:**

- [Scripting Guide](scripting/index.md) - Learn about event-driven actions
- [Systems Reference](systems/index.md) - Deep dive into managers
- [API Reference](api-reference.md) - Complete API documentation
