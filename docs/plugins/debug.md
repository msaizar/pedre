# DebugPlugin

Displays development information overlays showing player and NPC positions in tile and pixel coordinates.

## Location

- Implementation: [src/pedre/plugins/debug/plugin.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/debug/plugin.py)

## Configuration

The DebugPlugin uses the following settings from `pedre.conf.settings`:

### Display Settings

- `TILE_SIZE` - Size of tiles in pixels (default: 32)

## Public API

### Debug Mode Control

#### on_key_press

`on_key_press(symbol: int, modifiers: int) -> bool`

Toggle debug mode on/off with Shift+D.

**Parameters:**

- `symbol` - Arcade key constant
- `modifiers` - Modifier key bitfield

**Returns:**

- `True` if input was consumed

**Example:**

```python
def on_key_press(self, symbol, modifiers):
    # This is called automatically by PluginLoader
    self.debug_plugin.on_key_press(symbol, modifiers)
```

**Notes:**

- Called automatically by PluginLoader
- Toggles debug overlay when Shift+D is pressed
- Clears text objects when toggling off
- Logs state change to logger

### Debug Display

#### on_draw_ui

`on_draw_ui() -> None`

Render debug information overlay in screen coordinates.

**Example:**

```python
def on_draw(self):
    # Draw game
    self.scene.draw()

    # Draw UI (debug overlay is drawn here)
    self.debug_plugin.on_draw_ui()
```

**Notes:**

- Called automatically by PluginLoader
- Only renders when debug_mode is True
- Shows player position in tile and pixel coordinates
- Shows visible NPC positions in tile and pixel coordinates
- Shows NPC dialog levels
- Uses green text for player info
- Uses yellow text for NPC info

### Plugin Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the debug plugin with game context.

**Parameters:**

- `context` - Game context providing access to other plugins

**Notes:**

- Called automatically by PluginLoader
- Stores reference to game context
- Initializes empty text object list

#### cleanup

`cleanup() -> None`

Clean up debug resources when the scene unloads.

**Notes:**

- Clears all text objects
- Resets debug mode to False
- Called automatically by PluginLoader

## Debug Information Display

When debug mode is enabled with Shift+D, the overlay shows:

### Player Information

```text
Player: coords (320, 480)
```

**Fields:**

- Pixel coordinates (x, y) from sprite center position

### NPC Information

For each visible NPC:

```text
merchant: coords (384, 480) level 2
```

**Fields:**

- NPC name, pixel coordinates, and current dialog level

**Notes:**

- Only visible NPCs are shown
- NPCs with sprite.visible = False are excluded
- Dialog level indicates conversation progression

## Usage Examples

### Toggling Debug Mode

```python
# Debug mode is toggled with Shift+D
# Press Shift+D to enable the debug overlay
# Press Shift+D again to disable it
```

### Reading Debug Information

When debug mode is on:

1. **Player Position**: Check where the player is in both tile and pixel coordinates
2. **NPC Positions**: See all visible NPCs and their locations
3. **Dialog Levels**: Track which conversation stage each NPC is at

### Development Workflow

```python
# Enable debug mode (Shift+D)
# Move player around
# Observe tile coordinates to understand map layout
# Check NPC positions for pathfinding debugging
# Verify dialog levels after interactions
# Disable debug mode (Shift+D) when done
```

## Implementation Details

### Text Rendering

The debug overlay uses `arcade.Text` objects for efficient rendering:

- Text objects are reused between frames
- Object pool grows and shrinks based on number of debug lines
- Text is updated in-place when possible
- Extra objects are removed when not needed

### Coordinate Conversion

Tile coordinates are calculated from pixel coordinates:

```python
tile_x = int(pixel_x / TILE_SIZE)
tile_y = int(pixel_y / TILE_SIZE)
```

### Performance Considerations

- Debug overlay only renders when enabled
- Text objects are cached and reused
- NPC iteration skips invisible sprites
- Minimal overhead when debug mode is off

## Plugin Dependencies

The DebugPlugin depends on:

- `npc` - To access NPC plugin for NPC position data

The plugin also accesses:

- `player_plugin` - Via game context for player position
- `settings.TILE_SIZE` - For coordinate conversion

## See Also

- [NPCPlugin](npc.md) - NPC plugin providing position data
- [PlayerPlugin](player.md) - Player plugin providing player position
- [Configuration Guide](../guides/configuration.md)
