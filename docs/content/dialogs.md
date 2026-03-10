# Dialogs

Dialog definitions contain the text spoken by NPCs, organised per scene. They are validated against the NPC registry at startup — every dialog entry must reference a known NPC.

**Directory:** `assets/data/content/dialogs/` (one file per scene)

## File Layout

Each scene gets its own JSON file named `{scene}.json`:

```text
assets/
  data/
    content/
      dialogs/
        village.json
        forest.json
```

## Keys

Each file is a flat object whose keys follow the pattern `"{npc_name}/{level}"`:

```json
{
  "merchant/0": { "text": ["Hello, traveller!"], "name": "Old Merchant" },
  "merchant/1": { "text": ["Come back when you have coin."] },
  "guard/0":    { "text": ["Move along."] }
}
```

Entries are stored internally as `"{scene}/{npc_name}/{level}"`, where `scene` is the filename stem.

## Fields

| Field               | Type            | Required | Description                                            |
| ------------------- | --------------- | -------- | ------------------------------------------------------ |
| `text`              | list of strings | **Yes**  | Lines of dialogue spoken by the NPC                    |
| `name`              | string          | No       | Display name shown in the dialog UI (overrides default)|
| `conditions`        | list of objects | No       | Conditions that must pass for this dialog to trigger   |
| `on_condition_fail` | list of objects | No       | Actions to run when conditions are not met             |

## Example

```json
{
  "merchant/0": {
    "text": ["Welcome to my shop!", "I have the finest wares."],
    "name": "Old Merchant"
  },
  "merchant/1": {
    "text": ["Check your inventory first!"],
    "conditions": [
      {"name": "inventory_accessed", "equals": true}
    ],
    "on_condition_fail": [
      {"name": "dialog", "speaker": "Merchant", "text": ["You haven't checked your bag yet."]}
    ]
  },
  "guard/0": {
    "text": ["Move along, citizen."]
  }
}
```

## Accessing Dialogs at Runtime

Retrieve dialog text through `context.content_registry` in plugins and actions:

```python
dialogs = context.content_registry.get_sub_registry("dialogs")
definition = dialogs.get_dialog(scene="village", npc_name="merchant", level=0)
if definition:
    text_lines = definition["text"]
```

`get_dialog()` returns `None` when no entry exists for the given scene/NPC/level combination.

## Cross-Reference Validation

At startup, every dialog entry is checked against the NPC registry. If `npc_name` does not match a key in `npcs.json`, an `InvalidDefinitionError` is raised. Ensure all NPCs referenced in dialog files are defined in `npcs.json`.

## See Also

- [NPCs](npcs.md) — NPC definitions referenced by dialog entries
- [Custom Content Types](../extending/custom-content.md) — implementing a custom dialog registry
