# Pedre

A Python RPG framework built on [Arcade](https://api.arcade.academy/) with seamless [Tiled](https://www.mapeditor.org/) map editor integration. Build Zelda-like games with dialog systems, NPC interactions, inventory management, and event-driven scripting.

## Features

- **Tiled Map Integration** - Load .tmx maps with automatic layer detection and object parsing
- **NPC Plugin** - Animated NPCs with dialog trees, pathfinding, and state management
- **Dialog Plugin** - Multi-page conversations with character names and pagination
- **Event-Driven Scripting** - JSON-based cutscenes and interactive sequences
- **Inventory Management** - Item collection and categorization plugin
- **Portal Plugin** - Map transitions with conditional triggers
- **Save/Load Plugin** - Automatic game state persistence
- **Audio Management** - Background music and sound effects with caching
- **Camera Plugin** - Smooth camera following with optional bounds
- **Particle Effects** - Visual feedback plugin for interactions

## Requirements

- Python 3.14 or higher
- [Tiled Map Editor](https://www.mapeditor.org/) for creating game maps

## Installation

Install from PyPI:

```bash
pip install pedre
```

Or with uv:

```bash
uv add pedre
```

## Quick Start

```python
from pedre import run_game

if __name__ == "__main__":
    run_game()
```

This will start your game with the default configuration. Configure your game using `settings.py` in your project root:

```python
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
WINDOW_TITLE = "My RPG"
INITIAL_MAP = "my_map.tmx"
```

### Adding NPCs with Dialogs

Create a dialog file `assets/dialogs/village_dialogs.json` (where "village" matches your map name):

```json
{
  "merchant": {
    "0": {
      "name": "Merchant",
      "text": [
        "Welcome to my shop!",
        "Take a look around."
      ]
    }
  }
}
```

Place the NPC in your Tiled map's "NPCs" object layer as a point with these custom properties:

- `name` (string): "merchant" - unique identifier
- `sprite_sheet` (string): "images/characters/merchant.png" - path to sprite sheet
- `tile_size` (int): 32 - size of each tile in the sprite sheet
- Animation properties like `idle_down_frames`, `idle_down_row`, `walk_right_frames`, `walk_right_row`, etc.

See the [Getting Started Guide](https://msaizar.github.io/pedre/getting-started/) for complete NPC setup instructions.

### Creating Interactive Scripts

Create a script file `assets/scripts/village_scripts.json`:

```json
{
  "meet_merchant": {
    "scene": "village",
    "trigger": {
      "event": "npc_interacted",
      "npc": "merchant"
    },
    "actions": [
      {
        "type": "dialog",
        "speaker": "Merchant",
        "text": ["Welcome to my shop!", "Take a look around."]
      },
      {
        "type": "play_sfx",
        "file": "coin.wav"
      }
    ]
  }
}
```

### Adding Portals Between Maps

Portals use an event-driven system that gives you full control over transitions.

**In Tiled:**

1. Create a "Portals" object layer
2. Add a rectangle where you want the portal
3. Set the `name` property: "to_forest"
4. In the target map, create a "Waypoints" object layer with a point named "from_village"

**In your scripts file** (`assets/scripts/village_scripts.json`):

```json
{
  "to_forest_portal": {
    "trigger": {"event": "portal_entered", "portal": "to_forest"},
    "actions": [
      {"type": "change_scene", "target_map": "forest.tmx", "spawn_waypoint": "from_village"}
    ]
  }
}
```

This event-driven approach allows conditional portals, cutscenes before transitions, and locked doors with custom failure messages. See the [Portal Plugin](https://msaizar.github.io/pedre/plugins/portal/) and [Scripting Guide](https://msaizar.github.io/pedre/scripting/) for more details.

## Demo Project

Want to see a complete working example? Check out **[msaizar/pedre-demo](https://github.com/msaizar/pedre-demo)** - a fully functional RPG demo showcasing the framework's features including NPCs, dialogs, inventory, portals, and scripted events.

## Architecture

The framework uses a **plugin-based architecture** with event-driven communication:

- **Views** - Menu, Game, Inventory, Load screens
- **Sprites** - AnimatedPlayer, AnimatedNPC with sprite sheet support
- **Plugins** - Modular plugins for different game aspects:
  - DialogPlugin - Conversation display
  - NPCPlugin - NPC state and interactions
  - PortalPlugin - Map transitions
  - ScriptPlugin - Event-driven actions
  - InventoryPlugin - Item management
  - AudioPlugin - Sound and music
  - SavePlugin - Game persistence
  - And more...

## Development

Want to contribute or run from source?

```bash
# Clone the repository
git clone https://github.com/msaizar/pedre.git
cd pedre

# Install with dev dependencies
uv sync

# Run quality checks
just qa

# Run tests
just test
```

This project uses modern Python tooling:

- **uv** - Fast Python package manager
- **ruff** - Linter and formatter
- **ty** - Type checker
- **pytest** - Testing framework
- **just** - Command runner

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## Documentation

Full documentation is available at **[msaizar.github.io/pedre](https://msaizar.github.io/pedre/)**

Key guides:

- [Getting Started](https://msaizar.github.io/pedre/getting-started/) - Step-by-step tutorial
- [Configuration](https://msaizar.github.io/pedre/guides/configuration/) - Settings and customization
- [Tiled Integration](https://msaizar.github.io/pedre/guides/tiled-integration/) - Creating maps in Tiled
- [Scripting System](https://msaizar.github.io/pedre/scripting/) - Event-driven gameplay
- [Plugin Reference](https://msaizar.github.io/pedre/plugins/) - Complete plugin documentation
- [API Reference](https://msaizar.github.io/pedre/api/) - Python API docs

## License

BSD 3-Clause License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting pull requests.

## Credits

Built with:

- [Python Arcade](https://api.arcade.academy/) - 2D game framework
- [Tiled Map Editor](https://www.mapeditor.org/) - Level design tool
