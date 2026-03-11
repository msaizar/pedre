# Validators

Pedre includes a two-phase validation system for all game assets. It is invoked automatically by `pedre validate` and can also be called programmatically.

## Two-Phase Validation

Validation runs in two sequential phases:

1. **Phase 1 — Structural validation**: Each validator reads its asset file(s) and checks for correctness (valid JSON, required fields, known action/event/condition names). During this phase validators also populate the shared `ValidationContext` with entity information.

2. **Phase 2 — Cross-reference validation**: Validators use the populated context to verify that references between assets are valid (e.g. a script that targets NPC "alice" confirms "alice" exists in the referenced map).

## Built-in Validators

| Validator           | `name`    | Validates                                    |
| ------------------- | --------- | -------------------------------------------- |
| `MapValidator`      | `Maps`    | TMX map files in the maps directory          |
| `ItemValidator`     | `Items`   | `items.json` inventory item definitions      |
| `SpriteValidator`   | `Sprites` | `sprites.json` sprite animation definitions  |
| `NPCValidator`      | `NPCs`    | `npcs.json` NPC definitions                  |
| `PlayerValidator`   | `Players` | `players.json` player definitions            |
| `ScriptValidator`   | `Scripts` | JSON script files in the scripts directory   |
| `DialogValidator`   | `Dialogs` | JSON dialog files in the content directory   |

## API Reference

### `ValidationResult`

```python
from pedre.validators import ValidationResult
```

Returned by both `validate()` and `validate_cross_references()`.

```python
@dataclass
class ValidationResult:
    errors: list[str]       # Error messages found during validation
    item_count: int         # Number of items validated
    metadata: dict[str, int]  # Additional metrics (action counts, etc.)
```

A result with an empty `errors` list means validation passed.

### `Validator`

```python
from pedre.validators import Validator
```

Abstract base class for all validators.

```python
class Validator(ABC):
    def __init__(self, path: Path, context: ValidationContext) -> None: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def validate(self) -> ValidationResult: ...

    @abstractmethod
    def validate_cross_references(self) -> ValidationResult: ...
```

**Constructor arguments:**

- `path` — `Path` to the file or directory to validate
- `context` — shared `ValidationContext` instance passed to all validators in the same run

### `ValidationContext`

```python
from pedre.validators.context import ValidationContext
```

Shared dataclass populated during Phase 1 and read during Phase 2.

**Fields:**

| Field                | Type                                               | Description                                   |
| -------------------- | -------------------------------------------------- | --------------------------------------------- |
| `map_entities`       | `dict[str, dict[str, set[str]]]`                   | map name → entity type → entity names         |
| `script_references`  | `dict[str, set[EntityReference]]`                  | script name → referenced entities             |
| `dialog_references`  | `dict[tuple[str, str, str], set[EntityReference]]` | dialog key → referenced entities              |
| `inventory_items`    | `set[str]`                                         | known inventory item IDs                      |
| `sprite_ids`         | `set[str]`                                         | known sprite definition IDs                   |
| `npc_ids`            | `set[str]`                                         | known NPC definition IDs                      |
| `player_ids`         | `set[str]`                                         | known player definition IDs                   |

**Map entity methods:**

```python
context.add_map_entity(map_name, entity_type, entity_name)
# entity_type is one of: "npcs", "waypoints", "portals", "interactive_objects"

context.get_map_npcs(map_name)               # -> set[str]
context.get_map_waypoints(map_name)          # -> set[str]
context.get_map_portals(map_name)            # -> set[str]
context.get_map_interactive_objects(map_name) # -> set[str]

context.get_all_npcs()                       # -> set[str] across all maps
context.get_all_waypoints()                  # -> set[str] across all maps
context.get_all_portals()                    # -> set[str] across all maps
context.get_all_interactive_objects()        # -> set[str] across all maps
context.get_all_maps()                       # -> set[str] of all map names
```

**Content registration methods:**

```python
context.add_inventory_item(item_id)
context.get_inventory_items()   # -> set[str]

context.add_sprite_id(sprite_id)
context.get_sprite_ids()        # -> set[str]

context.add_npc_id(npc_id)
context.get_npc_ids()           # -> set[str]

context.add_player_id(player_id)
context.get_player_ids()        # -> set[str]
```

## Writing a Custom Validator

Subclass `Validator` and implement the three abstract members:

```python
from pathlib import Path
from pedre.validators import ValidationResult, Validator
from pedre.validators.context import ValidationContext


class QuestValidator(Validator):
    @property
    def name(self) -> str:
        return "Quests"

    def validate(self) -> ValidationResult:
        if not self.path.exists():
            return ValidationResult(
                errors=[f"Quests file not found: {self.path}"],
                item_count=0,
                metadata={},
            )

        import json
        data = json.loads(self.path.read_text())
        errors = []
        for quest_id, quest in data.items():
            if "title" not in quest:
                errors.append(f"Quest '{quest_id}': missing required 'title'")
            # Populate context for cross-referencing
            # e.g. self.context.add_map_entity(...)

        return ValidationResult(
            errors=errors,
            item_count=len(data),
            metadata={"Reward items": sum(len(q.get("rewards", [])) for q in data.values())},
        )

    def validate_cross_references(self) -> ValidationResult:
        errors = []
        known_npcs = self.context.get_all_npcs()
        # ... check references against context
        return ValidationResult(errors=errors, item_count=0, metadata={})
```

To run your validator alongside the built-ins, call it in the same pattern as `ValidateCommand` in `src/pedre/commands/validate.py`:

```python
context = ValidationContext()
quest_validator = QuestValidator(Path("assets/data/content/quests.json"), context)

result = quest_validator.validate()
cross_result = quest_validator.validate_cross_references()
```

## See Also

- [CLI Guide](../guides/cli.md) — `pedre validate` command and `--*-path` flags
- [Custom Commands](../extending/custom-commands.md) — adding commands that run validators
