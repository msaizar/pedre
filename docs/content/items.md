# Items

Item definitions describe inventory items — their display name, description, and optional metadata like images and category.

**File:** `assets/data/content/items.json`

## Fields

| Field         | Type   | Required | Description                                      |
| ------------- | ------ | -------- | ------------------------------------------------ |
| `name`        | string | **Yes**  | Display name shown in the inventory UI           |
| `description` | string | **Yes**  | Description shown when the item is inspected     |
| `image_path`  | string | No       | Path to the item image (relative to assets/)     |
| `icon_path`   | string | No       | Path to the inventory icon (relative to assets/) |
| `category`    | string | No       | Item category (e.g. `"weapon"`, `"key"`)         |
| `acquired`    | bool   | No       | Whether the item starts as acquired              |
| `consumable`  | bool   | No       | Whether the item is consumed on use              |

## Example

```json
{
  "iron_key": {
    "name": "Iron Key",
    "description": "A heavy iron key. It must open something important.",
    "icon_path": "images/items/iron_key_icon.png",
    "category": "key"
  },
  "health_potion": {
    "name": "Health Potion",
    "description": "Restores a small amount of health.",
    "image_path": "images/items/health_potion.png",
    "icon_path": "images/items/health_potion_icon.png",
    "category": "consumable",
    "consumable": true
  },
  "ancient_map": {
    "name": "Ancient Map",
    "description": "A worn map showing a hidden location.",
    "category": "quest"
  }
}
```

## See Also

- [Inventory Plugin](../plugins/inventory.md) — runtime inventory management
- [Custom Content Types](../extending/custom-content.md) — adding your own content types
