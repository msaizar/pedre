# Pedre Documentation

Welcome to the **Pedre** documentation! Pedre is a Python RPG framework built on [Arcade](https://api.arcade.academy/) with seamless [Tiled](https://www.mapeditor.org/) map editor integration.

## What is Pedre?

Pedre provides everything you need to build Zelda-like RPG games with:

- **Tiled Map Integration** - Load .tmx maps with automatic layer detection
- **NPC Plugin** - Animated NPCs with dialog trees and pathfinding
- **Dialog Plugin** - Multi-page conversations with character names
- **Event-Driven Scripting** - JSON-based cutscenes and interactive sequences
- **Inventory Management** - Item collection and categorization
- **Portal Plugin** - Map transitions with conditional triggers
- **Save/Load Plugin** - Automatic game state persistence
- **Audio Management** - Background music and sound effects
- **Camera Plugin** - Smooth camera following with optional bounds
- **Particle Effects** - Visual feedback plugin for interactions

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

Configure your game settings with `settings.py` in your project root:

```python
SCREEN_WIDTH=1280
SCREEN_HEIGHT=720
WINDOW_TITLE="My RPG"
INITIAL_MAP="my_map.tmx"
```

## Documentation Overview

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Getting Started**

    ---

    Build your first RPG game with step-by-step tutorials

    [:octicons-arrow-right-24: Get started](getting-started.md)

-   :material-api:{ .lg .middle } **API Reference**

    ---

    Framework architecture and Python API reference

    [:octicons-arrow-right-24: API docs](api/index.md)

-   :material-cog:{ .lg .middle } **Plugins**

    ---

    Detailed documentation for all plugin classes

    [:octicons-arrow-right-24: Explore plugins](plugins/index.md)

-   :material-script-text:{ .lg .middle } **Scripting**

    ---

    Create event-driven cutscenes and interactive sequences

    [:octicons-arrow-right-24: Write scripts](scripting/index.md)

-   :material-map:{ .lg .middle } **Tiled Integration**

    ---

    Learn how to create maps in Tiled for your game

    [:octicons-arrow-right-24: Use Tiled](guides/tiled-integration.md)

-   :material-tune:{ .lg .middle } **Configuration**

    ---

    Configure framework settings and customize behavior

    [:octicons-arrow-right-24: Configure](guides/configuration.md)

-   :material-console:{ .lg .middle } **Command-Line Interface**

    ---

    Use the Pedre CLI to manage and extend your projects

    [:octicons-arrow-right-24: CLI Guide](guides/cli.md)

-   :material-puzzle:{ .lg .middle } **Extending Pedre**

    ---

    Add custom actions, events, conditions, and plugins

    [:octicons-arrow-right-24: Extend](extending/index.md)

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
