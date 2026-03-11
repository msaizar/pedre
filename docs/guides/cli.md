# Command-Line Interface (CLI)

The Pedre CLI provides command-line utilities for managing and validating game projects.

## Overview

The Pedre CLI offers an extensible command system with automatic discovery. Commands can come from three sources:

1. **Framework commands** - Built-in commands in `pedre/commands/`
2. **Project commands** - User commands in `<project_root>/commands/`
3. **External packages** - Commands registered via entry points

## Built-in Commands

### `pedre init`

Initialize a new Pedre project with the recommended directory structure.

**Usage:**

```bash
pedre init [--path PATH]
```

**Options:**

- `--path PATH`, `-p PATH` - Project directory (default: current directory)

**What it creates:**

```text
my_game/
├── assets/
│   ├── audio/
│   │   ├── music/
│   │   └── sfx/
│   ├── data/
│   │   ├── content/
│   │   └── scripts/
│   ├── images/
│   └── maps/
├── main.py
└── settings.py
```

**Example:**

```bash
# Initialize in current directory
pedre init

# Initialize in specific directory
pedre init --path ./my-game
```

### `pedre validate`

Run validation checks on your Pedre project configuration and assets.

**Usage:**

```bash
pedre validate [options]
```

**What it checks:**

- Maps
- Items
- Sprites
- NPCs
- Players
- Scripts
- Dialogs

**Options:**

| Flag                  | Default                                    | Description                          |
| --------------------- | ------------------------------------------ | ------------------------------------ |
| `--maps-path PATH`    | `{ASSETS_DIR}/{MAPS_DIR}`                  | Path to maps directory (TMX files)   |
| `--items-path PATH`   | `{ASSETS_DIR}/{CONTENT_DIR}/items.json`    | Path to inventory items file         |
| `--sprites-path PATH` | `{ASSETS_DIR}/{CONTENT_DIR}/sprites.json`  | Path to sprites file                 |
| `--npcs-path PATH`    | `{ASSETS_DIR}/{CONTENT_DIR}/npcs.json`     | Path to NPCs file                    |
| `--players-path PATH` | `{ASSETS_DIR}/{CONTENT_DIR}/players.json`  | Path to players file                 |
| `--scripts-path PATH` | `{ASSETS_DIR}/{SCRIPTS_DIR}`               | Path to scripts directory            |
| `--dialogs-path PATH` | `{ASSETS_DIR}/{CONTENT_DIR}`               | Path to dialogs directory            |

Each validator is optional — it only runs when its default path exists or an explicit `--*-path` flag is provided.

**Examples:**

```bash
# Validate everything (uses defaults from settings.py)
pedre validate

# Validate only maps and scripts
pedre validate --maps-path assets/maps --scripts-path assets/data/scripts

# Validate with a non-standard content directory
pedre validate --npcs-path custom/npcs.json --sprites-path custom/sprites.json
```

Validation runs in two phases — structural checks first, then cross-reference checks (e.g. verifying that NPC names referenced in scripts exist in the map files). Exits with code `1` if any errors are found.

See [Validators API](../api/validators.md) for details on the underlying validation system.

## Installation Methods

### With uv (recommended)

```bash
# Run commands directly
uv run pedre init
uv run pedre validate

# Install as a tool
uv tool install pedre
pedre init
```

### With pip

```bash
# Install in editable mode
pip install -e .

# Run commands
pedre init
pedre validate
```

## Creating Custom Commands

The command system is extensible — you can add project-specific commands or distribute commands as installable packages.

See [Custom Commands](../extending/custom-commands.md) for a full guide covering project commands, external package entry points, the command base class, and best practices.

## See Also

- [Getting Started](../getting-started.md) - Initial project setup
- [Configuration Guide](configuration.md) - Project configuration
- [API Reference](../api/index.md) - Framework architecture
