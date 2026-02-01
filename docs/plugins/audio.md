# AudioPlugin

Manages background music and sound effects with caching.

## Location

- Implementation: [src/pedre/plugins/audio/plugin.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/audio/plugin.py)
- Base class: [src/pedre/plugins/audio/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/audio/base.py)
- Actions: [src/pedre/plugins/audio/actions.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/audio/actions.py)

## Configuration

The AudioPlugin uses the following settings from `pedre.conf.settings`:

### Volume and Playback Settings

- `AUDIO_MUSIC_VOLUME` - Default music volume (0.0 to 1.0, default: `0.5`)
- `AUDIO_MUSIC_ENABLED` - Whether music is enabled by default (default: `True`)
- `AUDIO_SFX_VOLUME` - Default sound effects volume (0.0 to 1.0, default: `0.7`)
- `AUDIO_SFX_ENABLED` - Whether sound effects are enabled by default (default: `True`)

These can be overridden in your project's `settings.py`:

```python
# Custom audio settings
AUDIO_MUSIC_VOLUME = 0.8
AUDIO_SFX_VOLUME = 0.5
AUDIO_MUSIC_ENABLED = False  # Start with music muted
```

## Public API

### Music Playback

#### play_music

`play_music(filename: str, *, loop: bool = True, volume: float | None = None) -> bool`

Play background music from the `assets/audio/music/` directory.

**Parameters:**

- `filename` - Music file name (e.g., `"background.ogg"`, `"beach.ogg"`)
- `loop` - Whether to loop the music continuously (default: `True`)
- `volume` - Optional volume override (0.0 to 1.0). If `None`, uses current `music_volume` setting

**Returns:**

- `True` if music started successfully, `False` if music is disabled or an error occurred

**Example:**

```python
# Play looping background music at default volume
audio_plugin.play_music("village_theme.ogg")

# Play one-time victory music at high volume
audio_plugin.play_music("victory.ogg", loop=False, volume=0.9)
```

**Notes:**

- Automatically stops any currently playing music
- Music files are cached for faster replay
- Non-looping music uses streaming to reduce memory usage
- If a file is being preloaded in background, waits briefly for preload to complete

#### stop_music

`stop_music() -> None`

Stop the currently playing music immediately.

**Example:**

```python
audio_plugin.stop_music()
```

**Notes:**

- Music file remains cached and can be replayed without reloading
- Called automatically when starting new music

#### pause_music

`pause_music() -> None`

Pause the currently playing music at its current position.

**Example:**

```python
# Pause when entering menu
audio_plugin.pause_music()
```

**Notes:**

- Use `resume_music()` to continue from the same position
- Use `stop_music()` if you want to restart from the beginning

#### resume_music

`resume_music() -> None`

Resume paused music from where it was paused.

**Example:**

```python
# Resume when exiting menu
audio_plugin.resume_music()
```

**Notes:**

- Does nothing if music was not previously paused

### Sound Effects

#### play_sfx

`play_sfx(sound_name: str, *, volume: float | None = None) -> bool`

Play a sound effect from the `assets/audio/sfx/` directory.

**Parameters:**

- `sound_name` - Sound effect file name (e.g., `"door_open.wav"`, `"footstep.wav"`)
- `volume` - Optional volume override (0.0 to 1.0). If `None`, uses current `sfx_volume` setting

**Returns:**

- `True` if sound played successfully, `False` if SFX is disabled or an error occurred

**Example:**

```python
# Play NPC voice at default volume
audio_plugin.play_sfx("martin.mp3")

# Play UI sound at lower volume
audio_plugin.play_sfx("click.wav", volume=0.3)
```

**Notes:**

- Sound effects are cached after first use for instant replay
- Multiple sound effects can play simultaneously
- Missing sound files are logged but don't cause errors

### Volume Control

#### set_music_volume

`set_music_volume(volume: float) -> None`

Set the music volume level.

**Parameters:**

- `volume` - Volume from 0.0 (silent) to 1.0 (full volume)

**Example:**

```python
audio_plugin.set_music_volume(0.5)  # 50% volume
```

**Notes:**

- Volume is automatically clamped to 0.0-1.0 range
- If music is currently playing, the change takes effect immediately

#### set_sfx_volume

`set_sfx_volume(volume: float) -> None`

Set the sound effects volume level.

**Parameters:**

- `volume` - Volume from 0.0 (silent) to 1.0 (full volume)

**Example:**

```python
audio_plugin.set_sfx_volume(0.8)  # 80% volume
```

**Notes:**

- Volume is automatically clamped to 0.0-1.0 range
- Does not affect currently playing sounds, only future playback

### Enable/Disable

#### toggle_music

`toggle_music() -> bool`

Toggle music on/off.

**Returns:**

- New music enabled state (`True` = enabled, `False` = disabled)

**Example:**

```python
# Toggle music in response to user pressing 'M'
new_state = audio_plugin.toggle_music()
print(f"Music is now {'on' if new_state else 'off'}")
```

**Notes:**

- When music is disabled, any currently playing music is stopped
- When re-enabled, music does not automatically resume

#### toggle_sfx

`toggle_sfx() -> bool`

Toggle sound effects on/off.

**Returns:**

- New SFX enabled state (`True` = enabled, `False` = disabled)

**Example:**

```python
# Toggle SFX in response to user pressing 'S'
new_state = audio_plugin.toggle_sfx()
print(f"Sound effects are now {'on' if new_state else 'off'}")
```

**Notes:**

- When SFX is disabled, all future `play_sfx()` calls return `False` immediately
- Currently playing sound effects are not affected

### Cache Management

#### clear_music_cache

`clear_music_cache() -> None`

Clear the music cache to free memory.

**Example:**

```python
# Clear music cache before loading a new scene
audio_plugin.clear_music_cache()
```

**Notes:**

- Music will be reloaded from disk on next use
- May cause a brief delay when starting music again

#### clear_sfx_cache

`clear_sfx_cache() -> None`

Clear the sound effects cache to free memory.

**Example:**

```python
# Clear SFX cache after completing a level
audio_plugin.clear_sfx_cache()
```

**Notes:**

- Sound effects will be reloaded from disk on next use
- May cause a brief delay the first time each sound is played again

#### clear_all_caches

`clear_all_caches() -> None`

Clear both music and SFX caches simultaneously.

**Example:**

```python
# Full cache clear when returning to main menu
audio_plugin.clear_all_caches()
```

### Advanced Methods

#### mark_music_loading

`mark_music_loading(filename: str) -> None`

Mark a music file as currently being loaded in the background.

**Parameters:**

- `filename` - Name of the music file being loaded

**Notes:**

- Used for background preloading coordination
- `play_music()` will wait briefly if a file is being preloaded

#### unmark_music_loading

`unmark_music_loading(filename: str) -> None`

Unmark a music file as being loaded.

**Parameters:**

- `filename` - Name of the music file that finished loading

**Notes:**

- Should be called after `mark_music_loading()` once the file is loaded

#### get_music_cache

`get_music_cache() -> dict[str, arcade.Sound]`

Get the music cache dictionary.

**Returns:**

- Dictionary mapping filename to `arcade.Sound` objects

#### set_music_cache

`set_music_cache(cache_key: str, sound: arcade.Sound) -> None`

Set a music file in the cache.

**Parameters:**

- `cache_key` - Filename to use as cache key
- `sound` - The `arcade.Sound` object to cache

### Save/Load Support

#### get_save_state

`get_save_state() -> dict[str, Any]`

Return serializable state for saving.

**Returns:**

- Dictionary containing audio settings (volume levels and enabled states)

**Example:**

```python
save_data = {
    "audio": audio_plugin.get_save_state(),
    # ... other save data
}
```

**Notes:**

- Saves music volume, SFX volume, music enabled, and SFX enabled states
- Delegates to `to_dict()`

#### restore_save_state

`restore_save_state(state: dict[str, Any]) -> None`

Restore state from save data.

**Parameters:**

- `state` - Previously saved state dictionary

**Example:**

```python
audio_plugin.restore_save_state(save_data["audio"])
```

**Notes:**

- Restores volume levels and enabled states
- Does not affect currently playing audio or cached files
- Delegates to `from_dict()`

#### to_dict

`to_dict() -> dict[str, bool | float]`

Convert audio settings to dictionary for serialization.

**Returns:**

- Dictionary with keys: `music_volume`, `sfx_volume`, `music_enabled`, `sfx_enabled`

**Example:**

```python
save_data = {
    "audio": audio_plugin.to_dict(),
    # ... other save data
}
```

#### from_dict

`from_dict(data: dict[str, bool | float]) -> None`

Load audio settings from a saved dictionary.

**Parameters:**

- `data` - Dictionary with audio settings

**Example:**

```python
audio_plugin.from_dict(save_data["audio"])
```

**Notes:**

- Missing keys are ignored (current values are retained)
- Volume values are clamped to 0.0-1.0 range

### Plugin Lifecycle

#### setup

`setup(context: GameContext) -> None`

Initialize the audio plugin with game context.

**Parameters:**

- `context` - Game context providing access to other plugins

**Notes:**

- Called automatically by PluginLoader
- Stores reference to game context

#### cleanup

`cleanup() -> None`

Clean up audio resources when the scene unloads.

**Notes:**

- Stops any playing music
- Clears all caches
- Called automatically by PluginLoader

#### reset

`reset() -> None`

Reset audio plugin for new game.

**Notes:**

- Stops currently playing music
- Keeps caches intact for performance

### Integration Methods

#### load_from_tiled

`load_from_tiled(tile_map: arcade.TileMap, arcade_scene: arcade.Scene) -> None`

Load and play background music from a Tiled map property.

**Parameters:**

- `tile_map` - Loaded TileMap with properties
- `arcade_scene` - Scene created from tile_map (unused)

**Notes:**

- Automatically called by the scene plugin when loading maps
- Looks for a `music` property on the map
- Music will loop continuously

**Tiled Configuration:**

1. Click on the map name in Layers panel (deselect any layers)
2. Open Properties panel (View → Properties)
3. Add `music` property (string type)
4. Set value to filename relative to `assets/audio/music/`

**Example:**

```yaml
music: "peaceful_village.ogg"
```

## Supported Formats

- **Music**: `.mp3`, `.ogg`, `.wav`
- **SFX**: `.wav`, `.ogg`, `.mp3`

## Actions

### PlayMusicAction

Play background music.

**Type:** `play_music`

**Parameters:**

- `file: str` - Music file name (in `assets/audio/music/`)
- `loop: bool` - Whether to loop the music (default: `true`)
- `volume: float` - Optional volume override (0.0 to 1.0)

**Example:**

```json
{
    "type": "play_music",
    "file": "town_theme.ogg"
}
```

```json
{
    "type": "play_music",
    "file": "victory_fanfare.ogg",
    "loop": false,
    "volume": 0.8
}
```

**Notes:**

- Stops any currently playing music before starting the new track
- Action completes immediately after starting playback

### PlaySFXAction

Play a sound effect.

**Type:** `play_sfx`

**Parameters:**

- `file: str` - Sound effect file name (in `assets/audio/sfx/`)

**Example:**

```json
{
    "type": "play_sfx",
    "file": "door_open.wav"
}
```

**Notes:**

- Action completes immediately after playing the sound
- Multiple sound effects can play simultaneously

## Custom Audio Implementation

If you need to replace the audio plugin with a custom implementation (e.g., for FMOD, Wwise, or a different audio backend), you can extend the `AudioBasePlugin` abstract base class.

### AudioBasePlugin

**Location:** [src/pedre/plugins/audio/base.py](https://github.com/msaizar/pedre/blob/main/src/pedre/plugins/audio/base.py)

The `AudioBasePlugin` class defines the minimum interface that any audio plugin must implement. All methods are abstract and must be implemented by your custom class.

#### Required Methods

Your custom audio plugin must implement these abstract methods:

```python
from pedre.plugins.audio.base import AudioBasePlugin
import arcade

class CustomAudioPlugin(AudioBasePlugin):
    """Custom audio implementation."""

    name = "audio"
    dependencies = []

    def get_music_cache(self) -> dict[str, arcade.Sound]:
        """Get music cache."""
        ...

    def set_music_cache(self, cache_key: str, sound: arcade.Sound) -> None:
        """Set music cache."""
        ...

    def play_sfx(self, sound_name: str, *, volume: float | None = None) -> bool:
        """Play a sound effect."""
        ...

    def mark_music_loading(self, filename: str) -> None:
        """Mark a music file as currently being loaded."""
        ...

    def unmark_music_loading(self, filename: str) -> None:
        """Unmark a music file as being loaded."""
        ...

    def play_music(self, filename: str, *, loop: bool = True, volume: float | None = None) -> bool:
        """Play background music."""
        ...
```

#### Registration

Register your custom audio plugin using the `@PluginRegistry.register` decorator:

```python
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.audio.base import AudioBasePlugin

@PluginRegistry.register
class CustomAudioPlugin(AudioBasePlugin):
    name = "audio"
    dependencies = []

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom plugin inherits from `BasePlugin` (via `AudioBasePlugin`), so you must implement the standard plugin lifecycle methods: `setup()`, `cleanup()`, and `reset()`
- The `role` attribute is set to `"audio_plugin"` in the base class
- Your implementation can use any audio backend, not just Arcade's audio system
- The return types shown (e.g., `arcade.Sound`) are for compatibility with the default implementation; your custom version can use different types internally as long as the interface is maintained
- Register your custom audio plugin in your project's `INSTALLED_PLUGINS` setting before the default `"pedre.plugins.audio"` to replace it

**Example Custom Implementation:**

```python
# In myproject/plugins/custom_audio.py
from pedre.plugins.registry import PluginRegistry
from pedre.plugins.audio.base import AudioBasePlugin

@PluginRegistry.register
class FMODAudioPlugin(AudioBasePlugin):
    """Custom FMOD-based audio plugin."""

    name = "audio"
    dependencies = []

    def __init__(self):
        # Initialize FMOD
        self.fmod_plugin = initialize_fmod()
        self.music_cache = {}
        # ... rest of initialization ...

    def play_music(self, filename: str, *, loop: bool = True, volume: float | None = None) -> bool:
        # Custom FMOD music playback logic
        sound = self.fmod_plugin.create_sound(filename)
        sound.play(loop=loop, volume=volume)
        return True

    # ... implement other abstract methods ...
```

```python
# In myproject/settings.py
INSTALLED_PLUGINS = [
    "myproject.plugins.custom_audio",  # Load custom audio first
    "pedre.plugins.camera",
    "pedre.plugins.debug",
    # ... rest of plugins (omit "pedre.plugins.audio") ...
]
```

## Usage Examples

### Background Music for Scenes

```python
# Play looping background music
audio_plugin.play_music("village_theme.ogg")

# Switch to battle music
audio_plugin.play_music("battle.ogg")
```

### Sound Effects on Interaction

```python
# Play NPC voice when interacting
audio_plugin.play_sfx("martin.mp3")

# Play UI feedback
audio_plugin.play_sfx("click.wav", volume=0.3)
```

### Scripted Audio Sequence

```json
{
    "dramatic_entrance": {
        "scene": "castle",
        "trigger": {
            "event": "portal_entered",
            "portal": "throne_room"
        },
        "actions": [
            {"type": "play_music", "file": "throne_room.ogg"},
            {"type": "play_sfx", "file": "door_open.wav"},
            {"type": "dialog", "speaker": "King", "text": ["Welcome to my court!"]},
            {"type": "wait_for_dialog_close"}
        ]
    }
}
```

### Pausing Audio During Menus

```python
# When opening pause menu
audio_plugin.pause_music()

# When closing pause menu
audio_plugin.resume_music()
```

### Saving and Restoring Audio Settings

```python
# Save
save_data = {"audio": audio_plugin.get_save_state()}

# Restore
audio_plugin.restore_save_state(save_data["audio"])
```

## See Also

- [DialogPlugin](dialog.md) - Conversation plugin
- [ScriptPlugin](script.md) - Event-driven scripting
- [SavePlugin](save.md) - Save/load plugin
- [Configuration Guide](../guides/configuration.md)
- [Scripting Actions](../scripting/actions.md)
