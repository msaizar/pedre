# Getting Started with Arcade Tiled RPG

This guide will walk you through creating your first RPG game using the Arcade Tiled RPG framework. By the end, you'll have a simple game with a player character, an NPC, dialog system, and map transitions.

## Prerequisites

Before starting, make sure you have:

- Python 3.14 or higher installed
- [uv](https://docs.astral.sh/uv/) package manager
- [Tiled Map Editor](https://www.mapeditor.org/) (free and open source)
- Basic knowledge of Python and object-oriented programming

## Step 1: Project Setup

### Install Pedre

```bash
# Create a new project directory
mkdir my-rpg
cd my-rpg

# Initialize uv project
uv init

# Install pedre package
uv add pedre
```

### Example Project Structure

```text
my-rpg/
├── assets/
│   ├── data/inventory-items.json
│   ├── maps/           # Tiled .tmx files
│   ├── images/
│   │   └── characters/ # Sprite sheets
│   ├── audio/
│   │   ├── music/      # Background music
│   │   └── sfx/        # Sound effects
│   ├── dialogs/        # NPC dialog JSON files
│   └── scripts/        # Event scripts JSON files
└── main.py             # Your game entry point
```

## Step 2: Create Your First Map

### In Tiled Map Editor

1. **Create a new map:**
    - File → New → New Map
    - Orientation: Orthogonal
    - Tile size: 32×32 pixels
    - Map size: 25×20 tiles (800×640 pixels)

2. **Create a tileset:**
    - Map → New Tileset
    - Name: "terrain"
    - Image: Use any 32×32 tileset (you can find free ones at [itch.io](https://itch.io/game-assets/free/tag-tileset))
    - Tile width/height: 32×32

3. **Add required layers:**

    Create these layers (Layer → New Layer):

    **Tile Layers:**

    - `Floor` - Ground tiles (draw your terrain here)
    - `Walls` - Wall tiles that block movement

    **Object Layers:**

    - `Player` - Player spawn point
    - `NPCs` - NPC spawn points
    - `Portals` - Map transition zones
    - `Waypoints` - Named positions for scripting

4. **Draw your map:**
    - Select the Floor layer
    - Use the tileset to paint ground tiles
    - Select the Walls layer
    - Paint walls around the perimeter

5. **Add player spawn point:**
    - Select the Player object layer
    - Insert → Point
    - Click somewhere in the center of your map (e.g., at 400, 320)
    - In the Properties panel, add custom properties:
        - `sprite_sheet` (string): `images/characters/player.png`
        - `tile_size` (int): `64`
        - `idle_up_frames` (int): `4`
        - `idle_up_row` (int): `0`
        - `idle_down_frames` (int): `4`
        - `idle_down_row` (int): `1`
        - `idle_right_frames` (int): `4`
        - `idle_right_row` (int): `2`
        - `walk_up_frames` (int): `6`
        - `walk_up_row` (int): `4`
        - `walk_down_frames` (int): `6`
        - `walk_down_row` (int): `5`
        - `walk_right_frames` (int): `6`
        - `walk_right_row` (int): `6`
        - `spawn_at_portal` (bool): `false` (optional - if true, player spawns at portal waypoints instead of this position)

6. **Save your map:**
    - File → Save As
    - Save as `assets/maps/village.tmx`

**Note:** You'll need a player sprite sheet at `assets/images/characters/player.png`. The framework expects a sprite sheet with animation frames arranged in rows (idle, walk, etc.). Adjust the frame counts and row indices to match your sprite sheet layout.

**Spawn Behavior:** By default (`spawn_at_portal: false`), the player spawns at this object's position. Set `spawn_at_portal: true` if you want the player to only spawn at portal waypoints (useful for maps that are always entered via portals).

## Step 3: Create a Simple Game

Create a new file `main.py` in your project root:

```python
"""Simple RPG game using Pedre framework."""

from pedre import run_game

if __name__ == "__main__":
    run_game()
```

Configure your game settings in `main.py`:

```python
"""Simple RPG game using Pedre framework."""

from pedre import run_game, GameSettings

# Configure game settings
settings = GameSettings(
    screen_width=1280,
    screen_height=720,
    window_title="My First RPG",
    initial_map="village.tmx"
)

if __name__ == "__main__":
    run_game(settings)
```

The scene name is automatically derived from the map filename (e.g., `village.tmx` → scene name `"village"`).

### Run Your Game

```bash
uv run python main.py
```

You should see your map with a player character! Use arrow keys to move around.

The `run_game()` function automatically:

- Creates the game window with your configured settings
- Loads the initial map from `assets/maps/`
- Sets up all game systems (NPCs, dialogs, scripts, etc.)
- Starts the game loop

## Step 4: Add an NPC

### Create NPC Sprite Sheet

For this tutorial, you'll need a character sprite sheet. The framework is flexible and works with various sprite sheet layouts:

- **Tile size**: Any consistent size (16×16, 32×32, 64×64, etc.)
- **Frames**: Any number of frames per animation
- **Rows**: Animations arranged in horizontal rows
- **Direction**: Only right-facing animations needed (left-facing auto-generated by flipping)

You can create your own or download free sprites from [OpenGameArt.org](https://opengameart.org/).

Save your NPC sprite sheet as `assets/images/characters/merchant.png`.

**Example sprite sheet layout:**

- Row 0: Idle animation frames (e.g., 4 frames)
- Row 1: Walk animation frames (e.g., 6 frames)
- Additional rows can contain other animations like interact or appear

### Add NPC to Tiled Map

1. Open `village.tmx` in Tiled
2. Select the NPCs object layer
3. Insert → Point (or press I)
4. Click where you want the NPC to spawn
5. In the Properties panel for this object, add custom properties:
      - `name` (string): `merchant`
      - `sprite_sheet` (string): `images/characters/merchant.png`
      - `tile_size` (int): `32`
      - `idle_up_frames` (int): `4`
      - `idle_up_row` (int): `0`
      - `idle_down_frames` (int): `4`
      - `idle_down_row` (int): `1`
      - `idle_right_frames` (int): `4`
      - `idle_right_row` (int): `2`
      - `walk_up_frames` (int): `6`
      - `walk_up_row` (int): `4`
      - `walk_down_frames` (int): `6`
      - `walk_down_row` (int): `5`
      - `walk_right_frames` (int): `6`
      - `walk_right_row` (int): `6`

6. Save the map

**Note:** The NPC will spawn at the exact x,y coordinates of the point object. The `sprite_sheet` property tells the framework which character sprite sheet to load, and the animation properties define how many frames and which rows to use for idle and walking animations.

### Create NPC Dialog

Create `assets/dialogs/village_dialogs.json`:

```json
{
  "merchant": {
    "0": {
      "name": "Merchant",
      "text": [
        "Hello, traveler!",
        "Welcome to our village.",
        "Feel free to look around."
      ]
    },
    "1": {
      "name": "Merchant",
      "text": [
        "Back again?",
        "I have nothing new to say."
      ]
    }
  }
}
```

**Dialog Structure:**

- Top-level keys are NPC names
- Second-level keys are dialog levels (conversation progress)
- `name` - NPC name displayed in dialog box
- `text` - Array of text strings (press SPACE to advance)

### Test NPC Interaction

Run your game again:

```bash
uv run python main.py
```

Walk up to the NPC and press SPACE. You should see the dialog appear! Press SPACE to advance through pages.

## Step 5: Add Interactive Scripts

Scripts let you trigger actions when events occur. Let's make the NPC give the player a sound effect after the first conversation.

### Create Script File

Create `assets/scripts/village_scripts.json`:

```json
{
  "first_meeting": {
    "scene": "village",
    "trigger": {
      "event": "dialog_closed",
      "npc": "merchant",
      "dialog_level": 0
    },
    "run_once": true,
    "actions": [
      {
        "type": "advance_dialog",
        "npc": "merchant"
      },
      {
        "type": "play_sfx",
        "file": "greeting.wav"
      }
    ]
  }
}
```

**Script Breakdown:**

- `scene`: Only runs in the "village" scene
- `trigger.event`: Trigger when dialog closes
- `trigger.npc`: Only if NPC is "merchant"
- `trigger.dialog_level`: Only at dialog level 0
- `run_once`: Only execute this script once
- `actions`: Sequence of actions to execute:
    1. Advance merchant's dialog level by 1 (so next conversation uses level 1 dialog)
    2. Play a sound effect

### Add Sound Effect (Optional)

If you have a sound file, place it in `assets/audio/sfx/greeting.wav`. Otherwise, remove the `play_sfx` action from the script.

### Test Scripts

Run the game and talk to the merchant. After closing the first dialog, the script will run and increment the merchant's dialog level. Talk to them again and you'll see the level 1 dialog!

## Step 6: Add Map Transitions

Let's create a second map and a portal to travel between them.

### Create Second Map

1. In Tiled, create a new map: `assets/maps/forest.tmx`
2. Use the same settings as before (32×32 tiles, 25×20 map)
3. Add the same layers: Floor, Walls, NPCs, Portals, Waypoints
4. Paint some terrain (make it look different from the village)
5. Select the Waypoints object layer
6. Insert → Point (or press I)
7. Click where you want the player to spawn when entering from village
8. In Properties panel, set Name: `from_village`
9. Save the map

### Add Waypoint in Village Map

1. Open `assets/maps/village.tmx`
2. Select the Waypoints object layer (create it if it doesn't exist)
3. Insert → Point (or press I)
4. Click where you want the player to spawn when returning from forest
5. In Properties panel, set Name: `from_forest`
6. Save the map

### Add Portal in Village Map

1. Still in `assets/maps/village.tmx`
2. Select the Portals object layer
3. Insert → Insert Rectangle
4. Draw a rectangle at the edge of your map (this is the portal zone)
5. In Properties panel:
      - Set Name: `to_forest`
      - Add custom property `target_map` (string): `forest.tmx`
      - Add custom property `spawn_waypoint` (string): `from_village`
6. Save the map

### Add Return Portal in Forest Map

1. Open `assets/maps/forest.tmx`
2. Select the Portals object layer
3. Insert → Insert Rectangle
4. Draw a rectangle where you want the return portal
5. In Properties panel:
      - Set Name: `to_village`
      - Add custom property `target_map` (string): `village.tmx`
      - Add custom property `spawn_waypoint` (string): `from_forest`
6. Save the map

### Test Portals

Run the game and walk into the portal rectangle. You should transition to the forest map! Walk into the return portal to go back.

The framework automatically:

- Detects portal collisions
- Saves your game state
- Loads the new map
- Spawns the player at the target waypoint

## Step 7: Add Inventory Items

The inventory system allows you to define collectible items and track their acquisition. Items are defined in a JSON file and can be collected through interactive objects or scripts.

### Define Inventory Items

Create `assets/data/inventory_items.json` to define all collectible items:

```json
{
  "items": [
    {
      "id": "golden_key",
      "name": "Golden Key",
      "description": "A mysterious golden key found in the forest.",
      "icon_path": "images/items/golden_key_icon.png",
      "category": "key_items",
      "acquired": false
    },
    {
      "id": "forest_photo",
      "name": "Forest Photo",
      "description": "A beautiful photo of the forest clearing.",
      "icon_path": "images/photos/forest_thumb.png",
      "image_path": "images/photos/forest.jpg",
      "category": "photos",
      "acquired": false
    }
  ]
}
```

**Item Fields:**

- `id` (required): Unique identifier for the item
- `name` (required): Display name shown in inventory
- `description` (required): Item description text
- `icon_path` (optional): Path to inventory icon/thumbnail image
- `image_path` (optional): Path to full-size image for viewable items (e.g., photos, documents)
- `category` (optional): Category for organization (default: "general")
- `acquired` (optional): Whether item starts collected (default: false)

The inventory system automatically loads this file on startup. Items with `image_path` can be clicked in the inventory to view the full image.

### Add Interactive Object in Tiled

1. Open `assets/maps/forest.tmx`
2. Create a new Object Layer named `Interactive`
3. Insert → Insert Rectangle
4. Draw a small rectangle where the item should be
5. In Properties panel:
      - Set Name: `treasure_chest`
      - Add custom property `type` (string): `item`
      - Add custom property `item_name` (string): `golden_key`
      - Add custom property `message` (string): `You found a Golden Key!`
6. Save the map

### Create Collection Script

Add to `assets/scripts/forest_scripts.json`:

```json
{
  "collect_key": {
    "scene": "forest",
    "trigger": {
      "event": "object_interacted",
      "object_name": "treasure_chest"
    },
    "run_once": true,
    "actions": [
      {
        "type": "dialog",
        "speaker": "Info",
        "text": ["You found a Golden Key!"]
      },
      {
        "type": "play_sfx",
        "file": "chest_open.wav"
      },
      {
        "type": "emit_particles",
        "particle_type": "sparkles",
        "x": 500,
        "y": 400
      }
    ]
  }
}
```

### View Inventory

Run the game, go to the forest, and interact with the treasure chest (press SPACE near it). Then press **I** to open the inventory and see your collected item!

## Step 8: Advanced: NPC Movement

Let's make an NPC walk to different locations.

### Add Waypoints

1. Open `assets/maps/village.tmx`
2. Select the Waypoints object layer
3. Add three points:
      - Name: `market_spot` (somewhere in the map)
      - Name: `well_spot` (another location)
      - Name: `home_spot` (another location)
4. Save the map

### Create Movement Script

Add to `assets/scripts/village_scripts.json`:

```json
{
  "merchant_to_market": {
    "scene": "village",
    "trigger": {
      "event": "npc_movement_complete",
      "npc": "merchant",
      "waypoint": "merchant_start"
    },
    "actions": [
      {
        "type": "move_npc",
        "npcs": ["merchant"],
        "waypoint": "market_spot"
      }
    ]
  },
  "merchant_to_well": {
    "scene": "village",
    "trigger": {
      "event": "npc_movement_complete",
      "npc": "merchant",
      "waypoint": "market_spot"
    },
    "actions": [
      {
        "type": "move_npc",
        "npcs": ["merchant"],
        "waypoint": "well_spot"
      }
    ]
  },
  "merchant_to_home": {
    "scene": "village",
    "trigger": {
      "event": "npc_movement_complete",
      "npc": "merchant",
      "waypoint": "well_spot"
    },
    "actions": [
      {
        "type": "move_npc",
        "npcs": ["merchant"],
        "waypoint": "home_spot"
      }
    ]
  }
}
```

The NPC will walk between the three waypoints in a loop. Each script triggers when the NPC completes movement to the previous waypoint. The framework uses A* pathfinding to navigate around walls!

## Next Steps

Congratulations! You've created your first RPG with:

- ✅ Custom Tiled maps
- ✅ Player movement and collision
- ✅ NPCs with dialog systems
- ✅ Event-driven scripting
- ✅ Map transitions with portals
- ✅ Collectible items and inventory
- ✅ NPC pathfinding and movement

### Learn More

- [Systems Reference](systems/index.md) - Deep dive into each manager
- [Tiled Integration](tiled-integration.md) - Advanced Tiled features
- [Scripting Guide](scripting/index.md) - All available actions and events
- [API Reference](api-reference.md) - Complete API documentation

Happy game dev! 🎮
