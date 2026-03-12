# Custom Content Types

Pedre's content registry system lets you define your own JSON-driven game data that integrates seamlessly with the framework's loading and validation lifecycle. For the built-in content types (sprites, NPCs, players, maps, items), see the [Content Registry Reference](../content/index.md).

## How Content Is Loaded

When the game initializes, `ContentLoader` imports each module listed in `INSTALLED_CONTENT`. This triggers `@ContentTypeRegistry.register` decorators to execute, registering each content type with the global `ContentTypeRegistry`. Once that is done, `ContentRegistry()` creates instances of all registered sub-registries and loads their JSON files from the content directory.

```text
ContentLoader.load_modules()
    → imports pedre.content.registries.sprite  → SpriteRegistry registered
    → imports pedre.content.registries.npc     → NPCRegistry registered
    → imports myproject.content.enemies        → EnemyRegistry registered

ContentRegistry()
    → creates SpriteRegistry instance, loads sprites.json
    → creates NPCRegistry instance, loads npcs.json
    → creates EnemyRegistry instance, loads enemies.json

ContentRegistry.validate_cross_references()
    → validates all inter-type references
```

### INSTALLED_CONTENT Setting

Modules are configured through the `INSTALLED_CONTENT` setting:

```python
INSTALLED_CONTENT = [
    "pedre.content.registries.npc",
    "pedre.content.registries.sprite",
    "pedre.content.registries.item",
]
```

To add your own types, extend the list in your `settings.py`:

```python
from pedre.conf import global_settings

INSTALLED_CONTENT = [
    *global_settings.INSTALLED_CONTENT,  # Include built-in types
    "myproject.content.enemies",          # Your custom content types
]
```

## Creating Custom Content Types

### 1. Define the Registry Class

Subclass `BaseContentRegistry` and decorate it with `@ContentTypeRegistry.register`:

```python
# myproject/content/enemies.py
from typing import Any, ClassVar

from pedre.content.registry import (
    BaseContentRegistry,
    ContentRegistry,
    ContentTypeRegistry,
    InvalidDefinitionError,
)


@ContentTypeRegistry.register
class EnemyRegistry(BaseContentRegistry):
    """Registry for enemy definitions."""

    name: ClassVar[str] = "enemies"
    filename: ClassVar[str] = "enemies.json"
    display_name: ClassVar[str] = "Enemy"

    def validate(self, definition_id: str, definition: dict[str, Any]) -> None:
        """Validate a single enemy definition."""
        for field in ("name", "health", "sprite_id"):
            if field not in definition:
                msg = f"Enemy '{definition_id}' missing required field '{field}'."
                raise InvalidDefinitionError(msg)

        if not isinstance(definition["health"], int) or definition["health"] <= 0:
            msg = f"Enemy '{definition_id}' field 'health' must be a positive integer."
            raise InvalidDefinitionError(msg)

    def validate_cross_references(self, content_registry: ContentRegistry) -> None:
        """Ensure each enemy's sprite_id references a valid sprite."""
        sprites = content_registry.get_sub_registry("sprites")
        if sprites is None:
            return
        for enemy_id, enemy_def in self.all().items():
            sprite_id = enemy_def["sprite_id"]
            if not sprites.has(sprite_id):
                msg = f"Enemy '{enemy_id}' references unknown sprite '{sprite_id}'."
                raise InvalidDefinitionError(msg)
```

### 2. Create the JSON File

Place `enemies.json` in your content directory (default: `assets/data/content/`):

```json
{
  "goblin": {
    "name": "Goblin",
    "health": 30,
    "sprite_id": "goblin_idle",
    "speed": 60
  },
  "orc": {
    "name": "Orc",
    "health": 80,
    "sprite_id": "orc_idle",
    "speed": 40
  }
}
```

### 3. Register in Settings

```python
# settings.py
from pedre.conf import global_settings

INSTALLED_CONTENT = [
    *global_settings.INSTALLED_CONTENT,
    "myproject.content.enemies",
]
```

### 4. Access in Plugins

```python
enemies = context.content_registry.get_sub_registry("enemies")
if enemies:
    goblin_def = enemies.get("goblin")
    goblin_health = goblin_def["health"]
```

## Validation

The registry calls two validation hooks at different points:

### `validate(definition_id, definition)`

Called once per definition when loading from JSON (inside `load_from_file`). Use this to check required fields, field types, and internal consistency of a single definition.

```python
def validate(self, definition_id: str, definition: dict[str, Any]) -> None:
    if "name" not in definition:
        msg = f"Enemy '{definition_id}' missing required field 'name'."
        raise InvalidDefinitionError(msg)
```

### `validate_cross_references(content_registry)`

Called once after all sub-registries are populated, allowing you to validate references to other content types. Use this when one type depends on IDs from another type.

```python
def validate_cross_references(self, content_registry: ContentRegistry) -> None:
    sprites = content_registry.get_sub_registry("sprites")
    if sprites is None:
        return
    for enemy_id, enemy_def in self.all().items():
        if not sprites.has(enemy_def["sprite_id"]):
            msg = f"Enemy '{enemy_id}' references unknown sprite '{enemy_def['sprite_id']}'."
            raise InvalidDefinitionError(msg)
```

## Error Types

| Exception                | When Raised                                    |
|--------------------------|------------------------------------------------|
| `RegistryError`          | Base class for all registry errors             |
| `DuplicateIDError`       | Registering an ID that already exists          |
| `MissingDefinitionError` | Calling `.get()` with an ID that doesn't exist |
| `InvalidDefinitionError` | A definition fails validation                  |

All exceptions are importable from `pedre.content.registry`.

## Configuration

| Setting             | Type   | Default          | Description                                              |
|---------------------|--------|------------------|----------------------------------------------------------|
| `INSTALLED_CONTENT` | list   | Built-in types   | Modules to import for content type registration          |
| `CONTENT_DIRECTORY` | string | `"data/content"` | Content JSON directory, relative to the assets directory |

## Best Practices

### Naming

- Registry `name` should be plural and lowercase (e.g., `"enemies"`, `"quests"`)
- `filename` should match `name` with `.json` extension (e.g., `"enemies.json"`)
- `display_name` should be singular for readable error messages (e.g., `"Enemy"`)

### Validation

- Validate all required fields in `validate()` — fail fast with clear messages
- Use `validate_cross_references()` only for inter-type references, not field validation
- Always guard against `None` when calling `get_sub_registry()` in cross-reference validation

### Module Structure

Keep each content type in its own module for clarity:

```text
myproject/
    content/
        __init__.py
        enemies.py    # EnemyRegistry
        quests.py     # QuestRegistry
```

## See Also

- [Content Registry Reference](../content/index.md) — built-in content type schemas
- [Custom Actions](custom-actions.md) — script actions that consume content
- [Custom Plugins](custom-plugins.md) — plugins that use content at runtime
- [Configuration Guide](../guides/configuration.md) — full settings reference
