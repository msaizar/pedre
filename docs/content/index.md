# Content Registry Reference

Pedre ships with built-in content types for the most common game data. Each type is loaded from a JSON file in your content directory and validated on startup.

## Built-in Content Types

| Type      | File / Directory    | Description                                        |
| --------- | ------------------- | -------------------------------------------------- |
| `sprites` | `sprites.json`      | Sprite sheet animation definitions                 |
| `npcs`    | `npcs.json`         | NPC definitions — sprite, scale, visibility        |
| `players` | `players.json`      | Player definitions — sprite and spawn positions    |
| `maps`    | `maps.json`         | Per-map overrides — music, camera behavior         |
| `items`   | `items.json`        | Inventory item definitions                         |
| `dialogs` | `dialogs/*.json`    | NPC dialog text, organised per scene               |

Click a type for the full schema and examples:

- [Sprites](sprites.md)
- [NPCs](npcs.md)
- [Players](players.md)
- [Maps](maps.md)
- [Items](items.md)
- [Dialogs](dialogs.md)

## Content Directory

All JSON files are loaded from a single directory, configured via `CONTENT_DIRECTORY` in `settings.py` (default: `data/content`, relative to your assets directory):

```text
assets/
  data/
    content/
      sprites.json
      npcs.json
      players.json
      maps.json
      items.json
      dialogs/
        village.json
        forest.json
```

## Accessing Content at Runtime

Content is accessed through `context.content_registry` in plugins and actions:

```python
sprites = context.content_registry.get_sub_registry("sprites")
if sprites:
    definition = sprites.get("player_idle")   # raises MissingDefinitionError if absent
    exists = sprites.has("player_idle")        # returns bool
    all_sprites = sprites.all()               # returns dict of all definitions
```

`get_sub_registry()` returns `None` if the type is not registered, so always check before using.

## Adding Custom Content Types

To define your own content types (enemies, quests, dialogue trees, etc.), see [Custom Content Types](../extending/custom-content.md).
