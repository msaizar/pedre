# Views

Game views represent different screens and game states in the Pedre framework.

## Location

[src/pedre/views/](https://github.com/msaizar/pedre/blob/main/src/pedre/views/)

## GameView

Primary gameplay view with player control, NPCs, and interactions.

### Constructor

```python
from pedre import GameView

game_view = GameView(view_manager, map_file="level1.tmx", scene_name="forest")
```

**Parameters:**

- `view_manager: ViewManager` - ViewManager instance
- `map_file: str` - Path to Tiled .tmx map file (optional)
- `scene_name: str` - Unique identifier for this scene (optional)

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
# Access via view manager
game_view = view_manager.game_view

# Access plugins through context
context = game_view.context
npc_plugin = context.get_plugin("npc")
dialog_plugin = context.get_plugin("dialog")
```

## MenuView

Main menu with navigation and asset preloading.

### Constructor

```python
from pedre import MenuView

menu_view = MenuView(view_manager)
```

**Parameters:**

- `view_manager: ViewManager` - ViewManager instance

### Configuration

Menu appearance is controlled through settings:

- `MENU_TITLE` - Menu title text
- `MENU_TITLE_SIZE` - Font size for title
- `MENU_OPTION_SIZE` - Font size for options
- `MENU_SPACING` - Vertical spacing between options
- `MENU_BACKGROUND_IMAGE` - Path to background image
- `MENU_MUSIC_FILES` - Music files to preload

See [Configuration Guide](../guides/configuration.md#menu-settings) for details.

### Example

```python
menu_view = view_manager.menu_view
view_manager.show_menu()
```

## LoadGameView

Load game screen for selecting save slots.

### Constructor

```python
from pedre.views import LoadGameView

load_view = LoadGameView(view_manager)
```

**Parameters:**

- `view_manager: ViewManager` - ViewManager instance

### Example

```python
load_view = view_manager.load_game_view
view_manager.show_load_game()
```

## SaveGameView

Save game screen for selecting save slots.

### Constructor

```python
from pedre.views import SaveGameView

save_view = SaveGameView(view_manager)
```

**Parameters:**

- `view_manager: ViewManager` - ViewManager instance

### Example

```python
save_view = view_manager.save_game_view
view_manager.show_save_game()
```

## See Also

- [ViewManager](view-manager.md) - View controller and transitions
- [GameContext](game-context.md) - Shared state container
- [Plugins Reference](../plugins/index.md) - Individual plugin documentation
