# AudioManager

Manages background music and sound effects with caching.

## Location

- Implementation: `src/pedre/systems/audio/manager.py`
- Base class: `src/pedre/systems/audio/base.py`

## Configuration

The AudioManager uses the following settings from `pedre.conf.settings`:

- `AUDIO_MUSIC_VOLUME` - Default music volume (0.0 to 1.0, default: 0.5)
- `AUDIO_MUSIC_ENABLED` - Whether music is enabled by default (default: True)
- `AUDIO_SFX_VOLUME` - Default sound effects volume (0.0 to 1.0, default: 0.7)
- `AUDIO_SFX_ENABLED` - Whether sound effects are enabled by default (default: True)

These can be overridden in your project's `settings.py`:

```python
# Custom audio settings
AUDIO_MUSIC_VOLUME = 0.8
AUDIO_SFX_VOLUME = 0.5
AUDIO_MUSIC_ENABLED = False  # Start with music muted
```

## Public API

### Music Playback

#### `play_music(filename: str, *, loop: bool = True, volume: float | None = None) -> bool`

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
audio_manager.play_music("village_theme.ogg")

# Play one-time victory music at high volume
audio_manager.play_music("victory.ogg", loop=False, volume=0.9)
```

**Notes:**

- Automatically stops any currently playing music
- Music files are cached for faster replay
- Non-looping music uses streaming to reduce memory usage

#### `stop_music() -> None`

Stop the currently playing music immediately.

**Example:**

```python
audio_manager.stop_music()
```

**Notes:**

- Music file remains cached and can be replayed without reloading
- Called automatically when starting new music

#### `pause_music() -> None`

Pause the currently playing music at its current position.

**Example:**

```python
# Pause when entering menu
audio_manager.pause_music()
```

**Notes:**

- Use `resume_music()` to continue from the same position
- Use `stop_music()` if you want to restart from the beginning

#### `resume_music() -> None`

Resume paused music from where it was paused.

**Example:**

```python
# Resume when exiting menu
audio_manager.resume_music()
```

**Notes:**

- Does nothing if music was not previously paused

### Sound Effects

#### `play_sfx(sound_name: str, *, volume: float | None = None) -> bool`

Play a sound effect from the `assets/audio/sfx/` directory.

**Parameters:**

- `sound_name` - Sound effect file name (e.g., `"door_open.wav"`, `"footstep.wav"`)
- `volume` - Optional volume override (0.0 to 1.0). If `None`, uses current `sfx_volume` setting

**Returns:**

- `True` if sound played successfully, `False` if SFX is disabled or an error occurred

**Example:**

```python
# Play NPC voice at default volume
audio_manager.play_sfx("martin.mp3")

# Play UI sound at lower volume
audio_manager.play_sfx("click.wav", volume=0.3)
```

**Notes:**

- Sound effects are cached after first use for instant replay
- Multiple sound effects can play simultaneously
- Missing sound files are logged but don't cause errors

### Volume Control

#### `set_music_volume(volume: float) -> None`

Set the music volume level.

**Parameters:**

- `volume` - Volume from 0.0 (silent) to 1.0 (full volume)

**Example:**

```python
audio_manager.set_music_volume(0.5)  # 50% volume
```

**Notes:**

- Volume is automatically clamped to 0.0-1.0 range
- If music is currently playing, the change takes effect immediately

#### `set_sfx_volume(volume: float) -> None`

Set the sound effects volume level.

**Parameters:**

- `volume` - Volume from 0.0 (silent) to 1.0 (full volume)

**Example:**

```python
audio_manager.set_sfx_volume(0.8)  # 80% volume
```

**Notes:**

- Volume is automatically clamped to 0.0-1.0 range
- Does not affect currently playing sounds, only future playback

### Enable/Disable

#### `toggle_music() -> bool`

Toggle music on/off.

**Returns:**

- New music enabled state (`True` = enabled, `False` = disabled)

**Example:**

```python
# Toggle music in response to user pressing 'M'
new_state = audio_manager.toggle_music()
print(f"Music is now {'on' if new_state else 'off'}")
```

**Notes:**

- When music is disabled, any currently playing music is stopped
- When re-enabled, music does not automatically resume

#### `toggle_sfx() -> bool`

Toggle sound effects on/off.

**Returns:**

- New SFX enabled state (`True` = enabled, `False` = disabled)

**Example:**

```python
# Toggle SFX in response to user pressing 'S'
new_state = audio_manager.toggle_sfx()
print(f"Sound effects are now {'on' if new_state else 'off'}")
```

**Notes:**

- When SFX is disabled, all future `play_sfx()` calls return `False` immediately
- Currently playing sound effects are not affected

### Cache Management

#### `clear_music_cache() -> None`

Clear the music cache to free memory.

**Example:**

```python
# Clear music cache before loading a new scene
audio_manager.clear_music_cache()
```

**Notes:**

- Music will be reloaded from disk on next use
- May cause a brief delay when starting music again

#### `clear_sfx_cache() -> None`

Clear the sound effects cache to free memory.

**Example:**

```python
# Clear SFX cache after completing a level
audio_manager.clear_sfx_cache()
```

**Notes:**

- Sound effects will be reloaded from disk on next use
- May cause a brief delay the first time each sound is played again

#### `clear_all_caches() -> None`

Clear both music and SFX caches simultaneously.

**Example:**

```python
# Full cache clear when returning to main menu
audio_manager.clear_all_caches()
```

### Advanced Methods

#### `mark_music_loading(filename: str) -> None`

Mark a music file as currently being loaded in the background.

**Parameters:**

- `filename` - Name of the music file being loaded

**Notes:**

- Used for background preloading coordination
- `play_music()` will wait briefly if a file is being preloaded

#### `unmark_music_loading(filename: str) -> None`

Unmark a music file as being loaded.

**Parameters:**

- `filename` - Name of the music file that finished loading

**Notes:**

- Should be called after `mark_music_loading()` once the file is loaded

#### `get_music_cache() -> dict[str, arcade.Sound]`

Get the music cache dictionary.

**Returns:**

- Dictionary mapping filename to `arcade.Sound` objects

#### `set_music_cache(cache_key: str, sound: arcade.Sound) -> None`

Set a music file in the cache.

**Parameters:**

- `cache_key` - Filename to use as cache key
- `sound` - The `arcade.Sound` object to cache

### Integration Methods

#### `load_from_tiled(tile_map: arcade.TileMap, arcade_scene: arcade.Scene) -> None`

Load and play background music from a Tiled map property.

**Parameters:**

- `tile_map` - Loaded TileMap with properties
- `arcade_scene` - Scene created from tile_map (unused)

**Notes:**

- Automatically called by the scene system when loading maps
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

## Custom Audio Implementation

If you need to replace the audio system with a custom implementation (e.g., for FMOD, Wwise, or a different audio backend), you can extend the `AudioBaseManager` abstract base class.

### AudioBaseManager

**Location:** `src/pedre/systems/audio/base.py`

The `AudioBaseManager` class defines the minimum interface that any audio manager must implement. All methods are abstract and must be implemented by your custom class.

#### Required Methods

Your custom audio manager must implement these abstract methods:

```python
from pedre.systems.audio.base import AudioBaseManager
import arcade

class CustomAudioManager(AudioBaseManager):
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

Register your custom audio manager using the `@SystemRegistry.register` decorator:

```python
from pedre.systems.registry import SystemRegistry
from pedre.systems.audio.base import AudioBaseManager

@SystemRegistry.register
class CustomAudioManager(AudioBaseManager):
    name = "audio"
    dependencies = []

    # ... implement all abstract methods ...
```

#### Notes on Custom Implementation

- Your custom manager inherits from `BaseSystem` (via `AudioBaseManager`), so you must implement the standard system lifecycle methods: `setup()`, `cleanup()`, and `reset()`
- The `role` attribute is set to `"audio_manager"` in the base class
- Your implementation can use any audio backend, not just Arcade's audio system
- The return types shown (e.g., `arcade.Sound`) are for compatibility with the default implementation; your custom version can use different types internally as long as the interface is maintained
- Register your custom audio manager in your project's `INSTALLED_SYSTEMS` setting before the default `"pedre.systems.audio"` to replace it

**Example Custom Implementation:**

```python
# In myproject/systems/custom_audio.py
from pedre.systems.registry import SystemRegistry
from pedre.systems.audio.base import AudioBaseManager

@SystemRegistry.register
class FMODAudioManager(AudioBaseManager):
    """Custom FMOD-based audio manager."""

    name = "audio"
    dependencies = []

    def __init__(self):
        # Initialize FMOD
        self.fmod_system = initialize_fmod()
        self.music_cache = {}
        # ... rest of initialization ...

    def play_music(self, filename: str, *, loop: bool = True, volume: float | None = None) -> bool:
        # Custom FMOD music playback logic
        sound = self.fmod_system.create_sound(filename)
        sound.play(loop=loop, volume=volume)
        return True

    # ... implement other abstract methods ...
```

```python
# In myproject/settings.py
INSTALLED_SYSTEMS = [
    "myproject.systems.custom_audio",  # Load custom audio first
    "pedre.systems.camera",
    "pedre.systems.debug",
    # ... rest of systems (omit "pedre.systems.audio") ...
]
```
