# Pedre

[![PyPI version](https://img.shields.io/pypi/v/pedre.svg)](https://pypi.org/project/pedre/)
[![Python](https://img.shields.io/pypi/pyversions/pedre.svg)](https://pypi.org/project/pedre/)
[![License](https://img.shields.io/github/license/msaizar/pedre.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-online-brightgreen)](https://msaizar.github.io/pedre/)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-261230)](https://github.com/astral-sh/ruff)

A Python RPG framework built on [Arcade](https://api.arcade.academy/) with seamless [Tiled](https://www.mapeditor.org/) map editor integration. Build Zelda-like games with dialog systems, NPC interactions, inventory management, and event-driven scripting.

## Features

- **Tiled Map Integration** - Load .tmx maps with automatic layer detection and object parsing
- **Event-Driven Scripting** - JSON-based cutscenes, triggers, conditions, and actions
- **NPC System** - Animated NPCs with dialog trees, pathfinding, and state management
- **Dialog System** - Multi-page conversations with character names and text reveal animation
- **Inventory System** - Item collection, categorization, and photo viewing
- **Portal System** - Map transitions with conditional triggers and waypoint spawning
- **Save/Load System** - Multi-slot game state persistence with auto-save
- **Pause Menu** - In-game overlay with save/load, new game, and resume options
- **Player Control** - Animated player sprite with 8-directional movement and collision
- **Camera System** - Smooth camera following with target switching and bounds
- **Audio System** - Background music and sound effects with volume control
- **Particle Effects** - Visual feedback for interactions (sparkles, hearts, trails, bursts)
- **Interaction System** - Distance-based object and NPC interaction detection
- **Physics System** - Collision detection with configurable wall layers
- **Pathfinding** - A* pathfinding for NPC movement around obstacles
- **Input Handling** - Normalized movement vectors with customizable key bindings
- **Debug Mode** - Development overlay showing coordinates and NPC states
- **Resource Caching** - Efficient loading and caching of sprites, audio, and maps

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

See the [Getting Started Guide](https://msaizar.github.io/pedre/getting-started/) for a complete step-by-step tutorial covering NPCs, dialogs, scripts, portals, and more.

## Demo Project

Want to see a complete working example? Check out **[msaizar/pedre-demo](https://github.com/msaizar/pedre-demo)** - a fully functional RPG demo showcasing the framework's features including NPCs, dialogs, inventory, portals, and scripted events.

## Architecture

Pedre uses a **plugin-based architecture** where plugins communicate via a central GameContext:

- **GameView** - Single view managing gameplay (pause menu and inventory are plugin overlays, not separate views)
- **GameContext** - Central coordinator providing plugins access to each other
- **EventBus** - Powers the event-driven scripting system (triggers and actions)
- **Plugins** - Modular, replaceable components for different game aspects
  - See [Plugin Reference](https://msaizar.github.io/pedre/plugins/) for complete list
- **Extensible scripting system** - Create custom actions, events, and conditions
- **Sprites** - AnimatedPlayer and AnimatedNPC with multi-directional sprite sheet support

All core plugins can be replaced or extended to customize your game's behavior.

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

# Run quality checks with fixes
just qa-fix

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
