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
│   │   ├── dialogs/
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

- Project structure
- Required files and directories
- Asset file integrity
- Configuration validity

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
