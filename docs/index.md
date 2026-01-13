# Pedre Documentation

Welcome to the **Pedre** documentation! Pedre is a Python RPG framework built on [Arcade](https://api.arcade.academy/) with seamless [Tiled](https://www.mapeditor.org/) map editor integration.

## What is Pedre?

Pedre provides everything you need to build Zelda-like RPG games with:

- **Tiled Map Integration** - Load .tmx maps with automatic layer detection
- **NPC System** - Animated NPCs with dialog trees and pathfinding
- **Dialog System** - Multi-page conversations with character names
- **Event-Driven Scripting** - JSON-based cutscenes and interactive sequences
- **Inventory Management** - Item collection and categorization
- **Portal System** - Map transitions with conditional triggers
- **Save/Load System** - Automatic game state persistence
- **Audio Management** - Background music and sound effects
- **Camera System** - Smooth camera following with optional bounds
- **Particle Effects** - Visual feedback system for interactions

## Installation

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

Configure your game settings with `GameSettings`:

```python
from pedre import run_game, GameSettings

settings = GameSettings(
    screen_width=1280,
    screen_height=720,
    window_title="My RPG",
    initial_map="my_map.tmx"
)

if __name__ == "__main__":
    run_game(settings)
```

## Documentation Overview

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Getting Started**

    ---

    Build your first RPG game with step-by-step tutorials

    [:octicons-arrow-right-24: Get started](getting-started.md)

-   :material-cog:{ .lg .middle } **Systems**

    ---

    Detailed documentation for all manager classes

    [:octicons-arrow-right-24: Explore systems](systems/index.md)

-   :material-map:{ .lg .middle } **Tiled Integration**

    ---

    Learn how to create maps in Tiled for your game

    [:octicons-arrow-right-24: Use Tiled](tiled-integration.md)

-   :material-script-text:{ .lg .middle } **Scripting**

    ---

    Create event-driven cutscenes and interactive sequences

    [:octicons-arrow-right-24: Write scripts](scripting/index.md)

-   :material-tune:{ .lg .middle } **Configuration**

    ---

    Configure framework settings and customize behavior

    [:octicons-arrow-right-24: Configure](configuration.md)

-   :material-api:{ .lg .middle } **API Reference**

    ---

    Complete reference for all classes and methods

    [:octicons-arrow-right-24: API docs](api-reference.md)

</div>

## Resources

- **GitHub Repository**: [msaizar/pedre](https://github.com/msaizar/pedre)
- **PyPI Package**: [pypi.org/project/pedre](https://pypi.org/project/pedre/)
- **Issue Tracker**: [GitHub Issues](https://github.com/msaizar/pedre/issues)
- **License**: BSD 3-Clause

## Credits

Built with:

- [Python Arcade](https://api.arcade.academy/) - 2D game framework
- [Tiled Map Editor](https://www.mapeditor.org/) - Level design tool
