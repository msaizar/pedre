# Views

The GameView is the primary gameplay screen in the Pedre framework. Unlike traditional multi-view architectures, Pedre uses only one view with plugin overlays for different UI states (like pause menus).

## Location

[src/pedre/views/](https://github.com/msaizar/pedre/blob/main/src/pedre/views/)

## GameView

Primary gameplay view with player control, NPCs, and interactions.

### Constructor

```python
from pedre.views.game_view import GameView

game_view = GameView(game)
```

**Parameters:**

- `game: Game` - Game coordinator instance

**Note:** The GameView is typically created and managed by the Game coordinator. You rarely need to instantiate it directly.

### Key Plugins

The GameView provides access to all game plugins through its context:

- `npc_plugin: NPCPlugin` - NPC state and interactions
- `dialog_plugin: DialogPlugin` - Dialog display
- `inventory_plugin: InventoryPlugin` - Item management
- `script_plugin: ScriptPlugin` - Event-driven scripts
- `audio_plugin: AudioPlugin` - Sound and music
- `save_plugin: SavePlugin` - Game persistence
- `camera_plugin: CameraPlugin` - Camera control
- `portal_plugin: PortalPlugin` - Map transitions
- `interaction_plugin: InteractionPlugin` - Object interactions
- `particle_plugin: ParticlePlugin` - Visual effects

### Example

```python
# Access via game coordinator
game_view = game.game_view

# Access plugins through context
context = game.game_context
npc_plugin = context.get_plugin("npc")
dialog_plugin = context.get_plugin("dialog")
```

## Architecture Notes

- **Single View Design**: Pedre uses only the GameView. There are no separate MenuView, LoadGameView, or SaveGameView classes.
- **Plugin Overlays**: UI states like pause menus are implemented as plugin overlays on top of the GameView, not as separate views.
- **Managed Lifecycle**: The Game coordinator manages the GameView lifecycle, creating and destroying it as needed for new games or loaded games.

## See Also

- [Game](game.md) - Game coordinator and lifecycle management
- [GameContext](game-context.md) - Shared state container
- [Plugins Reference](../plugins/index.md) - Individual plugin documentation
