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

### Key Managers

The GameView provides access to all game systems through its context:

- `npc_manager: NPCManager` - NPC state and interactions
- `dialog_manager: DialogManager` - Dialog display
- `inventory_manager: InventoryManager` - Item management
- `script_manager: ScriptManager` - Event-driven scripts
- `audio_manager: AudioManager` - Sound and music
- `save_manager: SaveManager` - Game persistence
- `camera_manager: CameraManager` - Camera control
- `portal_manager: PortalManager` - Map transitions
- `interaction_manager: InteractionManager` - Object interactions
- `particle_manager: ParticleManager` - Visual effects

### Example

```python
# Access via view manager
game_view = view_manager.game_view

# Access systems through context
context = game_view.context
npc_manager = context.get_system("npc")
dialog_manager = context.get_system("dialog")
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
- [Systems Reference](../systems/index.md) - Individual system documentation
