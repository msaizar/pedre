# Pedre

A Python RPG framework built on [Arcade](https://api.arcade.academy/) with seamless [Tiled](https://www.mapeditor.org/) map editor integration. Build Zelda-like games with dialog systems, NPC interactions, inventory management, and event-driven scripting.

## Features

- **Tiled Map Integration** - Load .tmx maps with automatic layer detection and object parsing
- **NPC System** - Animated NPCs with dialog trees, pathfinding, and state management
- **Dialog System** - Multi-page conversations with character names and pagination
- **Event-Driven Scripting** - JSON-based cutscenes and interactive sequences
- **Inventory Management** - Item collection and categorization system
- **Portal System** - Map transitions with conditional triggers
- **Save/Load System** - Automatic game state persistence
- **Audio Management** - Background music and sound effects with caching
- **Camera System** - Smooth camera following with optional bounds
- **Particle Effects** - Visual feedback system for interactions

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

This will start your game with the default configuration. Configure your game using `GameSettings`:

```python
from pedre import run_game, GameSettings

# Create settings directly
settings = GameSettings(
    screen_width=1280,
    screen_height=720,
    window_title="My RPG",
    initial_map="my_map.tmx"
)

if __name__ == "__main__":
    run_game(settings)
```

### Adding NPCs with Dialogs

Create a dialog file `assets/dialogs/village_dialogs.json`:

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

Place the NPC in your Tiled map's "NPCs" layer with custom properties:

- `name`: "merchant"
- NPC sprite will be automatically loaded and animated

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

In Tiled, create a "Portals" object layer and add a rectangle with properties:

- `name`: "to_forest"
- `target_map`: "forest.tmx"
- `spawn_waypoint`: "from_village"

Create a matching waypoint in the target map's "Waypoints" layer (Point object named "from_village") where the player should spawn.

The framework automatically handles transitions when the player enters the portal zone.

## Architecture

The framework uses a **manager-based architecture** with event-driven communication:

- **Views** - Menu, Game, Inventory, Load screens
- **Sprites** - AnimatedPlayer, AnimatedNPC with sprite sheet support
- **Systems** - Modular managers for different game aspects:
  - DialogManager - Conversation display
  - NPCManager - NPC state and interactions
  - PortalManager - Map transitions
  - ScriptManager - Event-driven actions
  - InventoryManager - Item management
  - AudioManager - Sound and music
  - SaveManager - Game persistence
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

## License

BSD 3-Clause License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) before submitting pull requests.

## Credits

Built with:

- [Python Arcade](https://api.arcade.academy/) - 2D game framework
- [Tiled Map Editor](https://www.mapeditor.org/) - Level design tool
